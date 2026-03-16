"""Tests for report generator."""

import pytest
from pathlib import Path
from src.report_generator import ReportGenerator
from src.exceptions import TemplateException


@pytest.fixture
def temp_template_dir(tmp_path):
    """Create temporary template directory with test template."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()

    # Create a simple test template
    template_content = """
<!DOCTYPE html>
<html>
<head><title>Test Report - {{ date }}</title></head>
<body>
    <h1>GitHub Trending - {{ date }}</h1>
    {% for project in daily_projects %}
    <div class="project">
        <h2>{{ project.name }}</h2>
        <p>{{ project.description }}</p>
        <p>Stars: {{ project.stars }}</p>
    </div>
    {% endfor %}
</body>
</html>
    """
    (template_dir / "report.html").write_text(template_content)
    return template_dir


@pytest.fixture
def sample_projects():
    """Sample projects for testing."""
    return [
        {
            "name": "owner/repo1",
            "url": "https://github.com/owner/repo1",
            "description": "Test repo 1",
            "language": "Python",
            "stars": 1000,
            "forks": 100,
            "stars_today": 50,
            "ranking": 1,
            "highlights": ["🏆 #1 in daily trending"],
        },
        {
            "name": "owner/repo2",
            "url": "https://github.com/owner/repo2",
            "description": "Test repo 2",
            "language": "JavaScript",
            "stars": 500,
            "forks": 50,
            "stars_today": 25,
            "ranking": 2,
            "highlights": ["🥇 Top 3 in daily trending"],
        },
    ]


def test_report_generator_initialization(temp_template_dir):
    """Test report generator initializes correctly."""
    generator = ReportGenerator(str(temp_template_dir))
    assert generator.template_dir == temp_template_dir
    assert generator.env is not None


def test_report_generator_invalid_template_dir():
    """Test report generator raises exception for invalid template directory."""
    with pytest.raises(TemplateException, match="Template directory not found"):
        ReportGenerator("/nonexistent/directory")


def test_generate_report(temp_template_dir, sample_projects, tmp_path):
    """Test generating HTML report."""
    generator = ReportGenerator(str(temp_template_dir))
    output_path = tmp_path / "output" / "report.html"

    result = generator.generate_report(
        output_path=str(output_path),
        date="2024-03-14",
        daily_projects=sample_projects,
    )

    assert result == str(output_path)
    assert output_path.exists()

    # Check content
    content = output_path.read_text()
    assert "GitHub Trending - 2024-03-14" in content
    assert "owner/repo1" in content
    assert "Test repo 1" in content
    assert "1000" in content


def test_generate_report_creates_parent_directory(temp_template_dir, sample_projects, tmp_path):
    """Test that generate_report creates parent directories if they don't exist."""
    generator = ReportGenerator(str(temp_template_dir))
    output_path = tmp_path / "nested" / "dir" / "report.html"

    generator.generate_report(
        output_path=str(output_path),
        date="2024-03-14",
        daily_projects=sample_projects,
    )

    assert output_path.exists()
    assert output_path.parent.exists()


def test_generate_report_with_all_time_ranges(temp_template_dir, sample_projects, tmp_path):
    """Test generating report with all three time ranges."""
    generator = ReportGenerator(str(temp_template_dir))
    output_path = tmp_path / "report.html"

    result = generator.generate_report(
        output_path=str(output_path),
        date="2024-03-14",
        daily_projects=sample_projects,
        weekly_projects=sample_projects[:1],
        monthly_projects=sample_projects[:1],
    )

    assert result == str(output_path)
    assert output_path.exists()


def test_generate_report_with_summaries(temp_template_dir, sample_projects, tmp_path):
    """Test generating report with summary statistics."""
    generator = ReportGenerator(str(temp_template_dir))
    output_path = tmp_path / "report.html"

    daily_summary = {
        "total_projects": 2,
        "total_stars_today": 75,
        "avg_stars_today": 37,
    }

    result = generator.generate_report(
        output_path=str(output_path),
        date="2024-03-14",
        daily_projects=sample_projects,
        daily_summary=daily_summary,
    )

    assert result == str(output_path)
    assert output_path.exists()


def test_generate_report_empty_projects(temp_template_dir, tmp_path):
    """Test generating report with empty project list."""
    generator = ReportGenerator(str(temp_template_dir))
    output_path = tmp_path / "report.html"

    result = generator.generate_report(
        output_path=str(output_path),
        date="2024-03-14",
        daily_projects=[],
    )

    assert result == str(output_path)
    assert output_path.exists()


def test_generate_report_template_not_found(tmp_path):
    """Test error when template file doesn't exist."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()

    generator = ReportGenerator(str(template_dir))

    with pytest.raises(TemplateException, match="Template file 'report.html' not found"):
        generator.generate_report(
            output_path=str(tmp_path / "report.html"),
            date="2024-03-14",
            daily_projects=[],
        )


def test_generate_simple_report(sample_projects, tmp_path):
    """Test generating simple text-based report."""
    # Use default template dir (will fail for HTML, but simple report should work)
    generator = ReportGenerator("templates")
    output_path = tmp_path / "simple_report.txt"

    result = generator.generate_simple_report(
        output_path=str(output_path),
        date="2024-03-14",
        projects=sample_projects,
    )

    assert result == str(output_path)
    assert output_path.exists()

    # Check content
    content = output_path.read_text()
    assert "GitHub Trending Report - 2024-03-14" in content
    assert "owner/repo1" in content
    assert "Test repo 1" in content
    assert "Python" in content
    assert "1,000" in content


def test_generate_simple_report_creates_parent_directory(sample_projects, tmp_path):
    """Test that simple report creates parent directories."""
    generator = ReportGenerator("templates")
    output_path = tmp_path / "nested" / "simple_report.txt"

    generator.generate_simple_report(
        output_path=str(output_path),
        date="2024-03-14",
        projects=sample_projects,
    )

    assert output_path.exists()
    assert output_path.parent.exists()


def test_generate_simple_report_empty_projects(tmp_path):
    """Test generating simple report with empty project list."""
    generator = ReportGenerator("templates")
    output_path = tmp_path / "simple_report.txt"

    result = generator.generate_simple_report(
        output_path=str(output_path),
        date="2024-03-14",
        projects=[],
    )

    assert result == str(output_path)
    assert output_path.exists()

    content = output_path.read_text()
    assert "GitHub Trending Report - 2024-03-14" in content
