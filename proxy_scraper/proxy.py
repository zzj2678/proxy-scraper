
import logging
import os
import ssl
from typing import List, Optional

import certifi
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector, ProxyType
from fake_useragent import UserAgent

from proxy_scraper.config import CONFIG
from proxy_scraper.protocol import Protocol

SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

VALIDATE_URL = CONFIG['validate_url']
TIMEOUT = CONFIG['timeout']


ua = UserAgent()

headers = {
    'User-Agent': ua.random
}

logger = logging.getLogger(__name__)

class Proxy:
    def __init__(self, host: str, port: int, protocol: Protocol, username: Optional[str] = None, password: Optional[str] = None, country: str = ''):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.username = username
        self.password = password
        self.country = country

    def __str__(self):
        return f"{self.protocol}://{self.host}:{self.port}"

    def get_address(self):
        return f"{self.host}:{self.port}"

    async def is_valid(self) -> bool:
        logger.debug(f"Creating ProxyConnector for proxy: {self}")

        connector = ProxyConnector(
            proxy_type=ProxyType.__dict__[self.protocol.upper().upper().rstrip("S")],
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            ssl=SSL_CONTEXT
        )

        try:
            async with ClientSession(connector=connector, headers=headers, raise_for_status=True) as session:
                async with session.get(VALIDATE_URL, timeout=TIMEOUT) as response:
                    if response.status == 200:
                        data = await response.json()
                        origin = data.get('origin')
                        if origin and self.host == origin:
                            logger.debug(f"Proxy {self} is valid.")
                            return True
                    logger.debug(f"Proxy {self} is invalid.")
        except Exception as e:
            logger.debug(f"Error validating proxy {self}: {e}")
        return False

    def detect_protocol(self) -> str:
        if self.port == 443:
            return 'https'
        elif self.port == 80:
            return 'http'
        else:
            # Default to HTTP if protocol is not specified
            return self.protocol if self.protocol else 'http'

class ProxyWriter:
    def save_raw_proxies(self, proxies: List[Proxy], directory: str):
        if not proxies:
            return

        # Create directories if they don't exist
        os.makedirs(directory, exist_ok=True)

        # Group proxies by protocol
        protocol_groups = {}
        for proxy in proxies:
            if proxy.protocol not in protocol_groups:
                protocol = proxy.protocol
                protocol_groups[protocol] = []
            protocol_groups[protocol].append(proxy.get_address())

        # Prepare to write all proxies to files
        for protocol, proxy_list in protocol_groups.items():
            filepath = os.path.join(directory, f'{protocol}.txt')

            # Collect all new proxies to write
            new_proxies = set(proxy_list)

            # Read existing proxies from file
            existing_proxies = set()
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    existing_proxies = {line.strip() for line in f.readlines()}

            # Filter out duplicates from new proxies
            new_proxies = new_proxies - existing_proxies

            if new_proxies:
                with open(filepath, 'a') as f:
                    f.write('\n'.join(new_proxies) + '\n')

                logger.info(f"Added {len(new_proxies)} new {protocol} proxies to {filepath}")
            else:
                logger.info(f"No new proxies to add for {protocol} to {filepath}")

            logger.debug(f"Existing {protocol} proxies in {filepath}: {len(existing_proxies)}")

    def save_proxies(self, proxies: List[Proxy], directory: str):
        if not proxies:
            return

        # Create directories if they don't exist
        os.makedirs(directory, exist_ok=True)

        # Group proxies by protocol
        protocol_groups = {}
        for proxy in proxies:
            if proxy.protocol not in protocol_groups:
                protocol = proxy.protocol
                protocol_groups[protocol] = []
            protocol_groups[protocol].append(proxy.get_address())

        # Prepare to write all proxies to files
        for protocol, proxy_list in protocol_groups.items():
            filepath = os.path.join(directory, f'{protocol}.txt')

            # Collect all new proxies to write
            new_proxies = set(proxy_list)

            # Write new proxies to file (overwrite existing content)
            with open(filepath, 'w') as f:
                f.write('\n'.join(new_proxies) + '\n')

            logger.info(f"Added {len(new_proxies)} new {protocol} proxies to {filepath}")
