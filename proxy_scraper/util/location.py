import logging
import os
import time
from functools import lru_cache

import requests

from proxy_scraper.util.xdbSearcher import XdbSearcher

logger = logging.getLogger(__name__)

class IPInfo:
    _instance = None
    DB_URL = (
        "https://mirror.ghproxy.com/https://raw.githubusercontent.com/lionsoul2014/ip2region/master/data/ip2region.xdb"
    )
    DB_PATH = "ip2region.xdb"
    API_URL = "http://ip-api.com/json/{}?lang=zh-CN"

    RETRY_WAIT_TIME = 45  # Wait time in seconds if rate-limited

    def __new__(cls, db_path=DB_PATH):
        if not cls._instance:
            cls._instance = super(IPInfo, cls).__new__(cls)
            cls._instance.db_path = db_path
            if not os.path.exists(cls._instance.db_path):
                logger.info(f"Database file {cls._instance.db_path} not found, downloading...")
                cls._instance._download_db(cls._instance.db_path)
            cls._instance._init_searcher()
        return cls._instance

    def _init_searcher(self):
        try:
            cb = XdbSearcher.loadContentFromFile(dbfile=self.db_path)
            self.searcher = XdbSearcher(contentBuff=cb)
            logger.info(f"Initialized XdbSearcher with database path {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize XdbSearcher: {e}")
            raise RuntimeError(f"Failed to initialize XdbSearcher: {e}")

    def _download_db(self, path):
        try:
            response = requests.get(self.DB_URL, stream=True)
            response.raise_for_status()
            with open(path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logger.info(f"Downloaded ip2region.xdb to {path}")
        except Exception as e:
            logger.error(f"Failed to download ip2region.xdb: {e}")
            raise RuntimeError(f"Failed to download ip2region.xdb: {e}")

    @lru_cache(maxsize=1024)
    def get_region(self, ip: str) -> dict:
        try:
            logger.info(f"Fetching region data for IP: {ip}")
            region_data = self.searcher.search(ip)
            logger.debug(f"Local database search result for {ip}: {region_data}")

            if region_data:
                region_list = region_data.split("|")
                region_info = {
                    "ip": ip,
                    "country": region_list[0],
                    "region": region_list[1],
                    "province": region_list[2],
                    "city": region_list[3],
                    "isp": region_list[4],
                }
                logger.info(f"Region data for IP {ip} from local DB: {region_info}")
                return region_info

            # If local database does not provide data, fall back to the API
            return self._fetch_from_api(ip)
        except Exception as e:
            logger.error(f"Error fetching region data for IP {ip}: {e}")
            raise RuntimeError(f"Error fetching region data for IP {ip}: {e}")

    def _fetch_from_api(self, ip: str) -> dict:
        try:
            logger.info(f"Fetching region data for IP {ip} from API")
            response = requests.get(self.API_URL.format(ip))
            data = response.json()

            if data.get("status") == "fail":
              # Rate limited or other failure
              logger.warning(f"Request failed for IP {ip}. Status: {data.get('message')}. Retrying after {self.RETRY_WAIT_TIME} seconds.")
              time.sleep(self.RETRY_WAIT_TIME)
              response = requests.get(self.API_URL.format(ip))
              data = response.json()

            if data.get("status") == "fail":
              # If still failing, log the error and return a fallback structure
              logger.error(f"Repeated failure for IP {ip}. Status: {data.get('message')}.")
              return {"ip": ip, "country": "", "region": "", "province": "", "city": "", "isp": ""}

            region_info = {
                "ip": ip,
                "country": data.get("country", ""),
                "region": data.get("regionName", ""),
                "province": data.get("regionName", ""),  # Adjust if needed
                "city": data.get("city", ""),
                "isp": data.get("isp", ""),
            }
            logger.info(f"Region data for IP {ip} from API: {region_info}")
            return region_info
        except Exception as e:
            logger.error(f"Failed to fetch data from API for IP {ip}: {e}")
            return {"ip": ip, "country": "", "region": "", "province": "", "city": "", "isp": ""}

    def __del__(self):
        if hasattr(self, "searcher"):
            self.searcher.close()
            logger.info("Closed XdbSearcher instance")


location = IPInfo()

# if __name__ == "__main__":
#     ip = "176.99.2.43"
#     info = IPInfo()
    # region_info = info.get_region(ip)
    # print(f"Region info for IP {ip}: {region_info}")
    # print(info.get_region("160.86.242.23"))
