"""
SQL Parser Utility for PixelLoft Analytics Pipeline.
Parses named queries dynamically from analysis_queries.sql.
"""

from pathlib import Path
from typing import Dict
from config import SQL_FILE_PATH


class SQLParser:
    """Parses and extracts analytical SQL queries from structured SQL files."""

    def __init__(self, sql_file_path: Path = SQL_FILE_PATH):
        self.sql_file_path = Path(sql_file_path)

    def load_queries(self) -> Dict[str, str]:
        """
        Parses analysis_queries.sql and returns a dictionary of query names to SQL statements:
        - 'funnel'
        - 'cohort'
        - 'ab_test'
        - 'revenue'
        """
        if not self.sql_file_path.exists():
            raise FileNotFoundError(f"SQL file not found at: {self.sql_file_path}")

        content = self.sql_file_path.read_text(encoding="utf-8")

        # Split raw file content into statements by semicolon
        raw_statements = [stmt.strip() for stmt in content.split(";") if stmt.strip()]

        queries = {}
        for stmt in raw_statements:
            stmt_upper = stmt.upper()
            if "WITH FUNNEL AS" in stmt_upper:
                queries["funnel"] = self._clean_statement(stmt)
            elif "WITH COHORT AS" in stmt_upper:
                queries["cohort"] = self._clean_statement(stmt)
            elif "SELECT" in stmt_upper and "EXPERIMENT_GROUP" in stmt_upper:
                queries["ab_test"] = self._clean_statement(stmt)
            elif "SELECT" in stmt_upper and "REVENUE_PER_SIGNUP_USD" in stmt_upper:
                queries["revenue"] = self._clean_statement(stmt)

        return queries

    @staticmethod
    def _clean_statement(statement: str) -> str:
        """Strips leading comment lines and formats SQL statement nicely."""
        lines = statement.splitlines()
        code_lines = [line for line in lines if not line.strip().startswith("--")]
        return "\n".join(code_lines).strip()
