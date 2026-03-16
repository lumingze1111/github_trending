"""DingTalk bot for sending notifications."""

import time
import hmac
import hashlib
import base64
import urllib.parse
from typing import Optional
import requests
from loguru import logger

from src.exceptions import DingTalkException
from src.utils import retry_on_exception


class DingTalkBot:
    """Bot for sending messages to DingTalk."""

    def __init__(self, webhook_url: str, secret: Optional[str] = None):
        """Initialize DingTalk bot.

        Args:
            webhook_url: DingTalk webhook URL
            secret: Secret for signature verification (optional)
        """
        self.webhook_url = webhook_url
        self.secret = secret
        logger.info("DingTalk bot initialized")

    def _generate_sign(self, timestamp: int) -> str:
        """Generate signature for DingTalk webhook.

        Args:
            timestamp: Current timestamp in milliseconds

        Returns:
            Base64 encoded signature
        """
        if not self.secret:
            return ""

        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            self.secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign

    @retry_on_exception(max_retries=3, backoff=[1, 2, 4])
    def send_text(self, content: str, at_all: bool = False) -> bool:
        """Send text message to DingTalk.

        Args:
            content: Message content
            at_all: Whether to @ all members

        Returns:
            True if sent successfully

        Raises:
            DingTalkException: If sending fails
        """
        data = {
            "msgtype": "text",
            "text": {"content": content},
            "at": {"isAtAll": at_all},
        }

        return self._send_message(data)

    @retry_on_exception(max_retries=3, backoff=[1, 2, 4])
    def send_markdown(
        self, title: str, text: str, at_all: bool = False
    ) -> bool:
        """Send markdown message to DingTalk.

        Args:
            title: Message title
            text: Markdown formatted text
            at_all: Whether to @ all members

        Returns:
            True if sent successfully

        Raises:
            DingTalkException: If sending fails
        """
        data = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": text},
            "at": {"isAtAll": at_all},
        }

        return self._send_message(data)

    @retry_on_exception(max_retries=3, backoff=[1, 2, 4])
    def send_link(
        self, title: str, text: str, message_url: str, pic_url: str = ""
    ) -> bool:
        """Send link message to DingTalk.

        Args:
            title: Message title
            text: Message text
            message_url: URL to open when clicked
            pic_url: Picture URL (optional)

        Returns:
            True if sent successfully

        Raises:
            DingTalkException: If sending fails
        """
        data = {
            "msgtype": "link",
            "link": {
                "title": title,
                "text": text,
                "messageUrl": message_url,
                "picUrl": pic_url,
            },
        }

        return self._send_message(data)

    def _send_message(self, data: dict) -> bool:
        """Send message to DingTalk webhook.

        Args:
            data: Message data

        Returns:
            True if sent successfully

        Raises:
            DingTalkException: If sending fails
        """
        try:
            # Add signature if secret is provided
            url = self.webhook_url
            if self.secret:
                timestamp = int(time.time() * 1000)
                sign = self._generate_sign(timestamp)
                url = f"{url}&timestamp={timestamp}&sign={sign}"

            # Send request
            response = requests.post(
                url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            # Check response
            if response.status_code != 200:
                raise DingTalkException(
                    f"HTTP error {response.status_code}: {response.text}"
                )

            result = response.json()
            if result.get("errcode") != 0:
                raise DingTalkException(
                    f"DingTalk API error: {result.get('errmsg', 'Unknown error')}"
                )

            logger.info("Message sent to DingTalk successfully")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending to DingTalk: {e}")
            raise DingTalkException(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Failed to send message to DingTalk: {e}")
            raise DingTalkException(f"Failed to send message: {e}")

    def send_report_notification(
        self, date: str, report_url: str, summary: dict
    ) -> bool:
        """Send GitHub trending report notification.

        Args:
            date: Report date
            report_url: URL to the report
            summary: Summary statistics

        Returns:
            True if sent successfully
        """
        title = f"GitHub Trending 日报 - {date}"

        # Build summary text
        total_projects = summary.get("total_projects", 0)
        total_stars = summary.get("total_stars_today", 0)
        top_languages = summary.get("top_languages", [])

        lang_text = ", ".join(
            [f"{lang['language']}({lang['count']})" for lang in top_languages[:3]]
        )

        text = (
            f"📊 今日trending: {total_projects}个项目\n"
            f"⭐ 新增stars: {total_stars:,}\n"
            f"💻 热门语言: {lang_text}\n\n"
            f"[点击查看完整报告]({report_url})"
        )

        return self.send_markdown(title, text)
