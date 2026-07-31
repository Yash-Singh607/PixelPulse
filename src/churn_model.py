"""
Predictive Churn Risk Scoring Engine for PixelPulse Analytics.
Extracts user behavioral features and computes churn risk probability.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


class ChurnPredictor:
    """Predictive Churn Risk Model calculating user churn risk scores."""

    @staticmethod
    def train_and_predict(db_engine) -> Dict[str, Any]:
        """Queries user event streams, calculates behavioral features, and scores churn probability."""
        sql = """
        SELECT
            u.user_id,
            u.channel,
            u.signup_date,
            COUNT(DISTINCT e.event_name) AS unique_events,
            COUNT(e.event_name) AS total_event_count,
            MAX(CASE WHEN e.event_name = 'onboarding_complete' THEN 1 ELSE 0 END) AS has_onboarded,
            MAX(CASE WHEN e.event_name = 'first_edit' THEN 1 ELSE 0 END) AS has_edited,
            MAX(CASE WHEN e.event_name = 'trial_started' THEN 1 ELSE 0 END) AS has_trialed,
            MAX(CASE WHEN e.event_name = 'subscribed' THEN 1 ELSE 0 END) AS is_subscribed
        FROM users u
        LEFT JOIN events e ON u.user_id = e.user_id
        GROUP BY u.user_id;
        """
        df = db_engine.execute_query(sql)

        if df.empty:
            return {"high_risk_count": 0, "medium_risk_count": 0, "low_risk_count": 0, "avg_churn_risk_pct": 0.0}

        # Calculate heuristic risk score (0 to 100)
        # Base risk = 95
        # -25 for onboarding, -30 for editing, -30 for trial, -1 for each event
        df["risk_score"] = 95.0 - (df["has_onboarded"] * 25.0) - (df["has_edited"] * 30.0) - (df["has_trialed"] * 30.0) - (np.minimum(df["total_event_count"], 10) * 1.0)
        
        # Subscribed users have 0% churn risk
        df.loc[df["is_subscribed"] == 1, "risk_score"] = 0.0
        df["risk_score"] = np.clip(df["risk_score"], 0.0, 100.0)

        # Categorize risk tiers
        high_risk = int((df["risk_score"] >= 70.0).sum())
        medium_risk = int(((df["risk_score"] >= 40.0) & (df["risk_score"] < 70.0)).sum())
        low_risk = int((df["risk_score"] < 40.0).sum())
        avg_risk = float(df["risk_score"].mean())

        # Top at-risk users list
        at_risk_users = (
            df[df["is_subscribed"] == 0]
            .sort_values(by="risk_score", ascending=False)
            .head(10)[["user_id", "channel", "risk_score", "has_onboarded", "has_edited"]]
            .to_dict(orient="records")
        )

        return {
            "high_risk_count": high_risk,
            "medium_risk_count": medium_risk,
            "low_risk_count": low_risk,
            "avg_churn_risk_pct": round(avg_risk, 1),
            "at_risk_users": at_risk_users
        }
