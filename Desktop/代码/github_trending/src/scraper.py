"""GitHub Trending scraper using Selenium."""

from typing import Dict, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger
import time
import random

from src.exceptions import ScraperException
from src.utils import retry_on_exception


class GitHubTrendingScraper:
    """Scraper for GitHub trending page."""

    BASE_URL = "https://github.com/trending"
    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    ]

    def __init__(self, headless: bool = True):
        """Initialize scraper with Chrome options.

        Args:
            headless: Run browser in headless mode
        """
        self.headless = headless
        self.driver = None

    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with options."""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"user-agent={random.choice(self.USER_AGENTS)}")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        return driver

    @retry_on_exception(max_retries=3, backoff=[2, 4, 8])
    def scrape_trending(self, time_range: str = "daily") -> str:
        """Scrape GitHub trending page.

        Args:
            time_range: One of 'daily', 'weekly', 'monthly'

        Returns:
            HTML content of the trending page

        Raises:
            ScraperException: If scraping fails
        """
        if time_range not in ["daily", "weekly", "monthly"]:
            raise ScraperException(f"Invalid time_range: {time_range}")

        url_map = {
            "daily": self.BASE_URL,
            "weekly": f"{self.BASE_URL}?since=weekly",
            "monthly": f"{self.BASE_URL}?since=monthly",
        }
        url = url_map[time_range]

        try:
            if not self.driver:
                self.driver = self._setup_driver()

            logger.info(f"Scraping {url}")
            self.driver.get(url)

            # Wait for trending list to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "Box-row"))
            )

            # Random delay to avoid detection
            time.sleep(random.uniform(1, 3))

            html_content = self.driver.page_source
            logger.info(f"Successfully scraped {time_range} trending page")
            return html_content

        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            raise ScraperException(f"Failed to scrape trending page: {e}")

    def scrape_all_time_ranges(self) -> Dict[str, str]:
        """Scrape all three time ranges.

        Returns:
            Dictionary with time_range as key and HTML content as value
        """
        results = {}
        for time_range in ["daily", "weekly", "monthly"]:
            try:
                results[time_range] = self.scrape_trending(time_range)
            except ScraperException as e:
                logger.error(f"Failed to scrape {time_range}: {e}")
                results[time_range] = None
        return results

    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("WebDriver closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
