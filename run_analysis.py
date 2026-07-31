"""
Backward-compatible wrapper entrypoint for SQL analysis pipeline.
Dynamically parses analysis_queries.sql, executes against pixelloft.db,
computes A/B statistical significance, and updates visualizations and CSV outputs.
"""

from cli import cmd_analyze

if __name__ == "__main__":
    class DummyArgs:
        pass
    cmd_analyze(DummyArgs())
