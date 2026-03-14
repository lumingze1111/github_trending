# tests/test_exceptions.py
import pytest
from src.exceptions import (
    ScraperException,
    ParserException,
    DatabaseException,
    TemplateException,
    OSSException,
    DingTalkException,
    ConfigException
)


def test_scraper_exception():
    exc = ScraperException("Network timeout")
    assert str(exc) == "Network timeout"
    assert isinstance(exc, Exception)


def test_parser_exception():
    exc = ParserException("Invalid HTML structure")
    assert str(exc) == "Invalid HTML structure"


def test_database_exception():
    exc = DatabaseException("Connection failed")
    assert str(exc) == "Connection failed"


def test_template_exception():
    exc = TemplateException("Template not found")
    assert str(exc) == "Template not found"


def test_oss_exception():
    exc = OSSException("Upload failed")
    assert str(exc) == "Upload failed"


def test_dingtalk_exception():
    exc = DingTalkException("Webhook error")
    assert str(exc) == "Webhook error"


def test_config_exception():
    exc = ConfigException("Missing required config")
    assert str(exc) == "Missing required config"
