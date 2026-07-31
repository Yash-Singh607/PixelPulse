"""
Unified Command Line Interface & Backend API Server for PixelPulse Product Analytics Data Pipeline & Dashboard.
"""

import argparse
import json
import http.server
import socketserver
import sys
import time
import webbrowser
from pathlib import Path
import pytest

from config import (
    AB_TEST_RESULT_PATH,
    CSV_COHORT_PATH,
    CSV_FUNNEL_PATH,
    CSV_REVENUE_PATH,
    DB_PATH,
    BASE_DIR,
)
from src.database import DatabaseEngine
from src.data_generator import generate_pixel_loft_data
from src.quality_checks import DataQualityChecker
from src.sql_parser import SQLParser
from src.statistics import ExperimentAnalyzer
from src.visualization import ChartVisualizer
from src.churn_model import ChurnPredictor


DATA_JSON_PATH = BASE_DIR / "data.json"


def cmd_generate(args):
    """Generates synthetic dataset and populates SQLite database."""
    print("Generating synthetic PixelPulse dataset...")
    users, events, subs = generate_pixel_loft_data(
        n_users=getattr(args, "n_users", 6000),
        random_seed=getattr(args, "seed", 42),
        db_path=DB_PATH,
    )
    print(f"Dataset generated successfully! ({len(users)} users, {len(events)} events, {len(subs)} subscriptions)")


def cmd_analyze(args):
    """Executes SQL analysis pipeline, ML churn scoring, CSV exports, chart rendering, and data.json output."""
    print("Running PixelPulse SQL analysis pipeline...")
    db = DatabaseEngine(db_path=DB_PATH)
    parser = SQLParser()
    queries = parser.load_queries()

    # 1. Execute SQL queries
    funnel_df = db.execute_query(queries["funnel"])
    cohort_df = db.execute_query(queries["cohort"])
    ab_df = db.execute_query(queries["ab_test"])
    rev_df = db.execute_query(queries["revenue"])

    # 2. Export CSV artifacts
    funnel_df.to_csv(CSV_FUNNEL_PATH, index=False)
    cohort_df.to_csv(CSV_COHORT_PATH, index=False)
    rev_df.to_csv(CSV_REVENUE_PATH, index=False)

    # 3. Statistical Analysis
    ab_result = ExperimentAnalyzer.analyze_ab_test(ab_df)
    ab_summary = ExperimentAnalyzer.format_summary(ab_result)
    AB_TEST_RESULT_PATH.write_text(ab_summary, encoding="utf-8")

    # 4. Data Quality Integrity Checks
    checker = DataQualityChecker(db)
    dq_results = [
        {"check_name": r.check_name, "passed": r.passed, "details": r.details}
        for r in checker.run_all_checks()
    ]

    # 5. ML Predictive Churn Scoring
    churn_metrics = ChurnPredictor.train_and_predict(db)

    # 6. Export JSON for Web Dashboard UI
    total_signups = int(funnel_df["signups"].sum())
    total_revenue = float(rev_df["total_revenue_usd"].sum())
    total_paid = int(funnel_df["subscribed"].sum())
    overall_conv = round((total_paid / total_signups * 100), 2) if total_signups > 0 else 0.0

    dashboard_data = {
        "project_name": "PixelPulse",
        "summary": {
            "total_signups": total_signups,
            "total_revenue": total_revenue,
            "total_paying_users": total_paid,
            "overall_conversion_pct": overall_conv,
            "ab_lift_pp": round(ab_result.absolute_lift_pp, 2),
            "ab_p_value": round(ab_result.p_value, 5),
            "ab_is_significant": ab_result.is_significant,
            "dq_all_passed": all(r["passed"] for r in dq_results),
            "avg_churn_risk_pct": churn_metrics["avg_churn_risk_pct"],
            "high_churn_users_count": churn_metrics["high_risk_count"]
        },
        "funnel": funnel_df.to_dict(orient="records"),
        "cohort": cohort_df.to_dict(orient="records"),
        "ab_test": {
            "groups": ab_df.to_dict(orient="records"),
            "result": {
                "n_control": ab_result.n_control,
                "n_treatment": ab_result.n_treatment,
                "p_control": round(ab_result.p_control * 100, 2),
                "p_treatment": round(ab_result.p_treatment * 100, 2),
                "abs_lift_pp": round(ab_result.absolute_lift_pp, 2),
                "rel_lift_pct": round(ab_result.relative_lift_pct, 2),
                "ci_lower_pp": round(ab_result.ci_lower_pp, 2),
                "ci_upper_pp": round(ab_result.ci_upper_pp, 2),
                "z_stat": round(ab_result.z_stat, 3),
                "p_value": round(ab_result.p_value, 5),
                "cohens_h": round(ab_result.cohens_h, 4),
                "is_significant": ab_result.is_significant,
            },
        },
        "revenue": rev_df.to_dict(orient="records"),
        "queries": queries,
        "data_quality": dq_results,
        "churn": churn_metrics,
    }

    DATA_JSON_PATH.write_text(json.dumps(dashboard_data, indent=2), encoding="utf-8")

    # 7. Generate Visualizations
    viz = ChartVisualizer()
    viz.generate_funnel_chart(funnel_df)
    viz.generate_retention_chart(cohort_df)
    viz.generate_ab_test_chart(ab_result.p_control, ab_result.p_treatment, ab_result.p_value)
    viz.generate_revenue_chart(rev_df)

    print("\n" + "=" * 50)
    print("PIXELPULSE ANALYSIS & DASHBOARD DATA UPDATED")
    print("=" * 50)
    print(f"Total Signups: {total_signups:,}")
    print(f"Total Revenue: ${total_revenue:,.2f}")
    print(f"A/B Lift: +{ab_result.absolute_lift_pp:.2f} pp (p = {ab_result.p_value:.5f})")
    print(f"ML Avg Churn Risk: {churn_metrics['avg_churn_risk_pct']}% ({churn_metrics['high_risk_count']} High Risk)")
    print(f"data.json exported to {DATA_JSON_PATH}")
    print("=" * 50)


