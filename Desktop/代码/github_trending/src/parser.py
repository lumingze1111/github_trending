"""HTML parser for GitHub Trending pages."""

from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from loguru import logger
import re

from src.exceptions import ParserException


class TrendingParser:
    """Parser for GitHub trending HTML content."""

    def __init__(self):
        """Initialize parser."""
        pass

    def parse_trending_page(self, html_content: str) -> List[Dict[str, any]]:
        """Parse GitHub trending page HTML.

        Args:
            html_content: HTML content from trending page

        Returns:
            List of project dictionaries with extracted information

        Raises:
            ParserException: If parsing fails
        """
        if not html_content:
            raise ParserException("Empty HTML content")

        try:
            soup = BeautifulSoup(html_content, "lxml")
            projects = []

            # Find all project rows
            project_rows = soup.find_all("article", class_="Box-row")

            if not project_rows:
                logger.warning("No project rows found in HTML")
                return []

            for row in project_rows:
                try:
                    project = self._parse_project_row(row)
                    if project:
                        projects.append(project)
                except Exception as e:
                    logger.warning(f"Failed to parse project row: {e}")
                    continue

            logger.info(f"Successfully parsed {len(projects)} projects")
            return projects

        except Exception as e:
            logger.error(f"Failed to parse HTML: {e}")
            raise ParserException(f"Failed to parse trending page: {e}")

    def _parse_project_row(self, row) -> Optional[Dict[str, any]]:
        """Parse a single project row.

        Args:
            row: BeautifulSoup element for project row

        Returns:
            Dictionary with project information or None if parsing fails
        """
        project = {}

        # Extract project name and URL
        h2_tag = row.find("h2", class_="h3")
        if not h2_tag:
            return None

        link = h2_tag.find("a")
        if not link:
            return None

        project["name"] = link.get("href", "").strip("/")
        project["url"] = f"https://github.com{link.get('href', '')}"

        # Extract description
        desc_tag = row.find("p", class_="col-9")
        project["description"] = desc_tag.get_text(strip=True) if desc_tag else ""

        # Extract language
        lang_tag = row.find("span", attrs={"itemprop": "programmingLanguage"})
        project["language"] = lang_tag.get_text(strip=True) if lang_tag else ""

        # Extract stars
        stars_tag = row.find("svg", class_="octicon-star")
        if stars_tag:
            stars_parent = stars_tag.find_parent("a")
            if stars_parent:
                stars_text = stars_parent.get_text(strip=True)
                project["stars"] = self._parse_number(stars_text)
            else:
                project["stars"] = 0
        else:
            project["stars"] = 0

        # Extract forks
        forks_tag = row.find("svg", class_="octicon-repo-forked")
        if forks_tag:
            forks_parent = forks_tag.find_parent("a")
            if forks_parent:
                forks_text = forks_parent.get_text(strip=True)
                project["forks"] = self._parse_number(forks_text)
            else:
                project["forks"] = 0
        else:
            project["forks"] = 0

        # Extract today's stars
        stars_today_tag = row.find("span", class_="d-inline-block float-sm-right")
        if stars_today_tag:
            stars_today_text = stars_today_tag.get_text(strip=True)
            project["stars_today"] = self._parse_number(stars_today_text)
        else:
            project["stars_today"] = 0

        # Extract built by (contributors)
        built_by = []
        built_by_section = row.find("span", string=re.compile("Built by"))
        if built_by_section:
            avatars = built_by_section.find_next_siblings("a")
            for avatar in avatars[:5]:  # Limit to 5 contributors
                img = avatar.find("img")
                if img and img.get("alt"):
                    built_by.append(img.get("alt").strip("@"))
        project["built_by"] = built_by

        return project

    def _parse_number(self, text: str) -> int:
        """Parse number from text (handles k, m suffixes).

        Args:
            text: Text containing number (e.g., "1.2k", "3,456", "89 stars today")

        Returns:
            Parsed integer value
        """
        if not text:
            return 0

        # Extract just the number part using regex
        # Matches patterns like: 1234, 1,234, 1.2k, 1.5m
        match = re.search(r'([\d,]+\.?\d*)\s*([km])?', text.lower())
        if not match:
            logger.warning(f"Failed to parse number from: {text}")
            return 0

        number_str = match.group(1).replace(",", "")
        suffix = match.group(2)

        # Handle k (thousands) and m (millions) suffixes
        multiplier = 1
        if suffix == "k":
            multiplier = 1000
        elif suffix == "m":
            multiplier = 1000000

        try:
            # Convert to float first (handles decimals like "1.2k")
            number = float(number_str)
            return int(number * multiplier)
        except ValueError:
            logger.warning(f"Failed to parse number from: {text}")
            return 0

    def validate_project(self, project: Dict[str, any]) -> bool:
        """Validate that project has required fields.

        Args:
            project: Project dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["name", "url"]
        return all(field in project and project[field] for field in required_fields)
