"""Tests for GitHub Trending analyzer."""

import pytest
from datetime import date
from unittest.mock import Mock
from src.analyzer import TrendingAnalyzer


@pytest.fixture
def mock_db():
    """Mock database instance."""
    db = Mock()
    db.get_previous_ranking.return_value = None
    return db


@pytest.fixture
def analyzer(mock_db):
    """Create analyzer instance."""
    return TrendingAnalyzer(mock_db)


@pytest.fixture
def sample_projects():
    """Sample projects for testing."""
    return [
        {
            "name": "owner/top-repo",
            "url": "https://github.com/owner/top-repo",
            "description": "Top trending repo",
            "language": "Python",
            "stars": 50000,
            "forks": 5000,
            "stars_today": 1500,
            "built_by": ["user1", "user2"],
        },
        {
            "name": "owner/second-repo",
            "url": "https://github.com/owner/second-repo",
            "description": "Second trending repo",
            "language": "JavaScript",
            "stars": 20000,
            "forks": 2000,
            "stars_today": 800,
            "built_by": ["user3"],
        },
        {
            "name": "owner/new-repo",
            "url": "https://github.com/owner/new-repo",
            "description": "New trending repo",
            "language": "Rust",
            "stars": 500,
            "forks": 50,
            "stars_today": 200,
            "built_by": ["user4"],
        },
    ]


def test_analyzer_initialization(mock_db):
    """Test analyzer initializes correctly."""
    analyzer = TrendingAnalyzer(mock_db)
    assert analyzer.db == mock_db


def test_analyze_projects(analyzer, sample_projects):
    """Test analyzing projects adds highlights and rankings."""
    current_date = date(2024, 3, 14)
    analyzed = analyzer.analyze_projects(sample_projects, "daily", current_date)

    assert len(analyzed) == 3

    # Check rankings are added
    assert analyzed[0]["ranking"] == 1
    assert analyzed[1]["ranking"] == 2
    assert analyzed[2]["ranking"] == 3

    # Check highlights are added
    assert "highlights" in analyzed[0]
    assert "highlights" in analyzed[1]
    assert "highlights" in analyzed[2]

    # Check highlights are lists
    assert isinstance(analyzed[0]["highlights"], list)
    assert len(analyzed[0]["highlights"]) > 0


def test_detect_highlights_top_ranking(analyzer, sample_projects):
    """Test top ranking highlights."""
    current_date = date(2024, 3, 14)

    # Rank 1
    highlights = analyzer._detect_highlights(sample_projects[0], 1, "daily", current_date)
    assert any("🏆 #1" in h for h in highlights)

    # Rank 2
    highlights = analyzer._detect_highlights(sample_projects[1], 2, "daily", current_date)
    assert any("🥇 Top 3" in h for h in highlights)

    # Rank 5
    highlights = analyzer._detect_highlights(sample_projects[0], 5, "daily", current_date)
    assert any("⭐ Top 10" in h for h in highlights)


def test_detect_highlights_high_growth(analyzer, sample_projects):
    """Test high growth highlights based on stars today."""
    current_date = date(2024, 3, 14)

    # 1500 stars today
    highlights = analyzer._detect_highlights(sample_projects[0], 1, "daily", current_date)
    assert any("🚀" in h and "1,500 stars today" in h for h in highlights)

    # 800 stars today
    highlights = analyzer._detect_highlights(sample_projects[1], 2, "daily", current_date)
    assert any("📈" in h and "800 stars today" in h for h in highlights)

    # 200 stars today
    highlights = analyzer._detect_highlights(sample_projects[2], 3, "daily", current_date)
    assert any("✨" in h and "200 stars today" in h for h in highlights)


def test_detect_highlights_new_project(analyzer, sample_projects):
    """Test new project highlight."""
    current_date = date(2024, 3, 14)

    # New project: low total stars but high daily stars
    highlights = analyzer._detect_highlights(sample_projects[2], 3, "daily", current_date)
    assert any("🆕 New trending project" in h for h in highlights)


