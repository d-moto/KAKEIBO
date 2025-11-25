import sqlite3
import os
import logging

logger = logging.getLogger("Kakeibo")

class DatabaseManager:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self._ensure_db_dir()

    def _ensure_db_dir(self):
        db_dir = os.path.dirname(self.db_file)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        conn.set_trace_callback(logger.debug)
        return conn
