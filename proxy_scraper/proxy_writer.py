import logging
import os
from typing import Dict, List, Set

from proxy_scraper.config import (
    CONFIG,  # Assuming CONFIG is defined and contains 'proxy_dir'
)
from proxy_scraper.proxy import Proxy

logger = logging.getLogger(__name__)

PROXY_DIR = CONFIG['proxy_dir']  # Default directory for saving proxies

class ProxyWriter:
    def __init__(self, directory: str = PROXY_DIR):
        self.directory = directory

    def save_raw_proxies(self, proxies: List[Proxy]):
        raw_directory = os.path.join(self.directory, 'raw')
        self._save_proxies(proxies, raw_directory, include_country=False, append=True)

    def save_proxies(self, proxies: List[Proxy]):
        self._save_proxies(proxies, self.directory, include_country=True, append=False)

    def save_country_proxies(self, proxies: List[Proxy]):
        country_protocol_groups = self._group_proxies_by_country_and_protocol(proxies)

        for country_code, protocol_groups in country_protocol_groups.items():
            for protocol, proxy_list in protocol_groups.items():
                protocol_directory = os.path.join(self.directory, protocol)
                os.makedirs(protocol_directory, exist_ok=True)

                filepath = os.path.join(protocol_directory, f'{country_code}.txt')

                formatted_proxies = {f"{proxy.get_address()}" for proxy in proxy_list}
                self._write_proxies_to_file(filepath, formatted_proxies, append=False)
                logger.info(f"Saved {len(formatted_proxies)} {protocol} proxies for {country_code} to {filepath}")

    def _save_proxies(self, proxies: List[Proxy], directory: str, include_country: bool, append: bool):
        if not proxies:
            logger.info("No proxies provided to save.")
            return

        os.makedirs(directory, exist_ok=True)

        protocol_groups = self._group_proxies_by_protocol(proxies)

        for protocol, proxy_list in protocol_groups.items():
            filepath = os.path.join(directory, f'{protocol}.txt')

            if include_country:
                formatted_proxies = {f"{proxy.get_address()} {proxy.get_country()}" for proxy in proxy_list}
            else:
                formatted_proxies = {proxy.get_address() for proxy in proxy_list}

            if append:
                existing_proxies = self._read_existing_proxies(filepath)
                new_proxies = {fp for fp in formatted_proxies if fp not in existing_proxies}
            else:
                new_proxies = formatted_proxies

            if new_proxies:
                self._write_proxies_to_file(filepath, new_proxies, append)
                logger.info(f"Added {len(new_proxies)} new {protocol} proxies to {filepath}")
            else:
                logger.info(f"No new proxies to add for {protocol} to {filepath}")

    def _group_proxies_by_protocol(self, proxies: List[Proxy]) -> Dict[str, List[Proxy]]:
        protocol_groups = {}
        for proxy in proxies:
            protocol = proxy.protocol
            if protocol not in protocol_groups:
                protocol_groups[protocol] = []
            protocol_groups[protocol].append(proxy)
        return protocol_groups

    def _group_proxies_by_country_and_protocol(self, proxies: List[Proxy]) -> Dict[str, Dict[str, List[Proxy]]]:
        country_protocol_groups = {}
        for proxy in proxies:
            country = proxy.get_country()
            protocol = proxy.protocol
            if country not in country_protocol_groups:
                country_protocol_groups[country] = {}
            if protocol not in country_protocol_groups[country]:
                country_protocol_groups[country][protocol] = []
            country_protocol_groups[country][protocol].append(proxy)
        return country_protocol_groups

    def _read_existing_proxies(self, filepath: str) -> Set[str]:
        if not os.path.exists(filepath):
            return set()
        try:
            with open(filepath, 'r') as f:
                return {line.strip().split()[0] for line in f.readlines()}  # Extract only the IP part
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
