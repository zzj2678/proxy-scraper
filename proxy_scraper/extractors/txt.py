import logging
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
                ip, port = ip_port.split(":")
                proxies.append(Proxy(ip, port, "http", ""))
        return proxies
