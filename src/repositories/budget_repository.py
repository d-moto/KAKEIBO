from typing import List, Dict
from core.database_manager import DatabaseManager

class BudgetRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_budget(self, month: str) -> int:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT amount FROM budgets WHERE month = ?", (month,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    def set_budget(self, month: str, amount: int):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO budgets (month, amount) VALUES (?, ?)", (month, amount))
        conn.commit()
        conn.close()

    def get_category_budgets(self) -> Dict[str, int]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT category, amount FROM category_budgets")
        rows = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}

    def set_category_budget(self, category: str, amount: int):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO category_budgets (category, amount) VALUES (?, ?)", (category, amount))
        conn.commit()
        conn.close()

    # --- Fixed Cost Methods ---
    def add_fixed_cost(self, name: str, amount: int, category: str, type: str, day_of_month: int, payment_method: str = "Cash", payment_account_id: int = None, payment_card_id: int = None):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO fixed_costs (name, amount, category, type, day_of_month, payment_method, payment_account_id, payment_card_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, amount, category, type, day_of_month, payment_method, payment_account_id, payment_card_id))
        conn.commit()
        conn.close()

    def get_fixed_costs(self) -> List[Dict]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fixed_costs")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_fixed_cost(self, fixed_cost_id: int):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fixed_costs WHERE id = ?", (fixed_cost_id,))
        conn.commit()
        conn.close()

    def update_fixed_cost(self, fixed_cost_id: int, name: str, amount: int, category: str, type: str, day_of_month: int, payment_method: str = "Cash", payment_account_id: int = None, payment_card_id: int = None):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE fixed_costs 
            SET name = ?, amount = ?, category = ?, type = ?, day_of_month = ?, payment_method = ?, payment_account_id = ?, payment_card_id = ?
            WHERE id = ?
        """, (name, amount, category, type, day_of_month, payment_method, payment_account_id, payment_card_id, fixed_cost_id))
        conn.commit()
        conn.close()

    def update_fixed_cost_last_added(self, fixed_cost_id: int, month: str):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE fixed_costs SET last_added_month = ? WHERE id = ?", (month, fixed_cost_id))
        conn.commit()
        conn.close()
