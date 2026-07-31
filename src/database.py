"""
Database Engine Manager for PixelLoft SQLite Data Warehouse.
Manages connections, schema initialization, performance indexing, and pandas query execution.
"""

import logging
import sqlite3
import time
from pathlib import Path
from typing import Dict, Optional, Union
import pandas as pd

from config import DB_PATH

logger = logging.getLogger(__name__)


class DatabaseEngine:
    """Production database engine manager for SQLite analytics database."""

    def __init__(self, db_path: Union[str, Path] = DB_PATH):
        self.db_path = Path(db_path)

    def get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite database connection with WAL mode enabled."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def create_indexes(self) -> None:
        """Creates database performance indexes for analytical query acceleration."""
        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_users_signup ON users(signup_date);",
            "CREATE INDEX IF NOT EXISTS idx_users_channel ON users(channel);",
            "CREATE INDEX IF NOT EXISTS idx_users_experiment ON users(experiment_group);",
            "CREATE INDEX IF NOT EXISTS idx_events_user_event ON events(user_id, event_name);",
            "CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);",
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);",
        ]
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for query in index_queries:
                cursor.execute(query)
            conn.commit()
        logger.info("Performance indexes created successfully.")

    def execute_query(self, query_sql: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """Executes a SQL query and returns the result set as a pandas DataFrame."""
        start_time = time.perf_counter()
        with self.get_connection() as conn:
            df = pd.read_sql(query_sql, conn, params=params)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.debug(f"Executed query in {elapsed_ms:.2f} ms ({len(df)} rows returned).")
        return df

    def verify_tables(self) -> Dict[str, int]:
        """Returns row counts for all target tables in the database."""
        tables = ["users", "events", "subscriptions"]
        counts = {}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for t in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {t};")
                counts[t] = cursor.fetchone()[0]
        return counts
