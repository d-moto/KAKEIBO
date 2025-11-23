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
