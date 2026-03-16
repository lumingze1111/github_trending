"""HTML report generator using Jinja2."""

from typing import Dict, List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from loguru import logger

from src.exceptions import TemplateException


class ReportGenerator:
    """Generator for HTML reports using Jinja2 templates."""

    def __init__(self, template_dir: str = "templates"):
        """Initialize report generator.

        Args:
            template_dir: Directory containing Jinja2 templates
        """
        self.template_dir = Path(template_dir)
        if not self.template_dir.exists():
            raise TemplateException(f"Template directory not found: {template_dir}")

        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        logger.info(f"ReportGenerator initialized with template dir: {template_dir}")

    def generate_report(
        self,
        output_path: str,
        date: str,
        daily_projects: List[Dict] = None,
        weekly_projects: List[Dict] = None,
        monthly_projects: List[Dict] = None,
        daily_summary: Dict = None,
        weekly_summary: Dict = None,
        monthly_summary: Dict = None,
    ) -> str:
        """Generate HTML report from template.

        Args:
            output_path: Path to save the generated HTML file
            date: Report date string
            daily_projects: List of daily trending projects
            weekly_projects: List of weekly trending projects
            monthly_projects: List of monthly trending projects
            daily_summary: Summary statistics for daily trending
            weekly_summary: Summary statistics for weekly trending
            monthly_summary: Summary statistics for monthly trending

        Returns:
            Path to the generated HTML file

        Raises:
            TemplateException: If template rendering fails
        """
        try:
            template = self.env.get_template("report.html")
        except TemplateNotFound:
            raise TemplateException("Template file 'report.html' not found")

        # Prepare template data
        template_data = {
            "date": date,
            "daily_projects": daily_projects or [],
            "weekly_projects": weekly_projects or [],
            "monthly_projects": monthly_projects or [],
            "daily_summary": daily_summary,
            "weekly_summary": weekly_summary,
            "monthly_summary": monthly_summary,
        }

        try:
            # Render template
            html_content = template.render(**template_data)

            # Write to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(html_content, encoding="utf-8")

            logger.info(f"Report generated successfully: {output_path}")
            return str(output_file)

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise TemplateException(f"Failed to render template: {e}")

    def generate_simple_report(
        self, output_path: str, date: str, projects: List[Dict]
    ) -> str:
        """Generate a simple text-based report as fallback.

        Args:
            output_path: Path to save the report
            date: Report date
            projects: List of projects

        Returns:
            Path to the generated file
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with output_file.open("w", encoding="utf-8") as f:
                f.write(f"GitHub Trending Report - {date}\n")
                f.write("=" * 50 + "\n\n")

                for idx, project in enumerate(projects, 1):
                    f.write(f"{idx}. {project.get('name', 'Unknown')}\n")
                    f.write(f"   URL: {project.get('url', 'N/A')}\n")
                    f.write(f"   Description: {project.get('description', 'N/A')}\n")
                    f.write(f"   Language: {project.get('language', 'N/A')}\n")
                    f.write(f"   Stars: {project.get('stars', 0):,}\n")
                    f.write(f"   Stars Today: {project.get('stars_today', 0):,}\n")
                    f.write("\n")

            logger.info(f"Simple report generated: {output_path}")
            return str(output_file)

        except Exception as e:
            logger.error(f"Failed to generate simple report: {e}")
            raise TemplateException(f"Failed to generate simple report: {e}")
