import os
from typing import List

from proxy_scraper.config import CONFIG
from proxy_scraper.proxy import Proxy

PROXY_DIR = CONFIG['proxy_dir']

class ProxyFileManager:
    @staticmethod
    def read_proxies_from_raw_directory(directory: str = os.path.join(PROXY_DIR, 'raw')) -> List[Proxy]:
        proxies = []
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path) and filename.endswith('.txt'):
                proxies.extend(ProxyFileManager.read_proxies_from_file(file_path))
        return proxies

    @staticmethod
    def read_proxies_from_file(file_path: str) -> List[Proxy]:
        proxies = []
        protocol = ProxyFileManager.extract_protocol_from_filename(file_path)
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    parts = line.split(' ')
                    host_ip = parts[0]
                    country = parts[1] if len(parts) > 1 else ''
                    if ':' in host_ip:
                        host, ip = host_ip.split(':', 1)
                        proxies.append(Proxy(host, ip, protocol, country))
        return proxies

    @staticmethod
    def extract_protocol_from_filename(filename: str) -> str:
        return os.path.basename(filename).rsplit('.', 1)[0]
