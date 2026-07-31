"""
Unit tests for DatabaseEngine and SQL connection handling.
"""

import sqlite3
import pytest
import pandas as pd
from src.database import DatabaseEngine
from config import DB_PATH


def test_database_connection(tmp_path):
    db_file = tmp_path / "test.db"
    engine = DatabaseEngine(db_path=db_file)
    conn = engine.get_connection()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()


def test_database_table_verification():
    engine = DatabaseEngine(db_path=DB_PATH)
    counts = engine.verify_tables()
    assert "users" in counts
    assert "events" in counts
    assert "subscriptions" in counts
    assert counts["users"] > 0
    assert counts["events"] > 0


def test_database_query_execution():
    engine = DatabaseEngine(db_path=DB_PATH)
    df = engine.execute_query("SELECT COUNT(*) AS total_users FROM users;")
    assert isinstance(df, pd.DataFrame)
    assert "total_users" in df.columns
    assert df["total_users"].iloc[0] > 0
