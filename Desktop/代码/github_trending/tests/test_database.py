# tests/test_database.py
import pytest
import sqlite3
from datetime import date
from src.database import Database
from src.exceptions import DatabaseException


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
