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

    def save_projects(self, projects: List[Dict[str, Any]], date: str, period: str) -> None:
        """
        Save projects and their trending records to database.

        Args:
            projects: List of project dictionaries
            date: Record date (YYYY-MM-DD)
            period: Period type ('daily', 'weekly', 'monthly')
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            for project in projects:
                # Insert or update project
                cursor.execute("""
                    INSERT INTO projects (repo_full_name, repo_url, first_seen_date, last_updated)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(repo_full_name) DO UPDATE SET
                        last_updated = excluded.last_updated
                """, (
                    project["repo_full_name"],
                    project["repo_url"],
                    date,
                    date
                ))

                # Get project_id
                cursor.execute(
                    "SELECT id FROM projects WHERE repo_full_name = ?",
                    (project["repo_full_name"],)
                )
                project_id = cursor.fetchone()[0]

                # Insert trending record
                cursor.execute("""
                    INSERT INTO trending_records (
                        project_id, record_date, period_type, rank,
                        description, language, total_stars, total_forks, period_stars
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(project_id, record_date, period_type) DO UPDATE SET
                        rank = excluded.rank,
                        description = excluded.description,
                        language = excluded.language,
                        total_stars = excluded.total_stars,
                        total_forks = excluded.total_forks,
                        period_stars = excluded.period_stars
                """, (
                    project_id,
                    date,
                    period,
                    project["rank"],
                    project.get("description", ""),
                    project.get("language", ""),
                    project.get("total_stars", 0),
                    project.get("total_forks", 0),
                    project.get("period_stars", 0)
                ))

            conn.commit()
            logger.info(f"Saved {len(projects)} projects to database")
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Failed to save projects: {e}")
            raise DatabaseException(f"Failed to save projects: {e}")
        finally:
            conn.close()

    def get_previous_ranking(self, date: str, period: str) -> Dict[str, int]:
        """
        Get previous rankings for comparison.

        Args:
            date: Record date (YYYY-MM-DD)
            period: Period type ('daily', 'weekly', 'monthly')

        Returns:
            Dictionary mapping repo_full_name to rank
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT p.repo_full_name, tr.rank
                FROM trending_records tr
                JOIN projects p ON tr.project_id = p.id
                WHERE tr.record_date = ? AND tr.period_type = ?
                ORDER BY tr.rank
            """, (date, period))

            rankings = {row[0]: row[1] for row in cursor.fetchall()}
            conn.close()

            return rankings
        except sqlite3.Error as e:
            logger.error(f"Failed to get previous ranking: {e}")
            raise DatabaseException(f"Failed to get previous ranking: {e}")
