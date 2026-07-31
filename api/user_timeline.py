from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.database import DatabaseEngine
from config import DB_PATH


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        db = DatabaseEngine(db_path=DB_PATH)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

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

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode("utf-8"))
