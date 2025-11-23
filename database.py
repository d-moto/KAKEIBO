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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                month TEXT PRIMARY KEY,
                amount INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fixed_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount INTEGER NOT NULL,
                category TEXT NOT NULL,
                type TEXT NOT NULL,
                day_of_month INTEGER NOT NULL,
                last_added_month TEXT
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

    def add_fixed_cost(self, name: str, amount: int, category: str, type: str, day_of_month: int):
        """Add a new fixed cost."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO fixed_costs (name, amount, category, type, day_of_month)
            VALUES (?, ?, ?, ?, ?)
        """, (name, amount, category, type, day_of_month))
        conn.commit()
        conn.close()

    def get_fixed_costs(self) -> List[Dict]:
        """Get all fixed costs."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fixed_costs")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_fixed_cost(self, fixed_cost_id: int):
        """Delete a fixed cost."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fixed_costs WHERE id = ?", (fixed_cost_id,))
        conn.commit()
        conn.close()

    def update_fixed_cost_last_added(self, fixed_cost_id: int, month: str):
        """Update the last added month for a fixed cost."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE fixed_costs SET last_added_month = ? WHERE id = ?", (month, fixed_cost_id))
        conn.commit()
        conn.close()

    def process_fixed_costs(self) -> int:
        """Check and auto-add fixed costs. Returns number of added transactions."""
        from datetime import datetime
        
        fixed_costs = self.get_fixed_costs()
        current_date = datetime.now()
        current_month = current_date.strftime("%Y-%m")
        today_day = current_date.day
        
        added_count = 0
        for fc in fixed_costs:
            # If never added (None) or added in a previous month
            if fc['last_added_month'] != current_month:
                # If today is on or after the scheduled day
                if today_day >= fc['day_of_month']:
                    # Add transaction
                    date_str = f"{current_month}-{fc['day_of_month']:02d}"
                    self.add_transaction(date_str, fc['type'], fc['category'], fc['amount'], f"Fixed Cost: {fc['name']}")
                    
                    # Update last added month
                    self.update_fixed_cost_last_added(fc['id'], current_month)
                    added_count += 1
        return added_count

    def get_monthly_summary(self, month: str) -> dict:
        """Get summary of income and expenses for a specific month for Money Flow."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get Income by Category
        cursor.execute("SELECT category, SUM(amount) FROM transactions WHERE type='Income' AND strftime('%Y-%m', date) = ? GROUP BY category", (month,))
        income_data = [{'category': row[0], 'amount': row[1]} for row in cursor.fetchall()]
        
        # Get Expenses by Category
        cursor.execute("SELECT category, SUM(amount) FROM transactions WHERE type='Expense' AND strftime('%Y-%m', date) = ? GROUP BY category", (month,))
        expense_data = [{'category': row[0], 'amount': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        total_income = sum(item['amount'] for item in income_data)
        total_expenses = sum(item['amount'] for item in expense_data)
        
        return {
            'income': income_data,
            'expenses': expense_data,
            'total_income': total_income,
            'total_expenses': total_expenses
        }

    def get_budget(self, month: str) -> int:
        """Get budget for a specific month."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT amount FROM budgets WHERE month = ?", (month,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    def set_budget(self, month: str, amount: int):
        """Set budget for a specific month."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO budgets (month, amount) VALUES (?, ?)", (month, amount))
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