def test_detect_highlights_popular_project(analyzer, sample_projects):
    """Test popular project highlight."""
    current_date = date(2024, 3, 14)

    # 50k stars
    highlights = analyzer._detect_highlights(sample_projects[0], 1, "daily", current_date)
    assert any("⭐" in h and "50,000 total stars" in h for h in highlights)


def test_detect_highlights_language(analyzer, sample_projects):
    """Test language highlight."""
    current_date = date(2024, 3, 14)

    # Python
    highlights = analyzer._detect_highlights(sample_projects[0], 1, "daily", current_date)
    assert any("💻 Python" in h for h in highlights)

    # JavaScript
    highlights = analyzer._detect_highlights(sample_projects[1], 2, "daily", current_date)
    assert any("💻 JavaScript" in h for h in highlights)


def test_detect_highlights_ranking_change(analyzer, mock_db, sample_projects):
    """Test ranking change highlight."""
    current_date = date(2024, 3, 14)

    # Mock previous ranking
    mock_db.get_previous_ranking.return_value = 5

    # Current rank 1, previous rank 5 = up 4 positions
    highlights = analyzer._detect_highlights(sample_projects[0], 1, "daily", current_date)
    assert any("📊 Up 4 positions" in h for h in highlights)


def test_get_trending_summary(analyzer, sample_projects):
    """Test generating trending summary."""
    analyzed = analyzer.analyze_projects(sample_projects, "daily", date(2024, 3, 14))
    summary = analyzer.get_trending_summary(analyzed, "daily")

    assert summary["time_range"] == "daily"
    assert summary["total_projects"] == 3
    assert summary["total_stars_today"] == 2500  # 1500 + 800 + 200
    assert summary["avg_stars_today"] == 833  # 2500 // 3
    assert len(summary["top_languages"]) > 0
    assert summary["top_project"]["name"] == "owner/top-repo"


def test_get_trending_summary_empty_projects(analyzer):
    """Test summary with empty project list."""
    summary = analyzer.get_trending_summary([], "daily")

    assert summary["time_range"] == "daily"
    assert summary["total_projects"] == 0
    assert summary["total_stars_today"] == 0
    assert summary["top_languages"] == []
    assert summary["top_project"] is None


def test_get_trending_summary_top_languages(analyzer):
    """Test top languages in summary."""
    projects = [
        {"name": "repo1", "language": "Python", "stars_today": 100},
        {"name": "repo2", "language": "Python", "stars_today": 200},
        {"name": "repo3", "language": "JavaScript", "stars_today": 150},
        {"name": "repo4", "language": "Rust", "stars_today": 50},
        {"name": "repo5", "language": "Go", "stars_today": 75},
    ]

    summary = analyzer.get_trending_summary(projects, "daily")

    assert len(summary["top_languages"]) > 0
    # Python should be first (appears twice)
    assert summary["top_languages"][0]["language"] == "Python"
    assert summary["top_languages"][0]["count"] == 2


def test_compare_time_ranges(analyzer, sample_projects):
    """Test comparing projects across time ranges."""
    comparison = analyzer.compare_time_ranges(
        sample_projects, sample_projects[:2], sample_projects[:1]
    )

    assert "daily_count" in comparison
    assert "weekly_count" in comparison
    assert "monthly_count" in comparison
    assert "consistent_trending" in comparison

    assert comparison["daily_count"] == 3
    assert comparison["weekly_count"] == 2
    assert comparison["monthly_count"] == 1


def test_compare_time_ranges_finds_consistent_projects(analyzer):
    """Test finding projects that appear in all time ranges."""
    daily = [
        {"name": "owner/repo1", "stars_today": 100},
        {"name": "owner/repo2", "stars_today": 200},
    ]
    weekly = [
        {"name": "owner/repo1", "stars_today": 500},
        {"name": "owner/repo3", "stars_today": 300},
    ]
    monthly = [
        {"name": "owner/repo1", "stars_today": 1000},
        {"name": "owner/repo4", "stars_today": 400},
    ]

    comparison = analyzer.compare_time_ranges(daily, weekly, monthly)

    # repo1 appears in all three
    assert len(comparison["consistent_trending"]) == 1
    assert comparison["consistent_trending"][0] == "owner/repo1"
