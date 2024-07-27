import asyncio
import logging
from typing import List

from proxy_scraper.proxy import Proxy

logger = logging.getLogger(__name__)

class ProxyValidator:
    # def __init__(self):
    #     self.writer = ProxyWriter()

    # async def validate_proxies_in_directory(self, directory: str):
    #     proxies = ProxyFileManager.read_proxies_from_directory(directory)
    #     valid_proxies = await self.validate_proxies(proxies)
    #     return valid_proxies

    async def validate_proxies(self, proxies: List[Proxy]) -> List[Proxy]:
        tasks = [proxy.is_valid() for proxy in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [proxy for proxy, result in zip(proxies, results) if result is True]
