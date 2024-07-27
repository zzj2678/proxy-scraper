import logging
import re
from typing import List

import aiohttp

from proxy_scraper.config import CONFIG
from proxy_scraper.extractors.base import ProxyScraperBase
from proxy_scraper.proxy import Proxy

logger = logging.getLogger(__name__)

PROXY_DIR = CONFIG["proxy_dir"]


class TxtScraper(ProxyScraperBase):
    def __init__(self):
        super().__init__()

    def get_urls(self):
        return [
            "https://api.openproxylist.xyz/http.txt",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://www.proxy-list.download/api/v1/get?type=https",
            "https://multiproxy.org/txt_all/proxy.txt",
            "https://multiproxy.org/txt_anon/proxy.txt",
            "https://proxyspace.pro/http.txt",
            "https://proxyspace.pro/https.txt",
            "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt",
            "https://github.com/Anonym0usWork1221/Free-Proxies/raw/main/proxy_files/http_proxies.txt",
            "https://github.com/Anonym0usWork1221/Free-Proxies/raw/main/proxy_files/https_proxies.txt",
            "https://github.com/officialputuid/KangProxy/raw/KangProxy/http/http.txt",
            "https://github.com/officialputuid/KangProxy/raw/KangProxy/https/https.txt",
            "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt"
        ]

    async def scrape(self):
        for url in self.get_urls():
            logger.info(f"Scraping proxies from {url}...")
            content = await self.fetch_content(url)
            proxies = self.extract_proxies(content)
            valid_proxies = await self.validator.validate_proxies(proxies)
            self.writer.save_raw_proxies(valid_proxies)

    async def fetch_content(self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()

    def extract_proxies(self, content: str) -> List[Proxy]:
        proxies = []
        if content:
            lines = content.strip().split("\n")
            for line in lines:
                ip_port = line.strip()
                if re.match(r'^(\d{1,3}\.){3}\d{1,3}:\d+$', ip_port):
                  ip, port = ip_port.split(":")
                  proxies.append(Proxy(ip, port, "http", ""))
        return proxies
