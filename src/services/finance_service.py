from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from dateutil.relativedelta import relativedelta

from repositories.transaction_repository import TransactionRepository
from repositories.budget_repository import BudgetRepository
from repositories.account_repository import AccountRepository

logger = logging.getLogger("Kakeibo")

class FinanceService:
    def __init__(self, transaction_repo: TransactionRepository, budget_repo: BudgetRepository, account_repo: AccountRepository):
        self.transaction_repo = transaction_repo
        self.budget_repo = budget_repo
        self.account_repo = account_repo

    def add_transaction(self, date: str, type: str, category: str, amount: int, note: str = "", account_id: int = None, credit_card_id: int = None):
        """Add a new transaction and handle side effects."""
        self.transaction_repo.add_transaction(date, type, category, amount, note, account_id, credit_card_id)
        
        # Handle Side Effects
        if type == "Expense" and credit_card_id:
            # Expense via Credit Card increases Liability
            self.account_repo.update_credit_card_balance(credit_card_id, amount)


    def process_fixed_costs(self) -> int:
        """Check and auto-add fixed costs. Returns number of added transactions."""
        fixed_costs = self.budget_repo.get_fixed_costs()
        
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
                    
                    self.transaction_repo.add_transaction(
                        date=date_str,
                        type=fc['type'],
                        category=fc['category'],
                        amount=fc['amount'],
                        note=f"Fixed Cost: {fc['name']}",
                        account_id=account_id,
                        credit_card_id=credit_card_id
                    )
                    
                    # Handle Side Effects
                    if fc['type'] == "Expense" and credit_card_id:
                         self.account_repo.update_credit_card_balance(credit_card_id, fc['amount'])
                    
                    # Update account balance if bank account used
                    if account_id:
                        self.account_repo.update_account_balance(account_id, -fc['amount']) # Subtracting for expense

                    # Update last added month
                    self.budget_repo.update_fixed_cost_last_added(fc['id'], current_month)
                    added_count += 1
        
        return added_count

    def calculate_next_payment(self, card_id: int, closing_day: int, withdrawal_day: int) -> Dict:
        """
        Calculate the next payment amount for a credit card based on closing and withdrawal days.
        Returns: {'payment_date': str, 'amount': int, 'period_start': str, 'period_end': str}
        """
        today = datetime.now()
        
        # 1. Determine Next Withdrawal Date
        # If today is before withdrawal day, next withdrawal is this month (if closing date allows) or next month?
        # Standard logic: Usage(M-1 Closing+1 to M Closing) -> Withdrawal(M+1 Withdrawal) or (M Withdrawal)?
        # Let's assume standard Japanese CC: Closing 15th -> Withdrawal 10th Next Month.
        # Or Closing End of Month -> Withdrawal 27th Next Month.
        
        # Let's find the relevant "Closing Date" that has just passed or is today.
        # Actually, we want to know "What is the accumulated amount for the NEXT withdrawal?"
        
        # Case A: Closing 15, Withdrawal 10 (Next Month)
        # Today: 11/25.
        # Last Closing: 11/15. Next Closing: 12/15.
        # Usage 10/16 - 11/15 -> Withdraw 12/10.
        # Usage 11/16 - 12/15 -> Withdraw 1/10.
        # So "Next Payment" is 12/10 (Amount fixed at 11/15).
        
        # Case B: Closing 31 (End), Withdrawal 27 (Next Month)
        # Today: 11/25.
        # Last Closing: 10/31. Next Closing: 11/30.
        # Usage 10/1 - 10/31 -> Withdraw 11/27.
        # If today (11/25) < 11/27, then Next Payment is 11/27 (Amount fixed at 10/31).
        # If today (11/28) > 11/27, then Next Payment is 12/27 (Amount accumulating 11/1 - 11/30).
        
        # Logic:
        # 1. Find the next withdrawal date from today.
        next_withdrawal_date = today.replace(day=withdrawal_day)
        if next_withdrawal_date < today:
             next_withdrawal_date = next_withdrawal_date + relativedelta(months=1)
             
        # 2. Determine which Closing Period corresponds to this Withdrawal Date.
        # Usually withdrawal is in the month following the closing month (or same month if closing is early and withdrawal late).
        # Let's assume "Next Month Payment" model if withdrawal_day < closing_day (e.g. Close 15, Pay 10).
        # If withdrawal_day > closing_day (e.g. Close 10, Pay 27), it might be same month?
        # Let's assume standard: Payment is usually ~1 month after closing.
        
        # We need to find the Closing Date that triggers this Next Withdrawal.
        # If Next Withdrawal is 12/10. Previous Closing was likely 11/15.
        # If Next Withdrawal is 11/27. Previous Closing was likely 10/31.
        
        # Let's iterate backwards from withdrawal date to find the most recent closing day.
        # This is heuristic but covers most cases.
        
        check_date = next_withdrawal_date - timedelta(days=1)
        while check_date.day != closing_day:
            check_date -= timedelta(days=1)
            # Safety break to prevent infinite loop if closing_day is invalid (e.g. 31 in Feb)
            # But we handle 31 as "End of Month" usually.
            if (next_withdrawal_date - check_date).days > 60:
                break
        
        closing_date = check_date
        
        # Handle "End of Month" closing (e.g. 31)
        # If user set 31, but previous month only had 30 days, check_date might have skipped it?
        # Actually, simpler logic:
        # Payment Month P. Payment Day W.
        # If W < C (Closing): Payment is for usage in P-2 to P-1. (Close P-1/C)
        # If W > C (Closing): Payment is for usage in P-1 to P. (Close P/C)? No, usually P-1.
        
        # Let's stick to: Payment is for the period ending on the most recent Closing Date before the Payment Date.
        
        # Period End = Closing Date.
        # Period Start = Previous Closing Date + 1 day.
        
        period_end = closing_date
        period_start = period_end - relativedelta(months=1) + timedelta(days=1)
        
        # Handle end of month logic for start date if needed
        # (relativedelta handles it well usually)
        
        # 3. Sum expenses in this period
        start_str = period_start.strftime("%Y-%m-%d")
        end_str = period_end.strftime("%Y-%m-%d")
        
        transactions = self.transaction_repo.get_transactions_by_date_range(start_str, end_str)
        
        amount = 0
        for t in transactions:
            if t['type'] == 'Expense' and t.get('credit_card_id') == card_id:
                amount += t['amount']
                
        return {
            'payment_date': next_withdrawal_date.strftime("%Y-%m-%d"),
            'amount': amount,
            'period_start': start_str,
            'period_end': end_str
        }

    def get_next_payment(self):
        """
        Calculates the next significant payment (Credit Card withdrawal or Fixed Cost).
        Returns a dict with 'date', 'amount', 'name'.
        """
        today = datetime.now()
        next_payment = None
        min_days_diff = float('inf')

        # 1. Check Credit Card Withdrawals
        cards = self.account_repo.get_credit_cards()
        
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
        fixed_costs = self.budget_repo.get_fixed_costs()
        
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

        return next_payment

    def get_asset_trend(self, days: int = 30) -> List[Dict]:
        """Calculate asset trend for the last N days."""
        current_assets = self.account_repo.get_total_assets()
        trend = []
        today = datetime.now().date()
        
        # Get transactions for the period that affected accounts
        start_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
        transactions = self.transaction_repo.get_transactions_by_date_range(start_date)
        
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
        today = datetime.now().date()
        # Logic to get comparison data... 
        # Since the original method in Database was cut off in view_file, I'll implement a basic version or try to read it.
        # But wait, I can just use the repository to get monthly summaries for the last N months.
        
        comparison_data = []
        for i in range(months):
            date = today - relativedelta(months=i)
            month_str = date.strftime("%Y-%m")
            summary = self.transaction_repo.get_monthly_summary(month_str)
            comparison_data.append({
                "month": month_str,
                "income": summary['total_income'],
                "expense": summary['total_expenses']
            })
            
        return list(reversed(comparison_data))

    def get_category_trend(self, category: str, months: int = 6) -> List[Dict]:
        """Get spending trend for a specific category over the last N months."""
        today = datetime.now().date()
        trend_data = []
        
        for i in range(months):
            date = today - relativedelta(months=i)
            month_str = date.strftime("%Y-%m")
            
            # Get transactions for this month and category
            # This is inefficient (N queries), but fine for small N. 
            # Ideally we'd add a method to repo to get grouped data.
            # For now, let's reuse get_monthly_summary which groups by category.
            summary = self.transaction_repo.get_monthly_summary(month_str)
            
            amount = 0
            for item in summary['expenses']:
                if item['category'] == category:
                    amount = item['amount']
                    break
            
            trend_data.append({
                "month": month_str,
                "amount": amount
            })
            
        return list(reversed(trend_data))
