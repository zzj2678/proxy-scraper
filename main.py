import argparse
import asyncio
import logging

from proxy_scraper.platform.ip89 import IP89
from proxy_scraper.platform.ip3366 import IP3366
from proxy_scraper.platform.kuaidaili import KuaidailiScraper
from proxy_scraper.platform.proxydb import ProxyDBScraper
from proxy_scraper.platform.txt import TxtScraper
from proxy_scraper.platform.zdaye import ZdayeScraper
from proxy_scraper.proxy_validator import ProxyValidator

logger = logging.getLogger(__name__)

async def scrape_proxies():
    scrapers = [
        ProxyDBScraper(),
        KuaidailiScraper(),
        ZdayeScraper(),
        IP3366(),
        IP89(),
        TxtScraper(),
    ]

    logger.info("Starting scraping proxies...")
    scraping_tasks = [scraper.scrape() for scraper in scrapers]
    await asyncio.gather(*scraping_tasks)
    logger.info("Scraping proxies completed.")

async def validate_proxies():
    validator = ProxyValidator()

    try:
        logger.info("Starting proxy validation...")
        await validator.validate_proxies_in_directory()
        logger.info("Proxy validation completed.")
    except Exception as e:
        logger.error(f"Error during proxy validation: {e}")

def main():
    parser = argparse.ArgumentParser(description="Proxy Scraper and Validator")
    parser.add_argument('--scrape', action='store_true', help="Scrape proxies")
    parser.add_argument('--validate', action='store_true', help="Validate proxies")
    args = parser.parse_args()

    if args.scrape and args.validate:
        logger.error("You can only specify one action: --scrape or --validate.")
        return

    if args.scrape:
        asyncio.run(scrape_proxies())
    elif args.validate:
        asyncio.run(validate_proxies())
    else:
        logger.error("You must specify an action: --scrape or --validate.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
