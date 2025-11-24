import unittest
import os
import sys
import shutil
from datetime import datetime

# Add parent directory and src to path to import database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from database import Database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Use a temporary database for testing
        self.test_db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")
        os.makedirs(self.test_db_dir, exist_ok=True)
        self.db_file = os.path.join(self.test_db_dir, "test_kakeibo.db")
        self.db = Database(self.db_file)

    def tearDown(self):
        # Clean up test database
        self.db.get_connection().close()
        if os.path.exists(self.test_db_dir):
            shutil.rmtree(self.test_db_dir)

    def test_add_get_transaction(self):
        date = "2023-01-01"
        self.db.add_transaction(date, "Expense", "Food", 1000, "Lunch")
        transactions = self.db.get_transactions()
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]['amount'], 1000)
        self.assertEqual(transactions[0]['category'], "Food")

    def test_get_balance(self):
        self.db.add_transaction("2023-01-01", "Income", "Salary", 5000)
        self.db.add_transaction("2023-01-02", "Expense", "Food", 1000)
        balance = self.db.get_balance()
        self.assertEqual(balance, 4000)

    def test_fixed_costs_processing(self):
        # Add a fixed cost scheduled for today
        today = datetime.now()
        day = today.day
        self.db.add_fixed_cost("Rent", 50000, "Housing", "Expense", day)
        
        # Process fixed costs
        added = self.db.process_fixed_costs()
        self.assertEqual(added, 1)
        
        # Verify transaction added
        transactions = self.db.get_transactions()
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]['amount'], 50000)
        self.assertEqual(transactions[0]['note'], "Fixed Cost: Rent")
        
        # Process again, should not add duplicate for this month
        added_again = self.db.process_fixed_costs()
        self.assertEqual(added_again, 0)

    def test_account_balance_update(self):
        self.db.add_account("Bank A", "Bank", 10000)
        accounts = self.db.get_accounts()
        account_id = accounts[0]['id']
        
        self.db.update_account_balance(account_id, -2000)
        
        updated_accounts = self.db.get_accounts()
        self.assertEqual(updated_accounts[0]['balance'], 8000)

if __name__ == '__main__':
    unittest.main()
