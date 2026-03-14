"""Database operations for the GitHub Trending scraper."""

import sqlite3
from datetime import date, datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
from loguru import logger
from src.exceptions import DatabaseException


class Database:
    """SQLite database manager for trending data."""

    def __init__(self, db_path: str):
        """
        Initialize database connection and create tables if needed.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Create parent directory if it doesn't exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        logger.info(f"Database initialized at {db_path}")

    def _init_database(self) -> None:
        """Create tables and indexes if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Create projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_full_name TEXT UNIQUE NOT NULL,
                    repo_url TEXT NOT NULL,
                    first_seen_date DATE NOT NULL,
                    last_updated DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create trending_records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trending_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    record_date DATE NOT NULL,
                    period_type TEXT NOT NULL,
                    rank INTEGER NOT NULL,
                    description TEXT,
                    language TEXT,
                    total_stars INTEGER,
                    total_forks INTEGER,
                    period_stars INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    UNIQUE(project_id, record_date, period_type)
                )
            """)

            # Create daily_reports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_date DATE UNIQUE NOT NULL,
                    oss_url TEXT,
                    dingtalk_sent BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trending_date
                ON trending_records(record_date)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trending_project
                ON trending_records(project_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_projects_name
                ON projects(repo_full_name)
            """)

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseException(f"Failed to initialize database: {e}")
        finally:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self.db_path)
