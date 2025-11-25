from typing import List, Dict
from core.database_manager import DatabaseManager

class AccountRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    # --- Account Methods ---
    def add_account(self, name: str, type: str, initial_balance: int = 0, asset_type: str = "Bank", linked_account_id: int = None, linked_card_id: int = None):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO accounts (name, type, balance, asset_type, linked_account_id, linked_card_id) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, type, initial_balance, asset_type, linked_account_id, linked_card_id))
        conn.commit()
        conn.close()

    def get_accounts(self) -> List[Dict]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_account_balance(self, account_id: int, amount: int):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, account_id))
        conn.commit()
        conn.close()

    def delete_account(self, account_id: int):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        conn.commit()
        conn.close()

    def update_account(self, account_id: int, name: str, type: str, balance: int, asset_type: str, linked_account_id: int = None, linked_card_id: int = None):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE accounts 
            SET name = ?, type = ?, balance = ?, asset_type = ?, linked_account_id = ?, linked_card_id = ?
            WHERE id = ?
        """, (name, type, balance, asset_type, linked_account_id, linked_card_id, account_id))
        conn.commit()
        conn.close()

    def get_total_assets(self) -> int:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(balance) FROM accounts")
        result = cursor.fetchone()[0]
        conn.close()
        return result if result is not None else 0

    def get_total_assets_by_type(self) -> Dict[str, int]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT asset_type, SUM(balance) FROM accounts GROUP BY asset_type")
        rows = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}

    def get_liquid_assets(self) -> int:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(balance) FROM accounts WHERE asset_type IN ('Bank', 'Cash')")
        result = cursor.fetchone()[0]
        conn.close()
        return result if result is not None else 0

    # --- Credit Card Methods ---
    def add_credit_card(self, name: str, linked_account_id: int, withdrawal_day: int, closing_day: int = 31, initial_balance: int = 0):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO credit_cards (name, linked_account_id, withdrawal_day, closing_day, balance) VALUES (?, ?, ?, ?, ?)", 
                       (name, linked_account_id, withdrawal_day, closing_day, initial_balance))
        conn.commit()
        conn.close()

    def get_credit_cards(self) -> List[Dict]:
        conn = self.db_manager.get_connection()
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
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM credit_cards WHERE id = ?", (card_id,))
        conn.commit()
        conn.close()

    def update_credit_card(self, card_id: int, name: str, linked_account_id: int, withdrawal_day: int, closing_day: int):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE credit_cards 
            SET name = ?, linked_account_id = ?, withdrawal_day = ?, closing_day = ?
            WHERE id = ?
        """, (name, linked_account_id, withdrawal_day, closing_day, card_id))
        conn.commit()
        conn.close()

    def update_credit_card_balance(self, card_id: int, amount: int):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE credit_cards SET balance = balance + ? WHERE id = ?", (amount, card_id))
        conn.commit()
        conn.close()

    def get_total_liabilities(self) -> int:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(balance) FROM credit_cards")
        result = cursor.fetchone()[0]
        conn.close()
        return result if result is not None else 0
