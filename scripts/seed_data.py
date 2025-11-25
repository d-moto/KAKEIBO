import sys
import os
import sqlite3
from datetime import datetime, timedelta
import random

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import Database

def seed_data():
    db = Database()
    db.init_db()
    
    print("Seeding data...")

    # 1. Accounts
    accounts = db.get_accounts()
    if not accounts:
        print("Creating Accounts...")
        db.add_account("Main Bank", "Bank", 1000000, "Bank")
        db.add_account("Wallet", "Cash", 50000, "Cash")
        accounts = db.get_accounts()
    
    main_bank_id = next((a['id'] for a in accounts if a['name'] == "Main Bank"), None)

    # 2. Credit Cards
    cards = db.get_credit_cards()
    if not cards:
        print("Creating Credit Cards...")
        # Rakuten: Close 15th, Withdraw 10th
        db.add_credit_card("Rakuten Card", main_bank_id, 10, 15)
        # Amazon: Close 31st (End), Withdraw 27th
        db.add_credit_card("Amazon Card", main_bank_id, 27, 31)
        cards = db.get_credit_cards()

    rakuten_id = next((c['id'] for c in cards if c['name'] == "Rakuten Card"), None)
    amazon_id = next((c['id'] for c in cards if c['name'] == "Amazon Card"), None)

    # 3. Transactions (2024 - Historical)
    # Generate for Nov 2024 and Dec 2024
    categories = ["Food", "Transport", "Shopping", "Entertainment", "Utilities"]
    
    dates_2024 = [
        ("2024-11-01", "Income", "Salary", 300000, "November Salary", main_bank_id, None),
        ("2024-11-05", "Expense", "Food", 3500, "Lunch", None, rakuten_id),
        ("2024-11-10", "Expense", "Utilities", 12000, "Electricity", None, amazon_id),
        ("2024-11-15", "Expense", "Shopping", 5000, "Books", None, rakuten_id),
        ("2024-11-20", "Expense", "Entertainment", 8000, "Movie", None, rakuten_id),
        ("2024-11-25", "Expense", "Transport", 10000, "Train Pass", None, amazon_id),
        ("2024-12-01", "Income", "Salary", 300000, "December Salary", main_bank_id, None),
        ("2024-12-05", "Expense", "Food", 4000, "Dinner", None, rakuten_id),
        ("2024-12-24", "Expense", "Entertainment", 15000, "Xmas Party", None, amazon_id),
    ]

    print("Inserting 2024 Data...")
    for date, type_, cat, amount, note, acc_id, card_id in dates_2024:
        if not db.transaction_exists(date, type_, cat, amount, note):
            db.add_transaction(date, type_, cat, amount, note, acc_id, card_id)

    # 4. Transactions (2025 - Recent for Next Payment Forecast)
    # Today is assumed 2025-11-25.
    # Rakuten (Close 15, Pay 10). 
    #   Next Pay: 12/10. Period: 10/16 - 11/15.
    # Amazon (Close 31, Pay 27).
    #   Next Pay: 11/27. Period: 10/1 - 10/31.
    
    dates_2025 = [
        # Rakuten Next Payment (12/10) Data (10/16 - 11/15)
        ("2025-10-20", "Expense", "Shopping", 15000, "Jacket", None, rakuten_id),
        ("2025-11-05", "Expense", "Food", 2000, "Cafe", None, rakuten_id),
        ("2025-11-15", "Expense", "Utilities", 8000, "Gas", None, rakuten_id),
        
        # Rakuten Current Usage (11/16 - Now)
        ("2025-11-20", "Expense", "Food", 3000, "Groceries", None, rakuten_id),
        
        # Amazon Next Payment (11/27) Data (10/1 - 10/31)
        ("2025-10-10", "Expense", "Shopping", 5000, "Amazon Sale", None, amazon_id),
        ("2025-10-25", "Expense", "Transport", 2000, "Taxi", None, amazon_id),
        
        # Amazon Current Usage (11/1 - Now)
        ("2025-11-05", "Expense", "Shopping", 1200, "Kindle", None, amazon_id),
    ]

    print("Inserting 2025 Data (for Forecast)...")
    for date, type_, cat, amount, note, acc_id, card_id in dates_2025:
        if not db.transaction_exists(date, type_, cat, amount, note):
            db.add_transaction(date, type_, cat, amount, note, acc_id, card_id)

    print("Done!")

if __name__ == "__main__":
    seed_data()
