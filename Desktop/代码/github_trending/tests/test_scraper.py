"""Tests for GitHub Trending scraper."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.scraper import GitHubTrendingScraper
from src.exceptions import ScraperException


@pytest.fixture
def mock_driver():
    """Mock Selenium WebDriver."""
    driver = Mock()
    driver.page_source = "<html><body>Mock HTML</body></html>"
    return driver


@pytest.fixture
def scraper():
    """Create scraper instance."""
    return GitHubTrendingScraper(headless=True)


def test_scraper_initialization():
    """Test scraper initializes correctly."""
    scraper = GitHubTrendingScraper(headless=True)
    assert scraper.headless is True
    assert scraper.driver is None


def test_invalid_time_range(scraper):
    """Test scraper raises exception for invalid time range."""
    with pytest.raises(ScraperException, match="Invalid time_range"):
        scraper.scrape_trending("invalid")


@patch("src.scraper.webdriver.Chrome")
@patch("src.scraper.ChromeDriverManager")
def test_scrape_trending_daily(mock_driver_manager, mock_chrome, scraper, mock_driver):
    """Test scraping daily trending page."""
    mock_chrome.return_value = mock_driver
    mock_driver_manager.return_value.install.return_value = "/path/to/driver"

    html = scraper.scrape_trending("daily")

    assert html == "<html><body>Mock HTML</body></html>"
    mock_driver.get.assert_called_once()
    assert "github.com/trending" in mock_driver.get.call_args[0][0]


@patch("src.scraper.webdriver.Chrome")
@patch("src.scraper.ChromeDriverManager")
def test_scrape_trending_weekly(mock_driver_manager, mock_chrome, scraper, mock_driver):
    """Test scraping weekly trending page."""
    mock_chrome.return_value = mock_driver
    mock_driver_manager.return_value.install.return_value = "/path/to/driver"

    html = scraper.scrape_trending("weekly")

    assert html == "<html><body>Mock HTML</body></html>"
    mock_driver.get.assert_called_once()
    assert "since=weekly" in mock_driver.get.call_args[0][0]


@patch("src.scraper.webdriver.Chrome")
@patch("src.scraper.ChromeDriverManager")
def test_scrape_trending_monthly(mock_driver_manager, mock_chrome, scraper, mock_driver):
    """Test scraping monthly trending page."""
    mock_chrome.return_value = mock_driver
    mock_driver_manager.return_value.install.return_value = "/path/to/driver"

    html = scraper.scrape_trending("monthly")

    assert html == "<html><body>Mock HTML</body></html>"
    mock_driver.get.assert_called_once()
    assert "since=monthly" in mock_driver.get.call_args[0][0]


@patch("src.scraper.webdriver.Chrome")
@patch("src.scraper.ChromeDriverManager")
def test_scrape_all_time_ranges(mock_driver_manager, mock_chrome, scraper, mock_driver):
    """Test scraping all time ranges."""
    mock_chrome.return_value = mock_driver
    mock_driver_manager.return_value.install.return_value = "/path/to/driver"

    results = scraper.scrape_all_time_ranges()

    assert len(results) == 3
    assert "daily" in results
    assert "weekly" in results
    assert "monthly" in results
    assert all(v == "<html><body>Mock HTML</body></html>" for v in results.values())


@patch("src.scraper.webdriver.Chrome")
@patch("src.scraper.ChromeDriverManager")
def test_scraper_context_manager(mock_driver_manager, mock_chrome, mock_driver):
    """Test scraper works as context manager."""
    mock_chrome.return_value = mock_driver
    mock_driver_manager.return_value.install.return_value = "/path/to/driver"

    with GitHubTrendingScraper() as scraper:
        html = scraper.scrape_trending("daily")
        assert html == "<html><body>Mock HTML</body></html>"

    mock_driver.quit.assert_called_once()


def test_scraper_close(scraper, mock_driver):
    """Test scraper closes driver properly."""
    scraper.driver = mock_driver
    scraper.close()

    mock_driver.quit.assert_called_once()
    assert scraper.driver is None


@patch("src.scraper.webdriver.Chrome")
@patch("src.scraper.ChromeDriverManager")
def test_scrape_trending_exception(mock_driver_manager, mock_chrome, scraper):
    """Test scraper handles exceptions."""
    mock_driver = Mock()
    mock_driver.get.side_effect = Exception("Network error")
    mock_chrome.return_value = mock_driver
    mock_driver_manager.return_value.install.return_value = "/path/to/driver"

    with pytest.raises(ScraperException, match="Failed to scrape trending page"):
        scraper.scrape_trending("daily")
