import logging
import os
from typing import Dict, List, Set

from proxy_scraper.config import (
    CONFIG,  # Assuming CONFIG is defined and contains 'proxy_dir'
)
from proxy_scraper.proxy import Proxy
from proxy_scraper.util.geo import GEO

logger = logging.getLogger(__name__)

PROXY_DIR = CONFIG['proxy_dir']  # Default directory for saving proxies

class ProxyWriter:
    def __init__(self, directory: str = PROXY_DIR):
        self.directory = directory
        self.geo = GEO()

    def save_raw_proxies(self, proxies: List[Proxy]):
        raw_directory = os.path.join(self.directory, 'raw')
        self._save_proxies(proxies, raw_directory, append=True)

    def save_proxies(self, proxies: List[Proxy]):
        self._save_proxies(proxies, self.directory, append=False)

    def _group_proxies_by_country_and_protocol(self, proxies: List[Proxy]) -> Dict[str, Dict[str, List[str]]]:
        country_protocol_groups = {}
        for proxy in proxies:
            country = proxy.get_country()
            protocol = proxy.protocol
            if country not in country_protocol_groups:
                country_protocol_groups[country] = {}
            if protocol not in country_protocol_groups[country]:
                country_protocol_groups[country][protocol] = []
            country_protocol_groups[country][protocol].append(f"{proxy.get_address()}")
        return country_protocol_groups

    def save_country_proxies(self, proxies: List[Proxy]):
        country_protocol_groups = self._group_proxies_by_country_and_protocol(proxies)

        for country, protocol_groups in country_protocol_groups.items():
            for protocol, proxy_list in protocol_groups.items():
                protocol_directory = os.path.join(self.directory, protocol)
                os.makedirs(protocol_directory, exist_ok=True)

                country_code = self.geo.get_country_code(country)

                filepath = os.path.join(protocol_directory, f'{country_code}.txt')

                new_proxies = set(proxy_list)
                self._write_proxies_to_file(filepath, new_proxies, append=False)
                logger.info(f"Saved {len(new_proxies)} {protocol} proxies for {country} to {filepath}")

    def _save_proxies(self, proxies: List[Proxy], directory: str, append: bool):
        if not proxies:
            logger.info("No proxies provided to save.")
            return

        os.makedirs(directory, exist_ok=True)

        protocol_groups = self._group_proxies_by_protocol(proxies)

        for protocol, proxy_list in protocol_groups.items():
            filepath = os.path.join(directory, f'{protocol}.txt')

            new_proxies = set(proxy_list)

            if append:
                existing_proxies = self._read_existing_proxies(filepath)
                new_proxies = new_proxies - existing_proxies

            if new_proxies:
                self._write_proxies_to_file(filepath, new_proxies, append)
                logger.info(f"Added {len(new_proxies)} new {protocol} proxies to {filepath}")
            else:
                logger.info(f"No new proxies to add for {protocol} to {filepath}")

    def _group_proxies_by_protocol(self, proxies: List[Proxy]) -> dict:
        protocol_groups = {}
        for proxy in proxies:
            protocol = proxy.protocol
            if protocol not in protocol_groups:
                protocol_groups[protocol] = []
            protocol_groups[protocol].append(f"{proxy.get_address()} {proxy.get_country()}")
        return protocol_groups

    def _read_existing_proxies(self, filepath: str) -> Set[str]:
        if not os.path.exists(filepath):
            return set()
        try:
            with open(filepath, 'r') as f:
                return {line.strip() for line in f.readlines()}
        except Exception as e:
            logger.error(f"Error reading proxies from {filepath}: {e}")
            return set()

    def _write_proxies_to_file(self, filepath: str, proxies: Set[str], append: bool):
        mode = 'a' if append else 'w'
        try:
            with open(filepath, mode) as f:
                f.write('\n'.join(proxies) + '\n')
        except Exception as e:
            logger.error(f"Error writing proxies to {filepath}: {e}")
