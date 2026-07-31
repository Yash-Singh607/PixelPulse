from http.server import BaseHTTPRequestHandler
import json
import time
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

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode("utf-8"))
