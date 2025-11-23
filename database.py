import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

# Use AppData for database to ensure write permissions
app_data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Kakeibo')
os.makedirs(app_data_dir, exist_ok=True)
DB_FILE = os.path.join(app_data_dir, "kakeibo.db")

class Database:
    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_file)

    def init_db(self):
        """Initialize the database table."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL, -- 'Income' or 'Expense'
                category TEXT NOT NULL,
                amount INTEGER NOT NULL,
                note TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Check if categories exist, if not add defaults
        cursor.execute("SELECT count(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            default_categories = [
                ("Salary", "Income"),
                ("Bonus", "Income"),
                ("Other", "Income"),
                ("Food", "Expense"),
                ("Transport", "Expense"),
                ("Rent", "Expense"),
                ("Utilities", "Expense"),
                ("Entertainment", "Expense"),
                ("Shopping", "Expense"),
                ("Healthcare", "Expense"),
                ("Education", "Expense"),
                ("Other", "Expense"),
            ]
            cursor.executemany("INSERT INTO categories (name, type) VALUES (?, ?)", default_categories)

        # Initialize default settings
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("csv_encoding", "Shift-JIS"))
            
        conn.commit()
        conn.close()

    def get_setting(self, key: str, default: str = None) -> str:
        """Get a setting value."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default

    def set_setting(self, key: str, value: str):
        """Set a setting value."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()

    def add_transaction(self, date: str, type: str, category: str, amount: int, note: str = ""):
        """Add a new transaction."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (date, type, category, amount, note)
            VALUES (?, ?, ?, ?, ?)
        """, (date, type, category, amount, note))
        conn.commit()
        conn.close()

    def update_transaction(self, transaction_id: int, date: str, type: str, category: str, amount: int, note: str = ""):
        """Update an existing transaction."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE transactions 
            SET date = ?, type = ?, category = ?, amount = ?, note = ?
            WHERE id = ?
        """, (date, type, category, amount, note, transaction_id))
        conn.commit()
        conn.close()

    def get_transactions(self, month: str = None) -> List[Dict]:
        """Get transactions, optionally filtered by month (YYYY-MM)."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if month:
            cursor.execute("SELECT * FROM transactions WHERE date LIKE ? ORDER BY date DESC, id DESC", (f"{month}%",))
        else:
            cursor.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC")
            
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_balance(self, month: str = None) -> int:
        """Calculate balance, optionally filtered by month (YYYY-MM)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if month:
            cursor.execute("SELECT type, amount FROM transactions WHERE date LIKE ?", (f"{month}%",))
        else:
            cursor.execute("SELECT type, amount FROM transactions")
            
        rows = cursor.fetchall()
        conn.close()

        balance = 0
        for type_, amount in rows:
            if type_ == "Income":
                balance += amount
            elif type_ == "Expense":
                balance -= amount
        return balance

    def delete_transaction(self, transaction_id: int):
        """Delete a transaction by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        conn.close()

    def get_categories(self, type_filter: str = None) -> List[Dict]:
        """Get categories, optionally filtered by type (Income/Expense)."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if type_filter:
            cursor.execute("SELECT * FROM categories WHERE type = ?", (type_filter,))
        else:
            cursor.execute("SELECT * FROM categories")
            
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def add_category(self, name: str, type: str):
        """Add a new category."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories (name, type) VALUES (?, ?)", (name, type))
        conn.commit()
        conn.close()

    def delete_category(self, category_id: int):
        """Delete a category."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
        conn.close()
