"""
Production Chart Visualization Engine for PixelLoft Product Analytics.
Generates publication-quality charts for funnels, retention, A/B experiments, and revenue.
"""

from pathlib import Path
from typing import Union
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from config import (
    ACCENT_COLOR,
    CHART_AB_TEST_PATH,
    CHART_FUNNEL_PATH,
    CHART_RETENTION_PATH,
    CHART_REVENUE_PATH,
    DPI,
    NEUTRAL_COLOR,
    PRIMARY_COLOR,
    SECONDARY_COLOR,
    STYLE_THEME,
)


class ChartVisualizer:
    """Production visualization engine producing clean, high-DPI charts."""

    def __init__(self):
        try:
            plt.style.use(STYLE_THEME)
        except Exception:
            plt.style.use("default")

    def generate_funnel_chart(
        self, funnel_df: pd.DataFrame, output_path: Union[str, Path] = CHART_FUNNEL_PATH
    ) -> None:
        """Chart 1: Funnel conversion by channel."""
        fig, ax = plt.subplots(figsize=(9, 5))
        x = funnel_df["channel"].str.replace("_", " ").str.title()
        
        ax.bar(x, funnel_df["pct_onboarded"], label="Signup -> Onboarded", color=PRIMARY_COLOR, alpha=0.85)
        ax.bar(x, funnel_df["overall_conversion_pct"], label="Signup -> Subscribed", color=SECONDARY_COLOR, alpha=0.90)
        
        ax.set_ylabel("% of signups", fontsize=11, fontweight="bold")
        ax.set_title("Onboarding Rate vs. Overall Paid Conversion by Channel", fontsize=13, fontweight="bold", pad=12)
        ax.legend(frameon=True, facecolor="white", edgecolor="none")
        plt.xticks(rotation=15, ha="right", fontsize=10)
        plt.tight_layout()
        plt.savefig(output_path, dpi=DPI)
        plt.close(fig)

    def generate_retention_chart(
        self, cohort_df: pd.DataFrame, output_path: Union[str, Path] = CHART_RETENTION_PATH
    ) -> None:
        """Chart 2: Cohort retention curve."""
        avg_retention = cohort_df.groupby("month_number")["retention_pct"].mean()
        fig, ax = plt.subplots(figsize=(7, 5))
        
        ax.plot(
            avg_retention.index,
            avg_retention.values,
            marker="o",
            color=PRIMARY_COLOR,
            linewidth=2.5,
            markersize=8,
            label="Average Cohort Retention",
        )
        for x_val, y_val in zip(avg_retention.index, avg_retention.values):
            ax.annotate(
                f"{y_val:.1f}%",
                (x_val, y_val),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
                fontsize=9,
                fontweight="bold",
            )
            
        ax.set_xlabel("Months Since Signup", fontsize=11, fontweight="bold")
        ax.set_ylabel("Average % Active Users", fontsize=11, fontweight="bold")
        ax.set_title("Average User Retention Curve Across 2025 Cohorts", fontsize=13, fontweight="bold", pad=12)
        ax.set_ylim(0, 100)
        plt.tight_layout()
        plt.savefig(output_path, dpi=DPI)
        plt.close(fig)

    def generate_ab_test_chart(
        self,
        p_control: float,
        p_treatment: float,
        p_value: float,
        output_path: Union[str, Path] = CHART_AB_TEST_PATH,
    ) -> None:
        """Chart 3: A/B Test onboarding activation comparison bar chart."""
        fig, ax = plt.subplots(figsize=(6, 5))
        groups = ["Control\n(Self-Serve)", "Treatment\n(Guided Edit)"]
        rates = [p_control * 100, p_treatment * 100]
        
        bars = ax.bar(groups, rates, color=[NEUTRAL_COLOR, SECONDARY_COLOR], width=0.55)
        ax.set_ylabel("Onboarding Activation Rate (%)", fontsize=11, fontweight="bold")
        abs_lift = rates[1] - rates[0]
        ax.set_title(
            f"A/B Test: Guided Edit Onboarding Activation\n(+{abs_lift:.2f}pp Lift, p={p_value:.4f})",
            fontsize=12,
            fontweight="bold",
            pad=12,
        )
        ax.set_ylim(0, max(rates) * 1.2)
        for b, r in zip(bars, rates):
            ax.text(b.get_x() + b.get_width() / 2, r + 1.5, f"{r:.2f}%", ha="center", fontsize=10, fontweight="bold")
            
        plt.tight_layout()
        plt.savefig(output_path, dpi=DPI)
        plt.close(fig)

    def generate_revenue_chart(
        self, rev_df: pd.DataFrame, output_path: Union[str, Path] = CHART_REVENUE_PATH
    ) -> None:
        """Chart 4: Revenue per signup by channel."""
        fig, ax = plt.subplots(figsize=(9, 5))
        rev_sorted = rev_df.sort_values("revenue_per_signup_usd", ascending=False).copy()
        rev_sorted["channel_name"] = rev_sorted["channel"].str.replace("_", " ").str.title()
        
        bars = ax.bar(rev_sorted["channel_name"], rev_sorted["revenue_per_signup_usd"], color=PRIMARY_COLOR)
        ax.set_ylabel("Revenue per Signup (USD)", fontsize=11, fontweight="bold")
        ax.set_title("Revenue per Signup by Acquisition Channel", fontsize=13, fontweight="bold", pad=12)
        
        for b, val in zip(bars, rev_sorted["revenue_per_signup_usd"]):
            ax.text(b.get_x() + b.get_width() / 2, val + 0.15, f"${val:.2f}", ha="center", fontsize=9, fontweight="bold")
            
        plt.xticks(rotation=15, ha="right", fontsize=10)
        plt.tight_layout()
        plt.savefig(output_path, dpi=DPI)
        plt.close(fig)
