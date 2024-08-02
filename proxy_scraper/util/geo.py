import logging
import os
import random
import time
from functools import lru_cache
from typing import Optional

import geoip2.database
import pycountry
import requests

from proxy_scraper.util.geo_db import GeoDB

logger = logging.getLogger(__name__)

GEO_NAMES_USERNAMES = ['no13bus', 'no10bus']
DB_URL = "https://mirror.ghproxy.com/https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb"
DB_PATH = "GeoLite2-Country.mmdb"
API_URL = "http://ip-api.com/json/{}"
FALLBACK_API = "https://ipapi.co/{}/json"
RETRY_WAIT_TIME = 45

class GeoInfo:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.geonames_usernames = GEO_NAMES_USERNAMES
        self.reader = None
        self.db = GeoDB()
        self._init_reader()

    def _init_reader(self):
        if not os.path.exists(self.db_path):
            logger.info(f"Database file {self.db_path} not found, downloading...")
            self._download_db(self.db_path)
        try:
            self.reader = geoip2.database.Reader(self.db_path)
            logger.info(f"Initialized GeoLite2 Reader with database path {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize GeoLite2 Reader: {e}")
            raise RuntimeError(f"Failed to initialize GeoLite2 Reader: {e}")

    def _download_db(self, path):
        try:
            response = requests.get(DB_URL, stream=True)
            response.raise_for_status()
            with open(path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            logger.info(f"Downloaded GeoLite2-Country.mmdb to {path}")
        except Exception as e:
            logger.error(f"Failed to download GeoLite2-Country.mmdb: {e}")
            raise RuntimeError(f"Failed to download GeoLite2-Country.mmdb: {e}")

    @lru_cache(maxsize=128)
    def _translate_country_name(self, name: str) -> Optional[str]:
        username = random.choice(self.geonames_usernames)
        url = f"http://api.geonames.org/searchJSON?q={name}&maxRows=1&username={username}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if 'geonames' in data and data['geonames']:
                return data['geonames'][0].get('countryCode')
        except requests.RequestException as e:
            logger.error(f"Error translating country name '{name}' using GeoNames: {e}")
        return None

    @lru_cache(maxsize=128)
    def _get_country_code_from_pycountry(self, name: str) -> Optional[str]:
        try:
            country = pycountry.countries.lookup(name)
            return country.alpha_2
        except LookupError:
            return None

    def get_country_code(self, name: str) -> Optional[str]:
        if any('\u4e00' <= char <= '\u9fff' for char in name):
            country_code = self._translate_country_name(name)
        else:
            country_code = self._get_country_code_from_pycountry(name)

        if country_code:
            return country_code
        else:
            logger.warning(f"Could not normalize country name '{name}'.")
            return None

    def get_region(self, ip: str) -> dict:
        cached_data = self.db.get(ip)
        if cached_data:
            logger.info(f"Cache hit for IP: {ip}")
            return cached_data

        try:
            logger.info(f"Fetching region data for IP: {ip}")
            region_info = self._query_geoip2(ip)
            logger.info(f"Region data for IP {ip} from GeoLite2: {region_info}")
            self.db.set(ip, region_info)
            return region_info
        except Exception as e:
            logger.error(f"Error fetching region data for IP {ip}: {e}")
            return self._fetch_from_api(ip)

    def _query_geoip2(self, ip: str) -> dict:
        try:
            response = self.reader.country(ip)
            country = response.country.name
            country_code = response.country.iso_code
            return {
                "ip": ip,
                "country": country,
                "countryCode": country_code,
            }
        except Exception as e:
            logger.error(f"GeoLite2 query failed for IP {ip}: {e}")
            raise RuntimeError(f"GeoLite2 query failed for IP {ip}: {e}")

    def _fetch_from_api(self, ip: str) -> dict:
        try:
            region_info = self._request_api(ip, API_URL)
            if region_info.get("status") == "fail":
                logger.warning(f"Using fallback API for IP {ip}")
                region_info = self._request_api(ip, FALLBACK_API)

            if region_info.get("status") == "fail":
                raise Exception(region_info.get("message"))

            region_info = self._format_api_data(ip, region_info)
            self.ip_cache.set(ip, region_info)
            return region_info
        except Exception as e:
            logger.error(f"Failed to fetch data from API for IP {ip}: {e}")
            return {"ip": ip, "country": "", "countryCode": ""}

    def _request_api(self, ip: str, url: str) -> dict:
        response = requests.get(url.format(ip))
        data = response.json()

        if data.get("status") == "fail" and url == API_URL:
            logger.warning(
                f"Request failed for IP {ip}. Status: {data.get('message')}. Retrying after {RETRY_WAIT_TIME} seconds."
            )
            time.sleep(RETRY_WAIT_TIME)
            response = requests.get(url.format(ip))
            data = response.json()

        return data

    def _format_api_data(self, ip: str, data: dict) -> dict:
        country = data.get("country")
        country_code = data.get("countryCode", data.get("country_code"))
        return {
            "ip": ip,
            "country": country,
            "countryCode": country_code,
        }

geo_info = GeoInfo()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    geo_info = GeoInfo()
    ip = "176.99.2.43"
    print(geo_info.get_region(ip))
    # print(geo_info.get_country_code("Germany"))
