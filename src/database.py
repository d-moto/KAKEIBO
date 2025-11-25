import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

from core.database_manager import DatabaseManager
from repositories.transaction_repository import TransactionRepository
from repositories.account_repository import AccountRepository
from repositories.budget_repository import BudgetRepository
from repositories.settings_repository import SettingsRepository
from services.finance_service import FinanceService

logger = logging.getLogger("Kakeibo")

# Use AppData for database to ensure write permissions
app_data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Kakeibo')
os.makedirs(app_data_dir, exist_ok=True)
DB_FILE = os.path.join(app_data_dir, "kakeibo.db")

class Database:
    def __init__(self, db_file: str = DB_FILE):
        self.db_manager = DatabaseManager(db_file)
        self.transaction_repo = TransactionRepository(self.db_manager)
        self.account_repo = AccountRepository(self.db_manager)
        self.budget_repo = BudgetRepository(self.db_manager)
        self.settings_repo = SettingsRepository(self.db_manager)
        self.finance_service = FinanceService(self.transaction_repo, self.budget_repo, self.account_repo)

    def get_connection(self):
        return self.db_manager.get_connection()

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
                note TEXT,
                account_id INTEGER,
                credit_card_id INTEGER
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

        # Credit Cards Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                linked_account_id INTEGER,
                withdrawal_day INTEGER,
                closing_day INTEGER DEFAULT 31, -- Default to end of month
                balance INTEGER DEFAULT 0,
                FOREIGN KEY(linked_account_id) REFERENCES accounts(id)
            )
        """)

        # Migrations (Simplified for refactor: just run them, they are safe if columns exist)
        # In a real app, we should have a proper migration system.
        try:
            cursor.execute("ALTER TABLE fixed_costs ADD COLUMN payment_method TEXT")
        except: pass
        try:
            cursor.execute("ALTER TABLE fixed_costs ADD COLUMN payment_account_id INTEGER")
        except: pass
        try:
            cursor.execute("ALTER TABLE fixed_costs ADD COLUMN payment_card_id INTEGER")
        except: pass
        try:
            cursor.execute("ALTER TABLE accounts ADD COLUMN asset_type TEXT DEFAULT 'Bank'")
        except: pass
        try:
            cursor.execute("ALTER TABLE accounts ADD COLUMN linked_account_id INTEGER")
        except: pass
        try:
            cursor.execute("ALTER TABLE accounts ADD COLUMN linked_card_id INTEGER")
        except: pass
        try:
            cursor.execute("ALTER TABLE credit_cards ADD COLUMN balance INTEGER DEFAULT 0")
        except: pass
        try:
            cursor.execute("ALTER TABLE credit_cards ADD COLUMN closing_day INTEGER DEFAULT 31")
        except: pass
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN account_id INTEGER")
        except: pass
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN credit_card_id INTEGER")
        except: pass
        
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

    # --- Delegated Methods ---

    def add_fixed_cost(self, *args, **kwargs):
        return self.budget_repo.add_fixed_cost(*args, **kwargs)

    def get_fixed_costs(self):
        return self.budget_repo.get_fixed_costs()

    def delete_fixed_cost(self, *args, **kwargs):
        return self.budget_repo.delete_fixed_cost(*args, **kwargs)

    def update_fixed_cost(self, *args, **kwargs):
        return self.budget_repo.update_fixed_cost(*args, **kwargs)

    def update_fixed_cost_last_added(self, *args, **kwargs):
        return self.budget_repo.update_fixed_cost_last_added(*args, **kwargs)

    def process_fixed_costs(self):
        return self.finance_service.process_fixed_costs()

    def get_monthly_summary(self, *args, **kwargs):
        return self.transaction_repo.get_monthly_summary(*args, **kwargs)

    def get_budget(self, *args, **kwargs):
        return self.budget_repo.get_budget(*args, **kwargs)

    def set_budget(self, *args, **kwargs):
        return self.budget_repo.set_budget(*args, **kwargs)

    def get_category_budgets(self):
        return self.budget_repo.get_category_budgets()

    def set_category_budget(self, *args, **kwargs):
        return self.budget_repo.set_category_budget(*args, **kwargs)

    def add_account(self, *args, **kwargs):
        return self.account_repo.add_account(*args, **kwargs)

    def get_accounts(self):
        return self.account_repo.get_accounts()

    def update_account_balance(self, *args, **kwargs):
        return self.account_repo.update_account_balance(*args, **kwargs)

    def delete_account(self, *args, **kwargs):
        return self.account_repo.delete_account(*args, **kwargs)

    def update_account(self, *args, **kwargs):
        return self.account_repo.update_account(*args, **kwargs)

    def add_credit_card(self, *args, **kwargs):
        return self.account_repo.add_credit_card(*args, **kwargs)

    def get_credit_cards(self):
        return self.account_repo.get_credit_cards()

    def delete_credit_card(self, *args, **kwargs):
        return self.account_repo.delete_credit_card(*args, **kwargs)

    def update_credit_card(self, *args, **kwargs):
        return self.account_repo.update_credit_card(*args, **kwargs)

    def update_credit_card_balance(self, *args, **kwargs):
        return self.account_repo.update_credit_card_balance(*args, **kwargs)

    def get_total_liabilities(self):
        return self.account_repo.get_total_liabilities()

    def get_net_assets(self):
        return self.account_repo.get_total_assets() - self.account_repo.get_total_liabilities()

    def get_setting(self, *args, **kwargs):
        return self.settings_repo.get_setting(*args, **kwargs)

    def set_setting(self, *args, **kwargs):
        return self.settings_repo.set_setting(*args, **kwargs)

    def add_transaction(self, *args, **kwargs):
        return self.finance_service.add_transaction(*args, **kwargs)

    def update_transaction(self, *args, **kwargs):
        return self.transaction_repo.update_transaction(*args, **kwargs)

    def get_transactions(self, *args, **kwargs):
        return self.transaction_repo.get_transactions(*args, **kwargs)

    def get_all_transactions(self):
        return self.transaction_repo.get_transactions(month=None)

    def transaction_exists(self, *args, **kwargs):
        return self.transaction_repo.transaction_exists(*args, **kwargs)

    def import_transactions(self, transactions: List[Dict]) -> int:
        # This logic was in Database, I should probably move it to Service or Repository.
        # It has loop and logic.
        # For now, I'll implement it here using repository methods to keep it simple, 
        # or better, move it to TransactionRepository?
        # TransactionRepository has `transaction_exists`.
        # Let's move `import_transactions` to TransactionRepository?
        # But `import_transactions` does bulk insert.
        # I'll implement it here delegating to repo.
        added_count = 0
        for t in transactions:
            if not self.transaction_repo.transaction_exists(t['date'], t['type'], t['category'], t['amount'], t['note']):
                self.transaction_repo.add_transaction(t['date'], t['type'], t['category'], t['amount'], t['note'])
                added_count += 1
        return added_count

    def get_balance(self, *args, **kwargs):
        return self.transaction_repo.get_balance(*args, **kwargs)

    def delete_transaction(self, *args, **kwargs):
        return self.transaction_repo.delete_transaction(*args, **kwargs)

    def get_categories(self, *args, **kwargs):
        return self.settings_repo.get_categories(*args, **kwargs)

    def add_category(self, *args, **kwargs):
        return self.settings_repo.add_category(*args, **kwargs)

    def delete_category(self, *args, **kwargs):
        return self.settings_repo.delete_category(*args, **kwargs)

    def get_total_assets(self):
        return self.account_repo.get_total_assets()

    def get_total_assets_by_type(self):
        return self.account_repo.get_total_assets_by_type()

    def get_liquid_assets(self):
        return self.account_repo.get_liquid_assets()

    def get_next_payment(self):
        return self.finance_service.get_next_payment()

    def calculate_next_payment(self, *args, **kwargs):
        return self.finance_service.calculate_next_payment(*args, **kwargs)

    def get_asset_trend(self, *args, **kwargs):
        return self.finance_service.get_asset_trend(*args, **kwargs)

    def get_monthly_comparison(self, *args, **kwargs):
        return self.finance_service.get_monthly_comparison(*args, **kwargs)

    def get_category_trend(self, *args, **kwargs):
        return self.finance_service.get_category_trend(*args, **kwargs)

    def get_transactions_by_date_range(self, *args, **kwargs):
        return self.transaction_repo.get_transactions_by_date_range(*args, **kwargs)