def cmd_test(args):
    """Runs data quality integrity checks and pytest suite."""
    print("Running Data Quality Integrity Checks...")
    db = DatabaseEngine(db_path=DB_PATH)
    checker = DataQualityChecker(db)
    results = checker.run_all_checks()

    all_passed = True
    for r in results:
        status = "PASSED" if r.passed else "FAILED"
        print(f" [{status}] {r.check_name}: {r.details}")
        if not r.passed:
            all_passed = False

    print("\nRunning PyTest automated test suite...")
    pytest_code = pytest.main(["-v", "tests"])

    if not all_passed or pytest_code != 0:
        print("\nTest suite FAILED.")
        sys.exit(1)
    else:
        print("\nAll Data Quality and PyTest checks PASSED!")


def cmd_dashboard(args):
    """Launches local web server with backend SQLite query API for the PixelPulse Web Dashboard UI."""
    port = getattr(args, "port", 8000)
    cmd_analyze(args)

    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(BASE_DIR), **kwargs)

        def do_POST(self):
            db = DatabaseEngine(db_path=DB_PATH)
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(body) if body else {}

            if self.path == "/api/query":
                sql_query = payload.get("query", "")
                try:
                    start_time = time.perf_counter()
                    df = db.execute_query(sql_query)
                    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                    response_data = {
                        "status": "success",
                        "elapsed_ms": elapsed_ms,
                        "count": len(df),
                        "columns": list(df.columns),
                        "rows": df.to_dict(orient="records")
                    }
                except Exception as e:
                    response_data = {"status": "error", "error_message": str(e)}

                self.send_json(response_data)

            elif self.path == "/api/explain":
                sql_query = payload.get("query", "")
                try:
                    explain_sql = f"EXPLAIN QUERY PLAN {sql_query};"
                    df = db.execute_query(explain_sql)
                    response_data = {
                        "status": "success",
                        "columns": list(df.columns),
                        "rows": df.to_dict(orient="records")
                    }
                except Exception as e:
                    response_data = {"status": "error", "error_message": str(e)}

                self.send_json(response_data)

            elif self.path == "/api/user_timeline":
                raw_id = str(payload.get("user_id", "1")).strip().lower()
                clean_id = raw_id.replace("user_", "").lstrip("0") or "1"
                try:
                    user_df = db.execute_query(f"SELECT * FROM users WHERE user_id = {clean_id};")
                    events_df = db.execute_query(f"SELECT * FROM events WHERE user_id = {clean_id} ORDER BY event_date ASC;")
                    subs_df = db.execute_query(f"SELECT * FROM subscriptions WHERE user_id = {clean_id};")

                    response_data = {
                        "status": "success",
                        "user": user_df.to_dict(orient="records")[0] if not user_df.empty else {},
                        "events": events_df.to_dict(orient="records"),
                        "subscription": subs_df.to_dict(orient="records")[0] if not subs_df.empty else None
                    }
                except Exception as e:
                    response_data = {"status": "error", "error_message": str(e)}

                self.send_json(response_data)
            else:
                super().do_POST()

        def send_json(self, data):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))

    url = f"http://localhost:{port}"
    print(f"\n[+] Launching PixelPulse AI Web Dashboard & Live SQLite API at {url}...")
    webbrowser.open(url)

    with socketserver.TCPServer(("", port), CustomHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nDashboard server stopped.")


def cmd_run_all(args):
    """Runs end-to-end data pipeline: generate -> analyze -> test."""
    cmd_generate(args)
    cmd_analyze(args)
    cmd_test(args)
    print("\nEnd-to-end PixelPulse pipeline completed successfully!")


def main():
    parser = argparse.ArgumentParser(description="PixelPulse Product Analytics CLI & Dashboard Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate synthetic database")
    gen_parser.add_argument("--n-users", type=int, default=6000, help="Number of users")
    gen_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    gen_parser.set_defaults(func=cmd_generate)

    # analyze
    ana_parser = subparsers.add_parser("analyze", help="Execute SQL analysis & export data.json")
    ana_parser.set_defaults(func=cmd_analyze)

    # test
    test_parser = subparsers.add_parser("test", help="Run data quality and unit tests")
    test_parser.set_defaults(func=cmd_test)

    # dashboard
    dash_parser = subparsers.add_parser("dashboard", help="Launch interactive Web Dashboard UI")
    dash_parser.add_argument("--port", type=int, default=8000, help="Server port")
    dash_parser.set_defaults(func=cmd_dashboard)

    # run-all
    runall_parser = subparsers.add_parser("run-all", help="Execute end-to-end pipeline")
    runall_parser.add_argument("--n-users", type=int, default=6000, help="Number of users")
    runall_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    runall_parser.set_defaults(func=cmd_run_all)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
