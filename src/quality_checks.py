"""
Data Quality & Integrity Assurance Engine for PixelLoft Data Warehouse.
Performs automated checks on primary key uniqueness, referential integrity, and temporal logic.
"""

import logging
from typing import Dict, List, NamedTuple
from src.database import DatabaseEngine

logger = logging.getLogger(__name__)


class DataQualityResult(NamedTuple):
    check_name: str
    passed: bool
    details: str


class DataQualityChecker:
    """Production Data Quality assurance engine."""

    def __init__(self, db_engine: DatabaseEngine):
        self.db = db_engine

    def run_all_checks(self) -> List[DataQualityResult]:
        """Runs all data quality checks and returns a summary list of results."""
        results = [
            self.check_user_primary_key_uniqueness(),
            self.check_events_referential_integrity(),
            self.check_subscriptions_referential_integrity(),
            self.check_event_temporal_consistency(),
            self.check_non_null_constraints(),
        ]
        return results

    def check_user_primary_key_uniqueness(self) -> DataQualityResult:
        """Check 1: Ensure user_id in users table is unique and non-null."""
        sql = """
        SELECT COUNT(user_id) - COUNT(DISTINCT user_id) AS duplicate_count
        FROM users;
        """
        df = self.db.execute_query(sql)
        duplicates = int(df["duplicate_count"].iloc[0])
        passed = duplicates == 0
        details = "0 duplicate user_ids found." if passed else f"{duplicates} duplicate user_ids detected!"
        return DataQualityResult("User Primary Key Uniqueness", passed, details)

    def check_events_referential_integrity(self) -> DataQualityResult:
        """Check 2: Ensure all user_ids in events exist in users table."""
        sql = """
        SELECT COUNT(e.user_id) AS orphan_count
        FROM events e
        LEFT JOIN users u ON e.user_id = u.user_id
        WHERE u.user_id IS NULL;
        """
        df = self.db.execute_query(sql)
        orphans = int(df["orphan_count"].iloc[0])
        passed = orphans == 0
        details = "0 orphan event records." if passed else f"{orphans} orphan event records found!"
        return DataQualityResult("Events Foreign Key Integrity", passed, details)

    def check_subscriptions_referential_integrity(self) -> DataQualityResult:
        """Check 3: Ensure all user_ids in subscriptions exist in users table."""
        sql = """
        SELECT COUNT(s.user_id) AS orphan_count
        FROM subscriptions s
        LEFT JOIN users u ON s.user_id = u.user_id
        WHERE u.user_id IS NULL;
        """
        df = self.db.execute_query(sql)
        orphans = int(df["orphan_count"].iloc[0])
        passed = orphans == 0
        details = "0 orphan subscription records." if passed else f"{orphans} orphan subscription records found!"
        return DataQualityResult("Subscriptions Foreign Key Integrity", passed, details)

    def check_event_temporal_consistency(self) -> DataQualityResult:
        """Check 4: Ensure signup_date <= event_date for all events."""
        sql = """
        SELECT COUNT(*) AS invalid_date_count
        FROM events e
        JOIN users u ON e.user_id = u.user_id
        WHERE e.event_date < u.signup_date;
        """
        df = self.db.execute_query(sql)
        invalids = int(df["invalid_date_count"].iloc[0])
        passed = invalids == 0
        details = "All events occur after or on signup date." if passed else f"{invalids} events precede signup date!"
        return DataQualityResult("Event Temporal Consistency", passed, details)

    def check_non_null_constraints(self) -> DataQualityResult:
        """Check 5: Ensure mandatory fields contain 0 null values."""
        sql = """
        SELECT 
            (SELECT COUNT(*) FROM users WHERE user_id IS NULL OR signup_date IS NULL OR channel IS NULL) +
            (SELECT COUNT(*) FROM events WHERE user_id IS NULL OR event_name IS NULL OR event_date IS NULL) +
            (SELECT COUNT(*) FROM subscriptions WHERE user_id IS NULL OR price_usd IS NULL) AS null_count;
        """
        df = self.db.execute_query(sql)
        null_count = int(df["null_count"].iloc[0])
        passed = null_count == 0
        details = "0 null values in mandatory fields." if passed else f"{null_count} null values in mandatory fields!"
        return DataQualityResult("Mandatory Fields Non-Null Constraint", passed, details)
