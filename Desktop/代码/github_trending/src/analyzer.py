"""Analyzer for GitHub Trending projects."""

from typing import List, Dict, Optional
from datetime import date
from loguru import logger

from src.database import Database


class TrendingAnalyzer:
    """Analyzer for detecting project highlights and trends."""

    def __init__(self, db: Database):
        """Initialize analyzer with database connection.

        Args:
            db: Database instance for historical data
        """
        self.db = db

    def analyze_projects(
        self, projects: List[Dict], time_range: str, current_date: date
    ) -> List[Dict]:
        """Analyze projects and add highlight information.

        Args:
            projects: List of project dictionaries
            time_range: Time range ('daily', 'weekly', 'monthly')
            current_date: Current date for analysis

        Returns:
            List of projects with added 'highlights' field
        """
        analyzed_projects = []

        for idx, project in enumerate(projects):
            project_copy = project.copy()
            project_copy["ranking"] = idx + 1
            project_copy["highlights"] = self._detect_highlights(
                project, idx + 1, time_range, current_date
            )
            analyzed_projects.append(project_copy)

        logger.info(f"Analyzed {len(analyzed_projects)} projects for {time_range}")
        return analyzed_projects

    def _detect_highlights(
        self, project: Dict, ranking: int, time_range: str, current_date: date
    ) -> List[str]:
        """Detect highlights for a project.

        Args:
            project: Project dictionary
            ranking: Current ranking position
            time_range: Time range ('daily', 'weekly', 'monthly')
            current_date: Current date

        Returns:
            List of highlight strings
        """
        highlights = []

        # Top ranking highlight
        if ranking == 1:
            highlights.append(f"🏆 #{ranking} in {time_range} trending")
        elif ranking <= 3:
            highlights.append(f"🥇 Top 3 in {time_range} trending")
        elif ranking <= 10:
            highlights.append(f"⭐ Top 10 in {time_range} trending")

        # High growth highlight (stars today)
        stars_today = project.get("stars_today", 0)
        if stars_today >= 1000:
            highlights.append(f"🚀 {stars_today:,} stars today")
        elif stars_today >= 500:
            highlights.append(f"📈 {stars_today:,} stars today")
        elif stars_today >= 100:
            highlights.append(f"✨ {stars_today:,} stars today")

        # New project highlight (low total stars but high daily stars)
        total_stars = project.get("stars", 0)
        if total_stars < 1000 and stars_today >= 100:
            highlights.append("🆕 New trending project")

        # Popular project highlight
        if total_stars >= 100000:
            highlights.append(f"💎 {total_stars:,} total stars")
        elif total_stars >= 50000:
            highlights.append(f"⭐ {total_stars:,} total stars")

        # Active community highlight
        forks = project.get("forks", 0)
        if forks >= 10000:
            highlights.append(f"👥 {forks:,} forks")

        # Language highlight
        language = project.get("language", "")
        popular_languages = ["Python", "JavaScript", "TypeScript", "Go", "Rust"]
        if language in popular_languages:
            highlights.append(f"💻 {language}")

        # Ranking change highlight (compare with previous day)
        previous_ranking = self.db.get_previous_ranking(
            project.get("name", ""), time_range, current_date
        )
        if previous_ranking:
            rank_change = previous_ranking - ranking
            if rank_change > 0:
                highlights.append(f"📊 Up {rank_change} positions")
            elif rank_change < 0:
                highlights.append(f"📉 Down {abs(rank_change)} positions")

        return highlights

    def get_trending_summary(
        self, projects: List[Dict], time_range: str
    ) -> Dict[str, any]:
        """Generate summary statistics for trending projects.

        Args:
            projects: List of analyzed projects
            time_range: Time range ('daily', 'weekly', 'monthly')

        Returns:
            Dictionary with summary statistics
        """
        if not projects:
            return {
                "time_range": time_range,
                "total_projects": 0,
                "total_stars_today": 0,
                "top_languages": [],
                "top_project": None,
            }

        # Calculate total stars today
        total_stars_today = sum(p.get("stars_today", 0) for p in projects)

        # Count languages
        language_counts = {}
        for project in projects:
            lang = project.get("language", "Unknown")
            if lang:
                language_counts[lang] = language_counts.get(lang, 0) + 1

        # Sort languages by count
        top_languages = sorted(
            language_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        summary = {
            "time_range": time_range,
            "total_projects": len(projects),
            "total_stars_today": total_stars_today,
            "top_languages": [{"language": lang, "count": count} for lang, count in top_languages],
            "top_project": projects[0] if projects else None,
            "avg_stars_today": total_stars_today // len(projects) if projects else 0,
        }

        logger.info(f"Generated summary for {time_range}: {len(projects)} projects")
        return summary

    def compare_time_ranges(
        self, daily: List[Dict], weekly: List[Dict], monthly: List[Dict]
    ) -> Dict[str, any]:
        """Compare projects across different time ranges.

        Args:
            daily: Daily trending projects
            weekly: Weekly trending projects
            monthly: Monthly trending projects

        Returns:
            Dictionary with comparison insights
        """
        # Find projects that appear in multiple time ranges
        daily_names = {p.get("name") for p in daily}
        weekly_names = {p.get("name") for p in weekly}
        monthly_names = {p.get("name") for p in monthly}

        # Projects in all three
        in_all_three = daily_names & weekly_names & monthly_names

        # Projects only in daily (new trending)
        only_daily = daily_names - weekly_names - monthly_names

        comparison = {
            "consistent_trending": list(in_all_three),
            "new_trending": list(only_daily),
            "daily_count": len(daily),
            "weekly_count": len(weekly),
            "monthly_count": len(monthly),
        }

        logger.info(
            f"Comparison: {len(in_all_three)} consistent, {len(only_daily)} new"
        )
        return comparison
