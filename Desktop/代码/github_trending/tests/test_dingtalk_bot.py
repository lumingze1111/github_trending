"""Tests for DingTalk bot."""

import pytest
from unittest.mock import Mock, patch
from src.dingtalk_bot import DingTalkBot
from src.exceptions import DingTalkException


@pytest.fixture
def bot():
    """Create DingTalk bot instance."""
    return DingTalkBot(
        webhook_url="https://oapi.dingtalk.com/robot/send?access_token=test",
        secret="test_secret",
    )


@pytest.fixture
def bot_without_secret():
    """Create DingTalk bot without secret."""
    return DingTalkBot(
        webhook_url="https://oapi.dingtalk.com/robot/send?access_token=test"
    )


def test_dingtalk_bot_initialization():
    """Test DingTalk bot initializes correctly."""
    bot = DingTalkBot(
        webhook_url="https://oapi.dingtalk.com/robot/send?access_token=test",
        secret="test_secret",
    )

    assert bot.webhook_url == "https://oapi.dingtalk.com/robot/send?access_token=test"
    assert bot.secret == "test_secret"


def test_dingtalk_bot_initialization_without_secret():
    """Test DingTalk bot without secret."""
    bot = DingTalkBot(
        webhook_url="https://oapi.dingtalk.com/robot/send?access_token=test"
    )

    assert bot.secret is None


def test_generate_sign(bot):
    """Test signature generation."""
    timestamp = 1615195200000
    sign = bot._generate_sign(timestamp)

    assert isinstance(sign, str)
    assert len(sign) > 0


def test_generate_sign_without_secret(bot_without_secret):
    """Test signature generation without secret."""
    sign = bot_without_secret._generate_sign(1615195200000)
    assert sign == ""


@patch("src.dingtalk_bot.requests.post")
def test_send_text(mock_post, bot):
    """Test sending text message."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
    mock_post.return_value = mock_response

    result = bot.send_text("Test message")

    assert result is True
    mock_post.assert_called_once()

    # Check request data
    call_args = mock_post.call_args
    data = call_args[1]["json"]
    assert data["msgtype"] == "text"
    assert data["text"]["content"] == "Test message"
    assert data["at"]["isAtAll"] is False


@patch("src.dingtalk_bot.requests.post")
def test_send_text_at_all(mock_post, bot):
    """Test sending text message with @all."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
    mock_post.return_value = mock_response

    result = bot.send_text("Test message", at_all=True)

    assert result is True

    # Check @all flag
    call_args = mock_post.call_args
    data = call_args[1]["json"]
    assert data["at"]["isAtAll"] is True


@patch("src.dingtalk_bot.requests.post")
def test_send_markdown(mock_post, bot):
    """Test sending markdown message."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
    mock_post.return_value = mock_response

    result = bot.send_markdown("Test Title", "**Bold text**")

    assert result is True

    # Check request data
    call_args = mock_post.call_args
    data = call_args[1]["json"]
    assert data["msgtype"] == "markdown"
    assert data["markdown"]["title"] == "Test Title"
    assert data["markdown"]["text"] == "**Bold text**"


@patch("src.dingtalk_bot.requests.post")
def test_send_link(mock_post, bot):
    """Test sending link message."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
    mock_post.return_value = mock_response

    result = bot.send_link(
        title="Test Link",
        text="Link description",
        message_url="https://example.com",
        pic_url="https://example.com/pic.jpg",
    )

    assert result is True

    # Check request data
    call_args = mock_post.call_args
    data = call_args[1]["json"]
    assert data["msgtype"] == "link"
    assert data["link"]["title"] == "Test Link"
    assert data["link"]["text"] == "Link description"
    assert data["link"]["messageUrl"] == "https://example.com"
    assert data["link"]["picUrl"] == "https://example.com/pic.jpg"


@patch("src.dingtalk_bot.requests.post")
def test_send_message_http_error(mock_post, bot):
    """Test handling HTTP error."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_post.return_value = mock_response

    with pytest.raises(DingTalkException, match="HTTP error 500"):
        bot.send_text("Test message")


@patch("src.dingtalk_bot.requests.post")
def test_send_message_api_error(mock_post, bot):
    """Test handling DingTalk API error."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"errcode": 310000, "errmsg": "Invalid token"}
    mock_post.return_value = mock_response

    with pytest.raises(DingTalkException, match="DingTalk API error"):
        bot.send_text("Test message")


@patch("src.dingtalk_bot.requests.post")
def test_send_message_network_error(mock_post, bot):
    """Test handling network error."""
    mock_post.side_effect = Exception("Connection timeout")

    with pytest.raises(DingTalkException, match="Failed to send message"):
        bot.send_text("Test message")


@patch("src.dingtalk_bot.requests.post")
def test_send_message_with_signature(mock_post, bot):
    """Test sending message with signature."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
    mock_post.return_value = mock_response

    bot.send_text("Test message")

    # Check URL contains timestamp and sign
    call_args = mock_post.call_args
    url = call_args[0][0]
    assert "timestamp=" in url
    assert "sign=" in url


@patch("src.dingtalk_bot.requests.post")
def test_send_message_without_signature(mock_post, bot_without_secret):
    """Test sending message without signature."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
    mock_post.return_value = mock_response

    bot_without_secret.send_text("Test message")

    # Check URL doesn't contain timestamp and sign
    call_args = mock_post.call_args
    url = call_args[0][0]
    assert "timestamp=" not in url
    assert "sign=" not in url


@patch("src.dingtalk_bot.requests.post")
def test_send_report_notification(mock_post, bot):
    """Test sending report notification."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
    mock_post.return_value = mock_response

    summary = {
        "total_projects": 25,
        "total_stars_today": 5000,
        "top_languages": [
            {"language": "Python", "count": 8},
            {"language": "JavaScript", "count": 6},
            {"language": "Go", "count": 4},
        ],
    }

    result = bot.send_report_notification(
        date="2024-03-14",
        report_url="https://example.com/report.html",
        summary=summary,
    )

    assert result is True

    # Check request data
    call_args = mock_post.call_args
    data = call_args[1]["json"]
    assert data["msgtype"] == "markdown"
    assert "GitHub Trending 日报 - 2024-03-14" in data["markdown"]["title"]
    assert "25个项目" in data["markdown"]["text"]
    assert "5,000" in data["markdown"]["text"]
    assert "Python(8)" in data["markdown"]["text"]
