from typing import List, Dict
from core.database_manager import DatabaseManager

class SettingsRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_setting(self, key: str, default: str = None) -> str:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default

    def set_setting(self, key: str, value: str):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()

    def get_categories(self, type_filter: str = None) -> List[Dict]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        if type_filter:
            cursor.execute("SELECT * FROM categories WHERE type = ?", (type_filter,))
        else:
            cursor.execute("SELECT * FROM categories")
            
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def add_category(self, name: str, type: str):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories (name, type) VALUES (?, ?)", (name, type))
        conn.commit()
        conn.close()

    def delete_category(self, category_id: int):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
        conn.close()
