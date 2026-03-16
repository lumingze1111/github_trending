"""Main scheduler for GitHub Trending scraper."""

import sys
from datetime import date
from pathlib import Path
from typing import Dict, List
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from src.config import Config
from src.scraper import GitHubTrendingScraper
from src.parser import TrendingParser
from src.analyzer import TrendingAnalyzer
from src.database import Database
from src.report_generator import ReportGenerator
from src.oss_uploader import OSSUploader
from src.dingtalk_bot import DingTalkBot
from src.exceptions import (
    ScraperException,
    ParserException,
    DatabaseException,
    TemplateException,
    OSSException,
    DingTalkException,
)


class TrendingScheduler:
    """Scheduler for GitHub Trending scraper workflow."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize scheduler with configuration.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = Config.load(config_path)

        # Setup logging
        self._setup_logging()

        # Initialize components
        self.db = Database(self.config["database"]["path"])
        self.scraper = GitHubTrendingScraper(
            headless=self.config["scraper"]["headless"]
        )
        self.parser = TrendingParser()
        self.analyzer = TrendingAnalyzer(self.db)
        self.report_generator = ReportGenerator()

        # Initialize OSS uploader
        oss_config = self.config["oss"]
        self.oss_uploader = OSSUploader(
            access_key_id=oss_config["access_key_id"],
            access_key_secret=oss_config["access_key_secret"],
            bucket_name=oss_config["bucket_name"],
            endpoint=oss_config["endpoint"],
            path_prefix=oss_config.get("path_prefix", ""),
        )

        # Initialize DingTalk bot
        dingtalk_config = self.config["dingtalk"]
        self.dingtalk_bot = DingTalkBot(
            webhook_url=dingtalk_config["webhook_url"],
            secret=dingtalk_config.get("secret"),
        )

        logger.info("TrendingScheduler initialized successfully")

    def _setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config.get("logging", {})
        log_level = log_config.get("level", "INFO")
        log_file = log_config.get("file", "/app/logs/scraper.log")

        # Remove default handler
        logger.remove()

        # Add console handler
        logger.add(
            sys.stderr,
            format=log_config.get(
                "format",
                "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
            ),
            level=log_level,
        )

        # Add file handler
        log_file_path = Path(log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_file,
            format=log_config.get(
                "format",
                "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
            ),
            level=log_level,
            rotation=log_config.get("max_bytes", 10485760),
            retention=log_config.get("backup_count", 5),
        )

        logger.info("Logging configured")

    def run_job(self):
        """Execute the complete trending scraping workflow."""
        current_date = date.today()
        logger.info(f"Starting trending scraping job for {current_date}")

        try:
            # Step 1: Scrape trending pages
            logger.info("Step 1: Scraping GitHub trending pages")
            html_data = self._scrape_all_pages()

            # Step 2: Parse HTML content
            logger.info("Step 2: Parsing HTML content")
            parsed_data = self._parse_all_pages(html_data)

            # Step 3: Analyze and add highlights
            logger.info("Step 3: Analyzing projects and adding highlights")
            analyzed_data = self._analyze_all_pages(parsed_data, current_date)

            # Step 4: Save to database
            logger.info("Step 4: Saving data to database")
            self._save_to_database(analyzed_data, current_date)

            # Step 5: Generate summaries
            logger.info("Step 5: Generating summaries")
            summaries = self._generate_summaries(analyzed_data)

            # Step 6: Generate HTML report
            logger.info("Step 6: Generating HTML report")
            report_path = self._generate_report(analyzed_data, summaries, current_date)

            # Step 7: Upload to OSS
            logger.info("Step 7: Uploading report to OSS")
            report_url = self._upload_to_oss(report_path, current_date)

            # Step 8: Send DingTalk notification
            logger.info("Step 8: Sending DingTalk notification")
            self._send_notification(report_url, summaries["daily"], current_date)

            # Step 9: Save report metadata
            logger.info("Step 9: Saving report metadata")
            self.db.save_daily_report(
                date=str(current_date),
                oss_url=report_url,
                dingtalk_sent=True,
            )

            logger.info(f"Job completed successfully for {current_date}")

        except Exception as e:
            logger.error(f"Job failed: {e}", exc_info=True)
            self._send_error_notification(str(e))
            raise

        finally:
            # Cleanup
            self.scraper.close()

    def _scrape_all_pages(self) -> Dict[str, str]:
        """Scrape all three time ranges.

        Returns:
            Dictionary with time_range as key and HTML content as value
        """
        html_data = {}

        for time_range in ["daily", "weekly", "monthly"]:
            try:
                html = self.scraper.scrape_trending(time_range)
                html_data[time_range] = html
                logger.info(f"Successfully scraped {time_range} trending")
            except ScraperException as e:
                logger.error(f"Failed to scrape {time_range}: {e}")
                html_data[time_range] = None

        return html_data

    def _parse_all_pages(self, html_data: Dict[str, str]) -> Dict[str, List[Dict]]:
        """Parse all HTML content.

        Args:
            html_data: Dictionary of HTML content

        Returns:
            Dictionary with time_range as key and parsed projects as value
        """
        parsed_data = {}

        for time_range, html in html_data.items():
            if html is None:
                parsed_data[time_range] = []
                continue

            try:
                projects = self.parser.parse_trending_page(html)
                # Validate projects
                valid_projects = [
                    p for p in projects if self.parser.validate_project(p)
                ]
                parsed_data[time_range] = valid_projects
                logger.info(f"Parsed {len(valid_projects)} projects from {time_range}")
            except ParserException as e:
                logger.error(f"Failed to parse {time_range}: {e}")
                parsed_data[time_range] = []

        return parsed_data

    def _analyze_all_pages(
        self, parsed_data: Dict[str, List[Dict]], current_date: date
    ) -> Dict[str, List[Dict]]:
        """Analyze all parsed projects.

        Args:
            parsed_data: Dictionary of parsed projects
            current_date: Current date

        Returns:
            Dictionary with analyzed projects
        """
        analyzed_data = {}

        for time_range, projects in parsed_data.items():
            analyzed_projects = self.analyzer.analyze_projects(
                projects, time_range, current_date
            )
            analyzed_data[time_range] = analyzed_projects
            logger.info(f"Analyzed {len(analyzed_projects)} projects for {time_range}")

        return analyzed_data

    def _save_to_database(self, analyzed_data: Dict[str, List[Dict]], current_date: date):
        """Save analyzed data to database.

        Args:
            analyzed_data: Dictionary of analyzed projects
            current_date: Current date
        """
        for time_range, projects in analyzed_data.items():
            if not projects:
                continue

            try:
                self.db.save_projects(
                    projects, date=str(current_date), period=time_range
                )
                logger.info(f"Saved {len(projects)} projects for {time_range}")
            except DatabaseException as e:
                logger.error(f"Failed to save {time_range} data: {e}")

    def _generate_summaries(self, analyzed_data: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """Generate summaries for all time ranges.

        Args:
            analyzed_data: Dictionary of analyzed projects

        Returns:
            Dictionary with summaries
        """
        summaries = {}

        for time_range, projects in analyzed_data.items():
            summary = self.analyzer.get_trending_summary(projects, time_range)
            summaries[time_range] = summary

        return summaries

    def _generate_report(
        self, analyzed_data: Dict[str, List[Dict]], summaries: Dict[str, Dict], current_date: date
    ) -> str:
        """Generate HTML report.

        Args:
            analyzed_data: Dictionary of analyzed projects
            summaries: Dictionary of summaries
            current_date: Current date

        Returns:
            Path to generated report
        """
        output_dir = Path("/tmp/reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"github-trending-{current_date}.html"

        try:
            self.report_generator.generate_report(
                output_path=str(output_path),
                date=str(current_date),
                daily_projects=analyzed_data.get("daily", []),
                weekly_projects=analyzed_data.get("weekly", []),
                monthly_projects=analyzed_data.get("monthly", []),
                daily_summary=summaries.get("daily"),
                weekly_summary=summaries.get("weekly"),
                monthly_summary=summaries.get("monthly"),
            )
            logger.info(f"Report generated: {output_path}")
            return str(output_path)
        except TemplateException as e:
            logger.error(f"Failed to generate report: {e}")
            # Fallback to simple report
            simple_path = output_dir / f"github-trending-{current_date}.txt"
            self.report_generator.generate_simple_report(
                str(simple_path), str(current_date), analyzed_data.get("daily", [])
            )
            return str(simple_path)

    def _upload_to_oss(self, report_path: str, current_date: date) -> str:
        """Upload report to OSS.

        Args:
            report_path: Path to report file
            current_date: Current date

        Returns:
            Public URL of uploaded file
        """
        object_name = f"github-trending-{current_date}.html"

        try:
            url = self.oss_uploader.upload_file(report_path, object_name)
            logger.info(f"Report uploaded to OSS: {url}")
            return url
        except OSSException as e:
            logger.error(f"Failed to upload to OSS: {e}")
            raise

    def _send_notification(self, report_url: str, summary: Dict, current_date: date):
        """Send DingTalk notification.

        Args:
            report_url: URL to the report
            summary: Summary statistics
            current_date: Current date
        """
        try:
            self.dingtalk_bot.send_report_notification(
                date=str(current_date),
                report_url=report_url,
                summary=summary,
            )
            logger.info("DingTalk notification sent successfully")
        except DingTalkException as e:
            logger.error(f"Failed to send DingTalk notification: {e}")
            raise

    def _send_error_notification(self, error_message: str):
        """Send error notification to DingTalk.

        Args:
            error_message: Error message
        """
        try:
            self.dingtalk_bot.send_text(
                f"⚠️ GitHub Trending 爬虫任务失败\n\n错误信息：{error_message}"
            )
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")

    def start(self):
        """Start the scheduler."""
        scheduler = BlockingScheduler()

        # Get schedule configuration
        schedule_config = self.config.get("scheduler", {})
        run_time = schedule_config.get("run_time", "09:00")
        timezone = schedule_config.get("timezone", "Asia/Shanghai")

        # Parse run time
        hour, minute = run_time.split(":")

        # Add job
        scheduler.add_job(
            self.run_job,
            CronTrigger(hour=int(hour), minute=int(minute), timezone=timezone),
            id="trending_scraper",
            name="GitHub Trending Scraper",
            replace_existing=True,
        )

        logger.info(f"Scheduler started. Job will run daily at {run_time} {timezone}")

        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped")


def main():
    """Main entry point."""
    scheduler = TrendingScheduler()

    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        logger.info("Running in test mode (single execution)")
        scheduler.run_job()
    else:
        logger.info("Starting scheduler")
        scheduler.start()


if __name__ == "__main__":
    main()
