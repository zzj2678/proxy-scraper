import logging
from typing import List

from bs4 import BeautifulSoup

from proxy_scraper.extractors.base import ProxyScraperBase
from proxy_scraper.proxy import Proxy

logger = logging.getLogger(__name__)

class ZdayeScraper(ProxyScraperBase):
    def get_urls(self):
        return [
            "https://www.zdaye.com/free/?ip=&adr=&checktime=&sleep=&cunhuo=&dengji=&nadr=&https=1&yys=&post=%E6%94%AF%E6%8C%81&px="
        ]

    def extract_proxies(self, content: str) -> List[Proxy]:
        proxies = []
        if not content:
            return proxies

        logger.debug("Parsing content to extract proxies...")
        soup = BeautifulSoup(content, 'html.parser')
        rows = soup.select('table tbody tr')
        for row in rows:
            cols = row.select('td')
            if len(cols) >= 2:
                ip = cols[0].text.strip()
                port = cols[1].text.strip()
                is_https = cols[5].find('div', class_='iyes') is not None
                protocol = 'http'
                if is_https:
                    protocol = 'https'

                proxy = Proxy(ip, port, protocol, '')
                proxies.append(proxy)
                logger.debug(f"Extracted proxy: {proxy}")

        return proxies
