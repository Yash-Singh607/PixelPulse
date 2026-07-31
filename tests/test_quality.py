"""
Unit & Integration tests for Data Quality and Data Integrity Checks.
"""

from src.database import DatabaseEngine
from src.quality_checks import DataQualityChecker
from config import DB_PATH


def test_user_primary_key_uniqueness():
    db = DatabaseEngine(db_path=DB_PATH)
    checker = DataQualityChecker(db)
    res = checker.check_user_primary_key_uniqueness()
    assert res.passed is True, f"Failed: {res.details}"


def test_events_referential_integrity():
    db = DatabaseEngine(db_path=DB_PATH)
    checker = DataQualityChecker(db)
    res = checker.check_events_referential_integrity()
    assert res.passed is True, f"Failed: {res.details}"


def test_subscriptions_referential_integrity():
    db = DatabaseEngine(db_path=DB_PATH)
    checker = DataQualityChecker(db)
    res = checker.check_subscriptions_referential_integrity()
    assert res.passed is True, f"Failed: {res.details}"


def test_event_temporal_consistency():
    db = DatabaseEngine(db_path=DB_PATH)
    checker = DataQualityChecker(db)
    res = checker.check_event_temporal_consistency()
    assert res.passed is True, f"Failed: {res.details}"


def test_non_null_constraints():
    db = DatabaseEngine(db_path=DB_PATH)
    checker = DataQualityChecker(db)
    res = checker.check_non_null_constraints()
    assert res.passed is True, f"Failed: {res.details}"
