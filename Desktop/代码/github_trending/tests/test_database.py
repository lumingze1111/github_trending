# tests/test_database.py
import pytest
import sqlite3
from datetime import date
from src.database import Database
from src.exceptions import DatabaseException


@pytest.fixture
def db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    database = Database(str(db_path))
    yield database
    # Cleanup happens automatically with tmp_path


def test_database_init_creates_tables(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    # Check tables exist
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]

    assert "projects" in tables
    assert "trending_records" in tables
    assert "daily_reports" in tables

    conn.close()


def test_database_init_creates_indexes(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
    )
    indexes = [row[0] for row in cursor.fetchall()]

    assert "idx_trending_date" in indexes
    assert "idx_trending_project" in indexes
    assert "idx_projects_name" in indexes

    conn.close()


def test_save_projects_inserts_new_projects_and_records(db):
    """Test saving new projects with trending records."""
    projects = [
        {
            "repo_full_name": "test/repo1",
            "repo_url": "https://github.com/test/repo1",
            "description": "Test repo 1",
            "language": "Python",
            "total_stars": 100,
            "total_forks": 20,
            "period_stars": 10,
            "rank": 1,
        }
    ]

    db.save_projects(projects, date="2026-03-13", period="daily")

    # Check projects table
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE repo_full_name = ?", ("test/repo1",))
    project_result = cursor.fetchone()

    assert project_result is not None
    assert project_result[1] == "test/repo1"  # repo_full_name
    assert project_result[2] == "https://github.com/test/repo1"  # repo_url
    assert project_result[3] == "2026-03-13"  # first_seen_date
    assert project_result[4] == "2026-03-13"  # last_updated

    # Check trending_records table
    project_id = project_result[0]
    cursor.execute("""
        SELECT * FROM trending_records
        WHERE project_id = ? AND record_date = ? AND period_type = ?
    """, (project_id, "2026-03-13", "daily"))
    record_result = cursor.fetchone()
    conn.close()

    assert record_result is not None
    assert record_result[2] == "2026-03-13"  # record_date
    assert record_result[3] == "daily"  # period_type
    assert record_result[4] == 1  # rank
    assert record_result[5] == "Test repo 1"  # description
    assert record_result[6] == "Python"  # language
    assert record_result[7] == 100  # total_stars
    assert record_result[8] == 20  # total_forks
    assert record_result[9] == 10  # period_stars


def test_save_projects_updates_existing(db):
    """Test updating existing projects."""
    # Insert initial project
    projects_v1 = [
        {
            "repo_full_name": "test/repo1",
            "repo_url": "https://github.com/test/repo1",
            "description": "Old description",
            "language": "Python",
            "total_stars": 100,
            "total_forks": 20,
            "period_stars": 10,
            "rank": 1,
        }
    ]
    db.save_projects(projects_v1, date="2026-03-13", period="daily")

    # Update with new data
    projects_v2 = [
        {
            "repo_full_name": "test/repo1",
            "repo_url": "https://github.com/test/repo1",
            "description": "New description",
            "language": "Python",
            "total_stars": 150,
            "total_forks": 25,
            "period_stars": 50,
            "rank": 1,
        }
    ]
    db.save_projects(projects_v2, date="2026-03-14", period="daily")

    conn = db._get_connection()
    cursor = conn.cursor()

    # Check project was updated
    cursor.execute("SELECT * FROM projects WHERE repo_full_name = ?", ("test/repo1",))
    result = cursor.fetchone()
    assert result[4] == "2026-03-14"  # last_updated should be new date

    # Check we have two trending records
    project_id = result[0]
    cursor.execute("SELECT COUNT(*) FROM trending_records WHERE project_id = ?", (project_id,))
    count = cursor.fetchone()[0]
    assert count == 2  # Should have records for both dates

    conn.close()
