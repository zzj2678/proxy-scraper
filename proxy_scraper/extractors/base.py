import abc
import asyncio
import logging

from playwright.async_api import async_playwright

from proxy_scraper.config import CONFIG
from proxy_scraper.proxy_validator import ProxyValidator
from proxy_scraper.proxy_writer import ProxyWriter

logger = logging.getLogger(__name__)

PROXY_DIR = CONFIG['proxy_dir']
TIMEOUT = CONFIG['timeout']

class ProxyScraperBase(abc.ABC):
    def __init__(self):
        self.writer = ProxyWriter()
        self.validator = ProxyValidator()

    @abc.abstractmethod
    def get_urls(self):
        pass

    @abc.abstractmethod
    def extract_proxies(self, content):
        pass

    async def fetch_page_content(self, url):
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            await context.add_init_script("Object.defineProperties(navigator, {webdriver:{get:()=>false}});")
            page = await context.new_page()

            async def handle(route, request):
                if route.request.resource_type in ["stylesheet", "image", "media", "font"]:
                    await route.abort()
                else:
                    await route.continue_()

            await page.route("**/*", handle)

            try:
                logger.info(f"Fetching page content from {url}")
                await page.goto(url, wait_until="domcontentloaded")

                logger.info("Waiting for table rows to load...")
                await page.wait_for_selector("table tbody tr", timeout=TIMEOUT*1000)

                content = await page.content()
                logger.debug("Page content fetched successfully.")
            except Exception as e:
                logger.error(f"Error during request: {e}")
                content = None
            finally:
                await browser.close()
                await playwright.stop()

            return content

    async def fetch_and_process(self, url):
        content = await self.fetch_page_content(url)
        if content:
            proxies = self.extract_proxies(content)
            valid_proxies = await self.validator.validate_proxies(proxies)
            self.writer.save_raw_proxies(valid_proxies)

    async def scrape(self):
        urls = self.get_urls()
        tasks = [self.fetch_and_process(url) for url in urls]
        await asyncio.gather(*tasks)
