"""
Vercel WSGI Serverless Function Handler for PixelPulse API.
"""

import json
import time
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.database import DatabaseEngine
from config import DB_PATH


def app(environ, start_response):
    path = environ.get("PATH_INFO", "")
    method = environ.get("REQUEST_METHOD", "GET")

    if method == "OPTIONS":
        start_response("200 OK", [
            ("Content-Type", "application/json"),
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "POST, GET, OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type")
        ])
        return [b"{}"]

    if method == "POST":
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
            body = environ["wsgi.input"].read(content_length).decode("utf-8")
            payload = json.loads(body)
        except Exception:
            payload = {}

        db = DatabaseEngine(db_path=DB_PATH)

        if path.endswith("/query") or "query" in path:
            sql_query = payload.get("query", "")
            try:
                start_time = time.perf_counter()
                df = db.execute_query(sql_query)
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                res = {
                    "status": "success",
                    "elapsed_ms": elapsed_ms,
                    "count": len(df),
                    "columns": list(df.columns),
                    "rows": df.to_dict(orient="records")
                }
            except Exception as e:
                res = {"status": "error", "error_message": str(e)}

        elif path.endswith("/explain") or "explain" in path:
            sql_query = payload.get("query", "")
            try:
                df = db.execute_query(f"EXPLAIN QUERY PLAN {sql_query};")
                res = {"status": "success", "columns": list(df.columns), "rows": df.to_dict(orient="records")}
            except Exception as e:
                res = {"status": "error", "error_message": str(e)}

        elif path.endswith("/user_timeline") or "user_timeline" in path:
            raw_id = str(payload.get("user_id", "1")).strip().lower()
            clean_id = raw_id.replace("user_", "").lstrip("0") or "1"
            try:
                user_df = db.execute_query(f"SELECT * FROM users WHERE user_id = {clean_id};")
                events_df = db.execute_query(f"SELECT * FROM events WHERE user_id = {clean_id} ORDER BY event_date ASC;")
                subs_df = db.execute_query(f"SELECT * FROM subscriptions WHERE user_id = {clean_id};")

                res = {
                    "status": "success",
                    "user": user_df.to_dict(orient="records")[0] if not user_df.empty else {},
                    "events": events_df.to_dict(orient="records"),
                    "subscription": subs_df.to_dict(orient="records")[0] if not subs_df.empty else None
                }
            except Exception as e:
                res = {"status": "error", "error_message": str(e)}
        else:
            res = {"status": "error", "error_message": "Endpoint not found"}

        start_response("200 OK", [
            ("Content-Type", "application/json"),
            ("Access-Control-Allow-Origin", "*")
        ])
        return [json.dumps(res).encode("utf-8")]

    start_response("200 OK", [
        ("Content-Type", "application/json"),
        ("Access-Control-Allow-Origin", "*")
    ])
    return [json.dumps({"status": "healthy", "service": "PixelPulse API"}).encode("utf-8")]
