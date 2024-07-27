import logging
from typing import List

from bs4 import BeautifulSoup

from proxy_scraper.extractors.base import ProxyScraperBase
from proxy_scraper.protocol import Protocol
from proxy_scraper.proxy import Proxy

logger = logging.getLogger(__name__)

class ProxyDBScraper(ProxyScraperBase):
    def get_urls(self):
        # protocols = [Protocol.HTTP, Protocol.HTTPS, Protocol.SOCKS4, Protocol.SOCKS5]
        protocols = [Protocol.HTTP, Protocol.HTTPS]
        countries = ['CN', 'US', 'HK', 'TW']

        base_url = "http://proxydb.net/?protocol={}&anonlvl=1&anonlvl=2&anonlvl=3&anonlvl=4&min_uptime=75&country={}"
        return [base_url.format(protocol, country) for protocol in protocols for country in countries]

    def extract_proxies(self, content: str) -> List[Proxy]:
        proxies = []
        if not content:
            return proxies

        logger.debug("Parsing content to extract proxies...")
        soup = BeautifulSoup(content, 'html.parser')
        rows = soup.select('table tbody tr')
        for row in rows:
            cols = row.select('td')
            if len(cols) >= 5:
                ip_port = cols[0].text.strip()
                ip, port = ip_port.split(':')
                protocol = cols[4].text.strip().lower()

                proxy = Proxy(ip, port, protocol, '')
                proxies.append(proxy)
                logger.debug(f"Extracted proxy: {proxy}")

        return proxies
