"""
Centralized Configuration Settings for PixelLoft Product Analytics Pipeline.
"""

from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR
SQL_DIR = BASE_DIR
OUTPUT_DIR = BASE_DIR

# Database configuration
DB_NAME = "pixelloft.db"
DB_PATH = DATA_DIR / DB_NAME
SQL_FILE_PATH = SQL_DIR / "analysis_queries.sql"

# Data Generation Parameters
RANDOM_SEED = 42
DEFAULT_N_USERS = 6000
START_DATE_STR = "2025-01-01"
END_DATE_STR = "2025-12-31"

# Output artifact paths
CSV_FUNNEL_PATH = OUTPUT_DIR / "output_funnel.csv"
CSV_COHORT_PATH = OUTPUT_DIR / "output_cohort.csv"
CSV_REVENUE_PATH = OUTPUT_DIR / "output_revenue.csv"
AB_TEST_RESULT_PATH = OUTPUT_DIR / "ab_test_result.txt"

CHART_FUNNEL_PATH = OUTPUT_DIR / "chart_funnel_by_channel.png"
CHART_RETENTION_PATH = OUTPUT_DIR / "chart_retention_curve.png"
CHART_AB_TEST_PATH = OUTPUT_DIR / "chart_ab_test.png"
CHART_REVENUE_PATH = OUTPUT_DIR / "chart_revenue_per_signup.png"

# Visualization Styling
STYLE_THEME = "seaborn-v0_8-whitegrid"
PRIMARY_COLOR = "#1565c0"
SECONDARY_COLOR = "#2e7d32"
NEUTRAL_COLOR = "#757575"
ACCENT_COLOR = "#e65100"
DPI = 150
