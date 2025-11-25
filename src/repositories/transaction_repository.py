from typing import List, Dict, Optional
from core.database_manager import DatabaseManager

class TransactionRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def add_transaction(self, date: str, type: str, category: str, amount: int, note: str = "", account_id: int = None, credit_card_id: int = None):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (date, type, category, amount, note, account_id, credit_card_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date, type, category, amount, note, account_id, credit_card_id))
        conn.commit()
        conn.close()

    def update_transaction(self, transaction_id: int, date: str, type: str, category: str, amount: int, note: str = "", account_id: int = None, credit_card_id: int = None):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE transactions 
            SET date = ?, type = ?, category = ?, amount = ?, note = ?, account_id = ?, credit_card_id = ?
            WHERE id = ?
        """, (date, type, category, amount, note, account_id, credit_card_id, transaction_id))
        conn.commit()
        conn.close()

    def delete_transaction(self, transaction_id: int):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        conn.close()

    def get_transactions(self, month: str = None) -> List[Dict]:
        conn = self.db_manager.get_connection()
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

    def transaction_exists(self, date: str, type_: str, category: str, amount: int, note: str) -> bool:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT count(*) FROM transactions 
            WHERE date = ? AND type = ? AND category = ? AND amount = ? AND note = ?
        """, (date, type_, category, amount, note))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def get_balance(self, month: str = None) -> int:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        if month:
            cursor.execute("SELECT type, amount FROM transactions WHERE date LIKE ?", (f"{month}%",))
        else:
            cursor.execute("SELECT type, amount FROM transactions")
            
        rows = cursor.fetchall()
        conn.close()

        balance = 0
        for row in rows:
            if row['type'] == "Income":
                balance += row['amount']
            elif row['type'] == "Expense":
                balance -= row['amount']
        return balance

    def get_monthly_summary(self, month: str) -> dict:
        conn = self.db_manager.get_connection()
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
    
    def get_transactions_by_date_range(self, start_date: str, end_date: str = None) -> List[Dict]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        if end_date:
            cursor.execute("""
                SELECT t.*, a.name as account_name, cc.name as credit_card_name, la.name as linked_account_name
                FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.id
                LEFT JOIN credit_cards cc ON t.credit_card_id = cc.id
                LEFT JOIN accounts la ON cc.linked_account_id = la.id
                WHERE t.date >= ? AND t.date <= ?
                ORDER BY t.date DESC, t.id DESC
            """, (start_date, end_date))
        else:
            cursor.execute("""
                SELECT t.*, a.name as account_name, cc.name as credit_card_name, la.name as linked_account_name
                FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.id
                LEFT JOIN credit_cards cc ON t.credit_card_id = cc.id
                LEFT JOIN accounts la ON cc.linked_account_id = la.id
                WHERE t.date >= ?
                ORDER BY t.date DESC, t.id DESC
            """, (start_date,))
            
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
