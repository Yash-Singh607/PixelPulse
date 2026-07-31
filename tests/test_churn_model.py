"""
Unit test suite for Predictive Churn Risk Scoring Engine.
"""

from src.database import DatabaseEngine
from src.churn_model import ChurnPredictor
from config import DB_PATH


def test_churn_prediction_execution():
    """Verify predictive churn scoring generates valid risk metrics."""
    db = DatabaseEngine(db_path=DB_PATH)
    result = ChurnPredictor.train_and_predict(db)

    assert "high_risk_count" in result
    assert "avg_churn_risk_pct" in result
    assert result["high_risk_count"] >= 0
    assert 0.0 <= result["avg_churn_risk_pct"] <= 100.0
    assert len(result["at_risk_users"]) <= 10
