import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger("Kakeibo")

# Use AppData for database to ensure write permissions
app_data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Kakeibo')
os.makedirs(app_data_dir, exist_ok=True)
DB_FILE = os.path.join(app_data_dir, "kakeibo.db")

class Database:
    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        # self.init_db() # Removed to prevent repeated initialization

    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        conn.set_trace_callback(logger.debug)
        return conn

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
                last_added_month TEXT,
                payment_method TEXT, -- 'Cash', 'Bank', 'Credit Card'
                payment_account_id INTEGER,
                payment_card_id INTEGER
            )
        """)

        # Add new columns to fixed_costs if they don't exist
        try:
            cursor.execute("ALTER TABLE fixed_costs ADD COLUMN payment_method TEXT")
        except Exception as e:
            logger.warning(f"Migration error (payment_method): {e}")
        try:
            cursor.execute("ALTER TABLE fixed_costs ADD COLUMN payment_account_id INTEGER")
        except Exception as e:
            logger.warning(f"Migration error (payment_account_id): {e}")
        try:
            cursor.execute("ALTER TABLE fixed_costs ADD COLUMN payment_card_id INTEGER")
        except Exception as e:
            logger.warning(f"Migration error (payment_card_id): {e}")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_budgets (
                category TEXT PRIMARY KEY,
                amount INTEGER
            )
        """)
        
        # Accounts Table

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                balance INTEGER DEFAULT 0,
                asset_type TEXT DEFAULT 'Bank', -- 'Bank', 'Cash', 'Investment', 'Stock', 'Other'
                linked_account_id INTEGER,
                linked_card_id INTEGER,
                FOREIGN KEY(linked_account_id) REFERENCES accounts(id),
                FOREIGN KEY(linked_card_id) REFERENCES credit_cards(id)
            )
        """)

        # Add asset_type column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE accounts ADD COLUMN asset_type TEXT DEFAULT 'Bank'")
        except Exception as e:
            logger.warning(f"Migration error (asset_type): {e}")

        # Add linked columns if they don't exist
        try:
            cursor.execute("ALTER TABLE accounts ADD COLUMN linked_account_id INTEGER")
        except Exception as e:
            logger.warning(f"Migration error (linked_account_id): {e}")
        try:
            cursor.execute("ALTER TABLE accounts ADD COLUMN linked_card_id INTEGER")
        except Exception as e:
            logger.warning(f"Migration error (linked_card_id): {e}")

        # Credit Cards Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                linked_account_id INTEGER,
                withdrawal_day INTEGER,
                balance INTEGER DEFAULT 0,
                FOREIGN KEY(linked_account_id) REFERENCES accounts(id)
            )
        """)

        # Add balance column to credit_cards if it doesn't exist
        try:
            cursor.execute("ALTER TABLE credit_cards ADD COLUMN balance INTEGER DEFAULT 0")
        except Exception as e:
            logger.warning(f"Migration error (credit_cards balance): {e}")

        # Update transactions table to include account_id and credit_card_id if they don't exist
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN account_id INTEGER")
        except Exception as e:
            logger.warning(f"Migration error (account_id): {e}") # Column likely exists
            
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN credit_card_id INTEGER")
        except Exception as e:
            logger.warning(f"Migration error (credit_card_id): {e}") # Column likely exists
        
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

        # Create Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)")

        # Initialize default settings
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("csv_encoding", "Shift-JIS"))
            
        conn.commit()
        conn.close()

    def add_fixed_cost(self, name: str, amount: int, category: str, type: str, day_of_month: int, payment_method: str = "Cash", payment_account_id: int = None, payment_card_id: int = None):
        """Add a new fixed cost."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO fixed_costs (name, amount, category, type, day_of_month, payment_method, payment_account_id, payment_card_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, amount, category, type, day_of_month, payment_method, payment_account_id, payment_card_id))
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

    def update_fixed_cost(self, fixed_cost_id: int, name: str, amount: int, category: str, type: str, day_of_month: int, payment_method: str = "Cash", payment_account_id: int = None, payment_card_id: int = None):
        """Update an existing fixed cost."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE fixed_costs 
            SET name = ?, amount = ?, category = ?, type = ?, day_of_month = ?, payment_method = ?, payment_account_id = ?, payment_card_id = ?
            WHERE id = ?
        """, (name, amount, category, type, day_of_month, payment_method, payment_account_id, payment_card_id, fixed_cost_id))
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
        
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM fixed_costs")
            fixed_costs = [dict(row) for row in cursor.fetchall()]
            
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
                        
                        # Determine account/card IDs
                        account_id = fc['payment_account_id']
                        credit_card_id = fc['payment_card_id']
                        
                        cursor.execute("""
                            INSERT INTO transactions (date, type, category, amount, note, account_id, credit_card_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (date_str, fc['type'], fc['category'], fc['amount'], f"Fixed Cost: {fc['name']}", account_id, credit_card_id))
                        
                        # Handle Side Effects (Logic duplicated from add_transaction for performance)
                        if fc['type'] == "Expense" and credit_card_id:
                             cursor.execute("UPDATE credit_cards SET balance = balance + ? WHERE id = ?", (fc['amount'], credit_card_id))
                        
                        # Update account balance if bank account used
                        if account_id:
                            cursor.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (fc['amount'], account_id)) # Note: Subtracting for expense

                        # Update last added month
                        cursor.execute("UPDATE fixed_costs SET last_added_month = ? WHERE id = ?", (current_month, fc['id']))
                        added_count += 1
            
            conn.commit()
            return added_count
        except Exception as e:
            logger.error(f"Error processing fixed costs: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()

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
        conn.commit()
        conn.close()

    def get_category_budgets(self) -> Dict[str, int]:
        """Get all category budgets."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT category, amount FROM category_budgets")
        rows = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}

    def set_category_budget(self, category: str, amount: int):
        """Set budget for a specific category."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO category_budgets (category, amount) VALUES (?, ?)", (category, amount))
        conn.commit()
        conn.close()

    # --- Account Methods ---
    def add_account(self, name: str, type: str, initial_balance: int = 0, asset_type: str = "Bank", linked_account_id: int = None, linked_card_id: int = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO accounts (name, type, balance, asset_type, linked_account_id, linked_card_id) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, type, initial_balance, asset_type, linked_account_id, linked_card_id))
        conn.commit()
        conn.close()

    def get_accounts(self) -> List[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_account_balance(self, account_id: int, amount: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, account_id))
        conn.commit()
        conn.close()

    def delete_account(self, account_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        conn.commit()
        conn.close()

    def update_account(self, account_id: int, name: str, type: str, balance: int, asset_type: str, linked_account_id: int = None, linked_card_id: int = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE accounts 
            SET name = ?, type = ?, balance = ?, asset_type = ?, linked_account_id = ?, linked_card_id = ?
            WHERE id = ?
        """, (name, type, balance, asset_type, linked_account_id, linked_card_id, account_id))
        conn.commit()
        conn.close()

    # --- Credit Card Methods ---
    def add_credit_card(self, name: str, linked_account_id: int, withdrawal_day: int, initial_balance: int = 0):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO credit_cards (name, linked_account_id, withdrawal_day, balance) VALUES (?, ?, ?, ?)", 
                       (name, linked_account_id, withdrawal_day, initial_balance))
        conn.commit()
        conn.close()

    def get_credit_cards(self) -> List[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cc.*, a.name as linked_account_name 
            FROM credit_cards cc 
            LEFT JOIN accounts a ON cc.linked_account_id = a.id
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_credit_card(self, card_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM credit_cards WHERE id = ?", (card_id,))
        conn.commit()
        conn.close()

    def update_credit_card(self, card_id: int, name: str, linked_account_id: int, withdrawal_day: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE credit_cards 
            SET name = ?, linked_account_id = ?, withdrawal_day = ?
            WHERE id = ?
        """, (name, linked_account_id, withdrawal_day, card_id))
        conn.commit()
        conn.close()

    def update_credit_card_balance(self, card_id: int, amount: int):
        """Update credit card balance (Liability). Positive amount increases liability."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE credit_cards SET balance = balance + ? WHERE id = ?", (amount, card_id))
        conn.commit()
        conn.close()

    def get_total_liabilities(self) -> int:
        """Get sum of all credit card balances (Liabilities)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(balance) FROM credit_cards")
        result = cursor.fetchone()[0]
        conn.close()
        return result if result is not None else 0

    def get_net_assets(self) -> int:
        """Get Net Assets (Total Assets - Total Liabilities)."""
        return self.get_total_assets() - self.get_total_liabilities()

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

    def add_transaction(self, date: str, type: str, category: str, amount: int, note: str = "", account_id: int = None, credit_card_id: int = None):
        """Add a new transaction."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (date, type, category, amount, note, account_id, credit_card_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date, type, category, amount, note, account_id, credit_card_id))
        conn.commit()
        conn.close()

        # Handle Side Effects
        if type == "Expense" and credit_card_id:
            # Expense via Credit Card increases Liability
            self.update_credit_card_balance(credit_card_id, amount)

    def update_transaction(self, transaction_id: int, date: str, type: str, category: str, amount: int, note: str = "", account_id: int = None, credit_card_id: int = None):
        """Update an existing transaction."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE transactions 
            SET date = ?, type = ?, category = ?, amount = ?, note = ?, account_id = ?, credit_card_id = ?
            WHERE id = ?
        """, (date, type, category, amount, note, account_id, credit_card_id, transaction_id))
        conn.commit()
        conn.close()

    def get_transactions(self, month: str = None) -> List[Dict]:
        """Get transactions, optionally filtered by month (YYYY-MM)."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if month:
            cursor.execute("""
                SELECT t.*, a.name as account_name, cc.name as credit_card_name, la.name as linked_account_name
                FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.id
                LEFT JOIN credit_cards cc ON t.credit_card_id = cc.id
                LEFT JOIN accounts la ON cc.linked_account_id = la.id
                WHERE t.date LIKE ? 
                ORDER BY t.date DESC, t.id DESC
            """, (f"{month}%",))
        else:
            cursor.execute("""
                SELECT t.*, a.name as account_name, cc.name as credit_card_name, la.name as linked_account_name
                FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.id
                LEFT JOIN credit_cards cc ON t.credit_card_id = cc.id
                LEFT JOIN accounts la ON cc.linked_account_id = la.id
                ORDER BY t.date DESC, t.id DESC
            """)
            
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_all_transactions(self) -> List[Dict]:
        """Get all transactions sorted by date."""
        return self.get_transactions(month=None)

    def transaction_exists(self, date: str, type_: str, category: str, amount: int, note: str) -> bool:
        """Check if a transaction already exists to avoid duplicates during import."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT count(*) FROM transactions 
            WHERE date = ? AND type = ? AND category = ? AND amount = ? AND note = ?
        """, (date, type_, category, amount, note))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def import_transactions(self, transactions: List[Dict]) -> int:
        """
        Import transactions from a list of dictionaries.
        Returns the number of transactions successfully added.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        added_count = 0
        
        for t in transactions:
            # Check for duplicates
            cursor.execute("""
                SELECT count(*) FROM transactions 
                WHERE date = ? AND type = ? AND category = ? AND amount = ? AND note = ?
            """, (t['date'], t['type'], t['category'], t['amount'], t['note']))
            
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO transactions (date, type, category, amount, note)
                    VALUES (?, ?, ?, ?, ?)
                """, (t['date'], t['type'], t['category'], t['amount'], t['note']))
                added_count += 1
                
        conn.commit()
        conn.close()
        return added_count

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

    def get_total_assets(self) -> int:
        """Get sum of all account balances."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(balance) FROM accounts")
        result = cursor.fetchone()[0]
        conn.close()
        return result if result is not None else 0

    def get_total_assets_by_type(self) -> Dict[str, int]:
        """Get total assets grouped by asset type."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT asset_type, SUM(balance) FROM accounts GROUP BY asset_type")
        rows = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}

    def get_liquid_assets(self) -> int:
        """Get sum of Bank and Cash account balances."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(balance) FROM accounts WHERE asset_type IN ('Bank', 'Cash')")
        result = cursor.fetchone()[0]
        conn.close()
        return result if result is not None else 0

    def get_next_payment(self):
        """
        Calculates the next significant payment (Credit Card withdrawal or Fixed Cost).
        Returns a dict with 'date', 'amount', 'name'.
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        today = datetime.now()
        next_payment = None
        min_days_diff = float('inf')

        # 1. Check Credit Card Withdrawals
        cursor.execute("SELECT * FROM credit_cards")
        cards = cursor.fetchall()
        
        for card in cards:
            withdrawal_day = card['withdrawal_day']
            if not withdrawal_day:
                continue
                
            # Calculate next withdrawal date
            try:
                target_date = today.replace(day=withdrawal_day)
                if target_date < today:
                    # Move to next month
                    if today.month == 12:
                        target_date = target_date.replace(year=today.year + 1, month=1)
                    else:
                        target_date = target_date.replace(month=today.month + 1)
            except ValueError:
                # Handle invalid dates (e.g. Feb 30) by skipping or adjusting
                continue
            
            # Estimate amount (simplified: current balance)
            amount = card['balance']
            if amount <= 0:
                continue

            days_diff = (target_date - today).days
            if 0 <= days_diff < min_days_diff:
                min_days_diff = days_diff
                next_payment = {
                    'date': target_date.strftime("%Y-%m-%d"),
                    'amount': amount,
                    'name': f"{card['name']} Withdrawal"
                }

        # 2. Check Fixed Costs
        cursor.execute("SELECT * FROM fixed_costs")
        fixed_costs = cursor.fetchall()
        
        for fc in fixed_costs:
            day = fc['day_of_month']
            try:
                target_date = today.replace(day=day)
                if target_date < today:
                     if today.month == 12:
                        target_date = target_date.replace(year=today.year + 1, month=1)
                     else:
                        target_date = target_date.replace(month=today.month + 1)
            except ValueError:
                continue
                
            days_diff = (target_date - today).days
            
            if 0 <= days_diff < min_days_diff:
                min_days_diff = days_diff
                next_payment = {
                    'date': target_date.strftime("%Y-%m-%d"),
                    'amount': fc['amount'],
                    'name': fc['name']
                }
            elif days_diff == min_days_diff and next_payment:
                 next_payment['amount'] += fc['amount']
                 next_payment['name'] += f", {fc['name']}"

        conn.close()
        return next_payment

    def get_asset_trend(self, days: int = 30) -> List[Dict]:
        """Calculate asset trend for the last N days."""
        from datetime import datetime, timedelta
        
        current_assets = self.get_total_assets()
        trend = []
        today = datetime.now().date()
        
        # Get transactions for the period that affected accounts
        start_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, type, amount 
            FROM transactions 
            WHERE date >= ? AND account_id IS NOT NULL
            ORDER BY date DESC
        """, (start_date,))
        transactions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Group transactions by date
        tx_by_date = {}
        for t in transactions:
            date_str = t['date']
            if date_str not in tx_by_date:
                tx_by_date[date_str] = []
            tx_by_date[date_str].append(t)
            
        # Iterate backwards
        current_balance = current_assets
        
        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            trend.append({"date": date_str, "amount": current_balance})
            
            # Reverse transactions for this day to get previous day's ending balance
            if date_str in tx_by_date:
                for t in tx_by_date[date_str]:
                    if t['type'] == 'Income':
                        current_balance -= t['amount']
                    elif t['type'] == 'Expense':
                        current_balance += t['amount']
                        
        return list(reversed(trend))

    def get_monthly_comparison(self, months: int = 6) -> List[Dict]:
        """Get income vs expense comparison for the last N months."""
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        today = datetime.now().date()
        start_date = (today - relativedelta(months=months-1)).replace(day=1)
        start_str = start_date.strftime("%Y-%m")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get monthly totals
        cursor.execute("""
            SELECT strftime('%Y-%m', date) as month, type, SUM(amount) 
            FROM transactions 
            WHERE strftime('%Y-%m', date) >= ?
            GROUP BY month, type
            ORDER BY month ASC
        """, (start_str,))
        
        rows = cursor.fetchall()
        conn.close()
        
        data = {}
        # Initialize with all months
        for i in range(months):
            d = start_date + relativedelta(months=i)
            m = d.strftime("%Y-%m")
            data[m] = {'month': m, 'income': 0, 'expense': 0}
            
        for row in rows:
            month, type_, amount = row
            if month in data:
                if type_ == 'Income':
                    data[month]['income'] = amount
                elif type_ == 'Expense':
                    data[month]['expense'] = amount
                    
        return list(data.values())

    def get_category_trend(self, category: str, months: int = 6) -> List[Dict]:
        """Get spending trend for a specific category over the last N months."""
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        today = datetime.now().date()
        start_date = (today - relativedelta(months=months-1)).replace(day=1)
        start_str = start_date.strftime("%Y-%m")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT strftime('%Y-%m', date) as month, SUM(amount)
            FROM transactions
            WHERE category = ? AND strftime('%Y-%m', date) >= ?
            GROUP BY month
            ORDER BY month ASC
        """, (category, start_str))
        
        rows = cursor.fetchall()
        conn.close()
        
        data = {}
        for i in range(months):
            d = start_date + relativedelta(months=i)
            m = d.strftime("%Y-%m")
            data[m] = {'month': m, 'amount': 0}
            
        for row in rows:
            month, amount = row
            if month in data:
                data[month]['amount'] = amount
                
        return list(data.values())
