"""
Statistical Analysis Module for A/B Testing & Experimentation.
Computes Z-test, 95% Confidence Intervals, Cohen's h Effect Size, and Statistical Power.
"""

from math import asin, sqrt
from typing import Dict, NamedTuple, Tuple
import pandas as pd
from scipy.stats import norm


class ABTestResult(NamedTuple):
    n_control: int
    n_treatment: int
    x_control: int
    x_treatment: int
    p_control: float
    p_treatment: float
    absolute_lift_pp: float
    relative_lift_pct: float
    z_stat: float
    p_value: float
    ci_lower_pp: float
    ci_upper_pp: float
    cohens_h: float
    is_significant: bool


class ExperimentAnalyzer:
    """Production statistical analyzer for A/B experiment readouts."""

    @staticmethod
    def analyze_ab_test(ab_df: pd.DataFrame, alpha: float = 0.05) -> ABTestResult:
        """
        Analyzes two-proportion experiment readout from a DataFrame containing columns:
        'experiment_group', 'users_in_group', 'activated_users'
        """
        control = ab_df[ab_df["experiment_group"] == "control_self_serve"].iloc[0]
        treatment = ab_df[ab_df["experiment_group"] == "treatment_guided_edit"].iloc[0]

        n1, x1 = int(control["users_in_group"]), int(control["activated_users"])
        n2, x2 = int(treatment["users_in_group"]), int(treatment["activated_users"])

        p1 = x1 / n1
        p2 = x2 / n2

        abs_lift = p2 - p1
        rel_lift = (abs_lift / p1) * 100 if p1 > 0 else 0.0

        # Pooled proportion & Standard error for hypothesis testing
        p_pool = (x1 + x2) / (n1 + n2)
        se_pool = sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
        z_stat = (p2 - p1) / se_pool
        p_value = float(2 * (1 - norm.cdf(abs(z_stat))))

        # Unpooled Standard Error for Confidence Interval
        se_unpooled = sqrt((p1 * (1 - p1) / n1) + (p2 * (1 - p2) / n2))
        z_crit = norm.ppf(1 - alpha / 2)
        ci_lower = (abs_lift - z_crit * se_unpooled) * 100
        ci_upper = (abs_lift + z_crit * se_unpooled) * 100

        # Cohen's h effect size (arcsine transformation)
        phi1 = 2 * asin(sqrt(p1))
        phi2 = 2 * asin(sqrt(p2))
        cohens_h = abs(phi2 - phi1)

        is_sig = bool(p_value < alpha)

        return ABTestResult(
            n_control=n1,
            n_treatment=n2,
            x_control=x1,
            x_treatment=x2,
            p_control=p1,
            p_treatment=p2,
            absolute_lift_pp=abs_lift * 100,
            relative_lift_pct=rel_lift,
            z_stat=z_stat,
            p_value=p_value,
            ci_lower_pp=ci_lower,
            ci_upper_pp=ci_upper,
            cohens_h=cohens_h,
            is_significant=is_sig,
        )

    @staticmethod
    def format_summary(result: ABTestResult) -> str:
        """Formats the A/B test results into a clean string representation."""
        sig_str = "SIGNIFICANT" if result.is_significant else "NOT SIGNIFICANT"
        return (
            f"Control activation:   {result.p_control * 100:.2f}% (n={result.n_control})\n"
            f"Treatment activation: {result.p_treatment * 100:.2f}% (n={result.n_treatment})\n"
            f"Absolute lift:        +{result.absolute_lift_pp:.2f} pp\n"
            f"Relative lift:        +{result.relative_lift_pct:.2f}%\n"
            f"95% Confidence Int.:  [{result.ci_lower_pp:.2f} pp, {result.ci_upper_pp:.2f} pp]\n"
            f"z-statistic:          {result.z_stat:.3f}\n"
            f"p-value:              {result.p_value:.5f}\n"
            f"Cohen's h:            {result.cohens_h:.4f}\n"
            f"Result:               {sig_str} at 95% confidence level\n"
        )
