import asyncio
import logging
import os
from typing import List

from proxy_scraper.config import CONFIG
from proxy_scraper.proxy import Proxy, ProxyWriter

logger = logging.getLogger(__name__)

PROXY_DIR = CONFIG['proxy_dir']
VALIDATE_URL = CONFIG['validate_url']
TIMEOUT = CONFIG['timeout']

class ProxyValidator:
    def __init__(self):
        self.writer = ProxyWriter()

    async def validate_proxies_in_directory(self, directory: str = os.path.join(PROXY_DIR, 'raw')):
        os.makedirs(PROXY_DIR, exist_ok=True)

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path) and filename.endswith('.txt'):
                logger.info(f"Processing file: {file_path}")
                proxies = self.read_proxies_from_file(file_path)
                valid_proxies = await self.validate_proxies(proxies)
                self.writer.save_proxies(valid_proxies, PROXY_DIR)
                logger.info(f"Moved {len(valid_proxies)} valid proxies from {file_path} to {PROXY_DIR}")

    def read_proxies_from_file(self, file_path: str) -> List[Proxy]:
        protocol = self.extract_protocol_from_filepath(file_path)
        proxies = []
        with open(file_path, 'r') as file:
            for line in file:
                ip_port = line.strip()
                ip, port = ip_port.split(':')
                proxies.append(Proxy(ip, port, protocol, ''))  # Assuming protocol and country are not provided in the file format
        return proxies

    def extract_protocol_from_filepath(self, file_path: str) -> str:
        # Extract protocol from file path assuming it's before the ".txt" extension
        file_name = os.path.basename(file_path)
        protocol = file_name[:-4]  # Remove the ".txt" extension
        return protocol

    async def validate_proxies(self, proxies: List[Proxy]) -> List[Proxy]:
        tasks = [proxy.is_valid() for proxy in proxies]
        valid_results = await asyncio.gather(*tasks)
        return [proxy for proxy, valid in zip(proxies, valid_results) if valid]
