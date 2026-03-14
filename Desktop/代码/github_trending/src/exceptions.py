"""Custom exception classes for the GitHub Trending scraper."""


class ScraperException(Exception):
    """Raised when scraping fails (network errors, page load timeout, etc.)."""
    pass


class ParserException(Exception):
    """Raised when parsing HTML fails."""
    pass


class DatabaseException(Exception):
    """Raised when database operations fail."""
    pass


class TemplateException(Exception):
    """Raised when template rendering fails."""
    pass


class OSSException(Exception):
    """Raised when OSS upload fails."""
    pass


class DingTalkException(Exception):
    """Raised when DingTalk message sending fails."""
    pass


class ConfigException(Exception):
    """Raised when configuration is invalid or missing."""
    pass
