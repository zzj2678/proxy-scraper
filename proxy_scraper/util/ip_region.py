import logging
import os

import requests

from proxy_scraper.util.xdbSearcher import XdbSearcher

logger = logging.getLogger(__name__)

class IPRegion:
    _instance = None
    DB_URL = "https://mirror.ghproxy.com/https://raw.githubusercontent.com/lionsoul2014/ip2region/master/data/ip2region.xdb"
    DB_PATH = "ip2region.xdb"
    API_URL = "http://ip-api.com/json/{}?lang=zh-CN"

    def __new__(cls, db_path=DB_PATH):
        if not cls._instance:
            cls._instance = super(IPRegion, cls).__new__(cls)
            cls._instance.db_path = db_path
            if not os.path.exists(cls._instance.db_path):
                cls._instance._download_db(cls._instance.db_path)
            cls._instance._init_searcher()
        return cls._instance

    def _init_searcher(self):
        try:
            self.searcher = XdbSearcher(self.db_path)
        except Exception as e:
            logging.error(f"Failed to initialize XdbSearcher: {e}")
            raise RuntimeError(f"Failed to initialize XdbSearcher: {e}")

    def _download_db(self, path):
        try:
            response = requests.get(self.DB_URL, stream=True)
            response.raise_for_status()
            with open(path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logging.info(f"Downloaded ip2region.xdb to {path}")
        except Exception as e:
            logging.error(f"Failed to download ip2region.xdb: {e}")
            raise RuntimeError(f"Failed to download ip2region.xdb: {e}")

    def get_region(self, ip: str) -> dict:
        try:
            # First try to get region data from the local database
            region_data = self.searcher.search(ip)
            if region_data:
                region_list = region_data.split("|")
                return {
                    "ip": ip,
                    "country": region_list[0],
                    "region": region_list[1],
                    "province": region_list[2],
                    "city": region_list[3],
                    "isp": region_list[4],
                }

            # If local database does not provide data, fall back to the API
            return self._fetch_from_api(ip)
        except Exception as e:
            logging.error(f"Error fetching region data for IP {ip}: {e}")
            raise RuntimeError(f"Error fetching region data for IP {ip}: {e}")

    def _fetch_from_api(self, ip: str) -> dict:
        try:
            response = requests.get(self.API_URL.format(ip))
            response.raise_for_status()
            data = response.json()
            return {
                "ip": ip,
                "country": data.get("country", ""),
                "region": data.get("regionName", ""),
                "province": data.get("regionName", ""),  # Adjust if needed
                "city": data.get("city", ""),
                "isp": data.get("isp", ""),
            }
        except Exception as e:
            logging.error(f"Failed to fetch data from API for IP {ip}: {e}")
            return {"ip": ip, "country": "", "region": "", "province": "", "city": "", "isp": ""}

    def __del__(self):
        if hasattr(self, 'searcher'):
            self.searcher.close()

if __name__ == '__main__':
    ip = '183.242.69.118'
    ip_region = IPRegion()
    print(ip_region.get_region(ip))
