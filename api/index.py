"""
Vercel Serverless Function Handler for PixelPulse API (/api/query, /api/explain, /api/user_timeline).
"""

from http.server import BaseHTTPRequestHandler
import json
import time
import sys
from pathlib import Path

# Add root directory to sys.path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.database import DatabaseEngine
from config import DB_PATH


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        db = DatabaseEngine(db_path=DB_PATH)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

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
            self.send_response(404)
            self.end_headers()

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))
