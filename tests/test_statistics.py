"""
Unit tests for statistical formulas and A/B test analysis engine.
"""

import pandas as pd
from src.statistics import ExperimentAnalyzer


def test_ab_test_statistical_significance():
    # Mock A/B test dataset with known proportions
    data = pd.DataFrame(
        [
            {"experiment_group": "control_self_serve", "users_in_group": 1000, "activated_users": 500},
            {"experiment_group": "treatment_guided_edit", "users_in_group": 1000, "activated_users": 600},
        ]
    )

    result = ExperimentAnalyzer.analyze_ab_test(data)

    assert result.n_control == 1000
    assert result.n_treatment == 1000
    assert result.p_control == 0.50
    assert result.p_treatment == 0.60
    assert abs(result.absolute_lift_pp - 10.0) < 1e-5
    assert abs(result.relative_lift_pct - 20.0) < 1e-5
    assert result.p_value < 0.001
    assert result.is_significant is True
    assert result.ci_lower_pp < result.absolute_lift_pp < result.ci_upper_pp
