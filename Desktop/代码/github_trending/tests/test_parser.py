"""Tests for GitHub Trending parser."""

import pytest
from src.parser import TrendingParser
from src.exceptions import ParserException


@pytest.fixture
def parser():
    """Create parser instance."""
    return TrendingParser()


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <html>
        <body>
            <article class="Box-row">
                <h2 class="h3">
                    <a href="/owner/repo-name">owner/repo-name</a>
                </h2>
                <p class="col-9">A sample repository description</p>
                <span itemprop="programmingLanguage">Python</span>
                <a href="/owner/repo-name/stargazers">
                    <svg class="octicon-star"></svg>
                    1,234
                </a>
                <a href="/owner/repo-name/forks">
                    <svg class="octicon-repo-forked"></svg>
                    567
                </a>
                <span class="d-inline-block float-sm-right">
                    89 stars today
                </span>
                <span>Built by</span>
                <a><img alt="@user1"/></a>
                <a><img alt="@user2"/></a>
            </article>
        </body>
    </html>
    """


@pytest.fixture
def sample_html_with_k_suffix():
    """Sample HTML with k suffix in numbers."""
    return """
    <html>
        <body>
            <article class="Box-row">
                <h2 class="h3">
                    <a href="/owner/popular-repo">owner/popular-repo</a>
                </h2>
                <p class="col-9">Popular repository</p>
                <span itemprop="programmingLanguage">JavaScript</span>
                <a href="/owner/popular-repo/stargazers">
                    <svg class="octicon-star"></svg>
                    12.5k
                </a>
                <a href="/owner/popular-repo/forks">
                    <svg class="octicon-repo-forked"></svg>
                    2.3k
                </a>
                <span class="d-inline-block float-sm-right">
                    1.2k stars today
                </span>
            </article>
        </body>
    </html>
    """


def test_parser_initialization(parser):
    """Test parser initializes correctly."""
    assert parser is not None


def test_parse_empty_html(parser):
    """Test parser raises exception for empty HTML."""
    with pytest.raises(ParserException, match="Empty HTML content"):
        parser.parse_trending_page("")


def test_parse_trending_page(parser, sample_html):
    """Test parsing trending page with valid HTML."""
    projects = parser.parse_trending_page(sample_html)

    assert len(projects) == 1
    project = projects[0]

    assert project["name"] == "owner/repo-name"
    assert project["url"] == "https://github.com/owner/repo-name"
    assert project["description"] == "A sample repository description"
    assert project["language"] == "Python"
    assert project["stars"] == 1234
    assert project["forks"] == 567
    assert project["stars_today"] == 89
    assert "user1" in project["built_by"]
    assert "user2" in project["built_by"]


def test_parse_trending_page_with_k_suffix(parser, sample_html_with_k_suffix):
    """Test parsing numbers with k suffix."""
    projects = parser.parse_trending_page(sample_html_with_k_suffix)

    assert len(projects) == 1
    project = projects[0]

    assert project["stars"] == 12500
    assert project["forks"] == 2300
    assert project["stars_today"] == 1200


def test_parse_number(parser):
    """Test number parsing with various formats."""
    assert parser._parse_number("1,234") == 1234
    assert parser._parse_number("1.2k") == 1200
    assert parser._parse_number("2.5k") == 2500
    assert parser._parse_number("1.5m") == 1500000
    assert parser._parse_number("100") == 100
    assert parser._parse_number("") == 0
    assert parser._parse_number("invalid") == 0


def test_parse_trending_page_no_projects(parser):
    """Test parsing HTML with no project rows."""
    html = "<html><body><div>No projects</div></body></html>"
    projects = parser.parse_trending_page(html)

    assert projects == []


def test_parse_trending_page_multiple_projects(parser):
    """Test parsing multiple projects."""
    html = """
    <html>
        <body>
            <article class="Box-row">
                <h2 class="h3"><a href="/owner1/repo1">owner1/repo1</a></h2>
                <p class="col-9">Description 1</p>
            </article>
            <article class="Box-row">
                <h2 class="h3"><a href="/owner2/repo2">owner2/repo2</a></h2>
                <p class="col-9">Description 2</p>
            </article>
            <article class="Box-row">
                <h2 class="h3"><a href="/owner3/repo3">owner3/repo3</a></h2>
                <p class="col-9">Description 3</p>
            </article>
        </body>
    </html>
    """
    projects = parser.parse_trending_page(html)

    assert len(projects) == 3
    assert projects[0]["name"] == "owner1/repo1"
    assert projects[1]["name"] == "owner2/repo2"
    assert projects[2]["name"] == "owner3/repo3"


def test_validate_project(parser):
    """Test project validation."""
    valid_project = {
        "name": "owner/repo",
        "url": "https://github.com/owner/repo",
        "description": "Test"
    }
    assert parser.validate_project(valid_project) is True

    invalid_project_no_name = {
        "url": "https://github.com/owner/repo"
    }
    assert parser.validate_project(invalid_project_no_name) is False

    invalid_project_empty_name = {
        "name": "",
        "url": "https://github.com/owner/repo"
    }
    assert parser.validate_project(invalid_project_empty_name) is False


def test_parse_project_missing_optional_fields(parser):
    """Test parsing project with missing optional fields."""
    html = """
    <html>
        <body>
            <article class="Box-row">
                <h2 class="h3">
                    <a href="/owner/minimal-repo">owner/minimal-repo</a>
                </h2>
            </article>
        </body>
    </html>
    """
    projects = parser.parse_trending_page(html)

    assert len(projects) == 1
    project = projects[0]

    assert project["name"] == "owner/minimal-repo"
    assert project["url"] == "https://github.com/owner/minimal-repo"
    assert project["description"] == ""
    assert project["language"] == ""
    assert project["stars"] == 0
    assert project["forks"] == 0
    assert project["stars_today"] == 0
    assert project["built_by"] == []
