
import logging
import ssl
from typing import Optional

import certifi
from aiohttp import ClientError, ClientSession
from aiohttp_socks import ProxyConnector, ProxyType
from fake_useragent import UserAgent

from proxy_scraper.config import CONFIG
from proxy_scraper.protocol import Protocol
from proxy_scraper.util.geo import geo_info

SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

VALIDATE_URL = CONFIG['validate_url']
TIMEOUT = CONFIG['timeout']


ua = UserAgent()

headers = {
    'User-Agent': ua.random
}

logger = logging.getLogger(__name__)

class Proxy:
    def __init__(self, host: str, port: int, protocol: Protocol, username: Optional[str] = None, password: Optional[str] = None, country:Optional[str] = None):
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
        except ClientError as e:
            logger.debug(f"Network error while validating proxy {self}: {e}")
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

    def get_region(self) -> dict:
        try:
            return geo_info.get_region(self.host)
        except Exception as e:
            logger.error(f"Error fetching region data for IP {self.host}: {e}")
            return {}

    def get_country(self) -> str:
        if self.country:
            return self.country

        region = self.get_region()
        return region.get('countryCode', 'Unknown')
