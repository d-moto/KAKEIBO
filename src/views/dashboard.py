import flet as ft
from database import Database
import traceback
from datetime import datetime, timedelta
import csv
from views.fixed_costs_dialog import FixedCostsDialog
from views.components.asset_summary_card import AssetSummaryCard
from views.components.transaction_list import TransactionList
from views.components.expense_chart import ExpenseChart
from views.components.budget_progress import BudgetProgress
from config.theme import AppTheme
from config.locales import get_text
import logging

logger = logging.getLogger("Kakeibo")

from views.components.credit_card_usage import CreditCardUsage
from views.components.bank_account_summary import BankAccountSummary
from views.components.fixed_cost_list import FixedCostList

class DashboardView(ft.UserControl):
    def __init__(self, page: ft.Page, db: Database, on_edit_click=None):
        super().__init__()
        self.page = page
        self.on_edit_click = on_edit_click
        self.db = db
        self.current_month = datetime.now().strftime("%Y-%m")
        
        # Components
        self.asset_summary = AssetSummaryCard(
            on_set_savings=self.show_savings_dialog, 
            on_set_investment=self.show_investment_dialog,
            on_period_click=self.show_period_dialog
        )
        self.transaction_list = TransactionList(page, db, on_edit=self.on_edit_transaction, on_refresh=self.load_data)
        self.transaction_list.expand = True
        self.expense_chart = ExpenseChart()
        self.expense_chart.expand = True
        self.credit_card_usage = CreditCardUsage()
        self.bank_account_summary = BankAccountSummary()
        self.fixed_cost_list = FixedCostList()
        self.budget_progress = BudgetProgress(on_set_budget=self.show_budget_dialog)
        
        self.file_picker = ft.FilePicker(on_result=self.export_csv)
        self.month_text = ft.Text(
            self.current_month,
            size=20,
            weight=ft.FontWeight.BOLD,
            color=AppTheme.colors["text_primary"]
        )


    def build(self):
        self.lang = self.db.get_setting("language", "en")
        self.asset_summary.lang = self.lang
        self.expense_chart.lang = self.lang
        self.credit_card_usage.lang = self.lang
        self.bank_account_summary.lang = self.lang
        
        # Left Column Content
        left_column = ft.Column(
            controls=[
                self.asset_summary,
                ft.Divider(color=AppTheme.colors["divider"]),
                # Navigation & Actions Row
                ft.Row(
                    [
                        ft.IconButton(icon=ft.icons.CHEVRON_LEFT, on_click=self.prev_month, icon_color=AppTheme.colors["text_primary"]),
                        self.month_text,
                        ft.IconButton(icon=ft.icons.CHEVRON_RIGHT, on_click=self.next_month, icon_color=AppTheme.colors["text_primary"]),
                        ft.IconButton(
                            icon=ft.icons.DOWNLOAD, 
                            tooltip="Export CSV", 
                            icon_color=AppTheme.colors["text_secondary"],
                            on_click=lambda _: self.file_picker.save_file(allowed_extensions=["csv"], file_name=f"kakeibo_{self.current_month}.csv")
                        ),
                        ft.IconButton(
                            icon=ft.icons.CAMERA_ALT,
                            tooltip="Import from Screenshot",
                            icon_color=AppTheme.colors["text_secondary"],
                            on_click=self.show_screenshot_import_dialog
                        ),
                        ft.IconButton(
                            icon=ft.icons.REPEAT,
                            tooltip="Fixed Costs",
                            icon_color=AppTheme.colors["text_secondary"],
                            on_click=self.show_fixed_costs_dialog
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                self.budget_progress,
                self.transaction_list
            ],
            spacing=20,
            expand=True,
        )

        # Right Column Content
        right_column = ft.Column(
            controls=[
                ft.Container(content=self.expense_chart, expand=True), # Chart takes available space
                self.bank_account_summary, # Bank accounts
                self.credit_card_usage, # Usage summary below chart
                self.fixed_cost_list # Fixed Cost List
            ],
            spacing=20,
            expand=True
        )

        # Main Row
        main_row = ft.Row(
            controls=[
                ft.Container(content=left_column, expand=2, padding=10),
                ft.Container(content=right_column, expand=1, padding=10)
            ],
            expand=True,
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START
        )

        return ft.Container(
            content=main_row,
            expand=True,
            padding=20,
        )

    def did_mount(self):
        if self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)
        self.page.update()
        self.load_data()

    def _get_period_dates(self, month_str):
        # Calculate start and end date for the period based on start_day setting
        start_day = int(self.db.get_setting("start_day", "1"))
        year, month = map(int, month_str.split('-'))
        
        if start_day == 1:
            start_date = datetime(year, month, 1)
            # End date is last day of month
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        else:
            start_date = datetime(year, month, start_day)
            if month == 12:
                end_date = datetime(year + 1, 1, start_day) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, start_day) - timedelta(days=1)
                
        return start_date, end_date

    def load_data(self):
        try:
            start_date, end_date = self._get_period_dates(self.current_month)
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            period_str = f"{start_date.strftime('%m/%d')} - {end_date.strftime('%m/%d')}"
            
            # 1. Get Transactions by Range
            transactions = self.db.get_transactions_by_date_range(start_str, end_str)
            self.transaction_list.set_transactions(transactions)
            
            # 2. Calculate Financials
            total_income = sum(t['amount'] for t in transactions if t['type'] == 'Income')
            total_expense = sum(t['amount'] for t in transactions if t['type'] == 'Expense')
            
            # 3. Get Assets & Liabilities
            total_assets = self.db.get_total_assets()
            
            # 4. Get Budget & Fixed Costs & Savings/Investment Goals
            budget = self.db.get_budget(self.current_month)
            fixed_costs_total = sum(fc['amount'] for fc in self.db.get_fixed_costs())
            
            savings_goal_str = self.db.get_setting("savings_goal", "0")
            try:
                savings_goal = int(savings_goal_str)
            except ValueError:
                savings_goal = 0
                
            investment_goal_str = self.db.get_setting("investment_goal", "0")
            try:
                investment_goal = int(investment_goal_str)
            except ValueError:
                investment_goal = 0
            
            # 5. Calculate Living Budget & Variable Expenses
            living_budget = budget - fixed_costs_total - savings_goal - investment_goal
            
            # Variable Expenses = Total Expenses - Fixed Costs (Planned)
            variable_expenses = total_expense - fixed_costs_total
            
            # Update Components
            self.asset_summary.update_data(
                period_str=period_str,
                total_income=total_income,
                budget=budget,
                fixed_costs=fixed_costs_total,
                savings_goal=savings_goal,
                investment_goal=investment_goal,
                total_assets=total_assets
            )
            
            self.budget_progress.update_budget(living_budget, variable_expenses)
            
            # 6. Update Chart
            expenses = [t for t in transactions if t['type'] == 'Expense']
            # Group by category
            category_expenses = {}
            for t in expenses:
                cat = t['category']
                category_expenses[cat] = category_expenses.get(cat, 0) + t['amount']
            
            sorted_expenses = sorted(
                [{'category': k, 'amount': v} for k, v in category_expenses.items()],
                key=lambda x: x['amount'],
                reverse=True
            )
            self.expense_chart.update_chart(sorted_expenses)
            
            # 7. Update Credit Card Usage & Bank Account Summary
            credit_cards = self.db.get_credit_cards()
            card_usage = {}
            for t in expenses:
                if t.get('credit_card_id'):
                    cid = t['credit_card_id']
                    card_usage[cid] = card_usage.get(cid, 0) + t['amount']
            
            # Calculate Fixed Costs per Card and Account
            fixed_costs_card_data = {}
            fixed_costs_account_data = {}
            fixed_costs_list = self.db.get_fixed_costs()
            for fc in fixed_costs_list:
                if fc.get('payment_card_id'):
                    cid = fc['payment_card_id']
                    fixed_costs_card_data[cid] = fixed_costs_card_data.get(cid, 0) + fc['amount']
                if fc.get('payment_account_id'):
                    aid = fc['payment_account_id']
                    fixed_costs_account_data[aid] = fixed_costs_account_data.get(aid, 0) + fc['amount']
            
            # Calculate Next Payment for Credit Cards
            next_payment_data = {}
            cc_payments_account_data = {}
            
            for card in credit_cards:
                card_id = card['id']
                closing_day = card.get('closing_day', 31)
                withdrawal_day = card.get('withdrawal_day')
                linked_account_id = card.get('linked_account_id')
                
                if withdrawal_day:
                    payment_info = self.db.calculate_next_payment(card_id, closing_day, withdrawal_day)
                    if payment_info['amount'] > 0:
                        next_payment_data[card_id] = payment_info
                        
                        if linked_account_id:
                            cc_payments_account_data[linked_account_id] = cc_payments_account_data.get(linked_account_id, 0) + payment_info['amount']

            self.credit_card_usage.update_usage(credit_cards, card_usage, fixed_costs_card_data, next_payment_data)
            
            # Update Bank Account Summary
            accounts = self.db.get_accounts()
            self.bank_account_summary.update_accounts(accounts, fixed_costs_account_data, cc_payments_account_data)
            
            # Update Fixed Cost List
            self.fixed_cost_list.update_list(fixed_costs_list)
            
            self.month_text.value = self.current_month
            self.month_text.update()
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            traceback.print_exc()

    def prev_month(self, e):
        date = datetime.strptime(self.current_month, "%Y-%m")
        prev_date = date.replace(day=1) - timedelta(days=1)
        self.current_month = prev_date.strftime("%Y-%m")
        self.load_data()

    def next_month(self, e):
        date = datetime.strptime(self.current_month, "%Y-%m")
        # Add 32 days to ensure next month
        next_date = (date.replace(day=1) + timedelta(days=32)).replace(day=1)
        self.current_month = next_date.strftime("%Y-%m")
        self.load_data()

    def on_edit_transaction(self, transaction):
        if self.on_edit_click:
            self.on_edit_click(transaction)

    def show_period_dialog(self, e):
        def save_period(e):
            try:
                day = int(day_input.value)
                if 1 <= day <= 28: # Simplify to avoid 29-31 issues for now
                    self.db.set_setting("start_day", str(day))
                    self.page.dialog.open = False
                    self.page.update()
                    self.load_data()
                    snack = ft.SnackBar(ft.Text(f"Start day set to {day}"))
                    self.page.overlay.append(snack)
                    snack.open = True
                    self.page.update()
                else:
                    day_input.error_text = "Please enter a day between 1 and 28"
                    day_input.update()
            except ValueError:
                day_input.error_text = "Invalid number"
                day_input.update()

        def close_dlg(e):
            self.page.dialog.open = False
            self.page.update()

        current_day = self.db.get_setting("start_day", "1")
        day_input = ft.TextField(label="Start Day of Month (1-28)", value=current_day, keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Set Budget Period Start Day"),
            content=day_input,
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.TextButton("Save", on_click=save_period),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def show_savings_dialog(self, e):
        def save_savings(e):
            try:
                amount = int(savings_input.value)
                self.db.set_setting("savings_goal", str(amount))
                self.page.dialog.open = False
                self.page.update()
                self.load_data()
                snack = ft.SnackBar(ft.Text(f"Savings Goal set to ¥{amount:,}"))
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()
            except ValueError:
                pass

        def close_dlg(e):
            self.page.dialog.open = False
            self.page.update()

        current_savings = self.db.get_setting("savings_goal", "0")
        savings_input = ft.TextField(label="Savings Goal", value=current_savings, keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Set Monthly Savings Goal"),
            content=savings_input,
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.TextButton("Save", on_click=save_savings),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def show_investment_dialog(self, e):
        def save_investment(e):
            try:
                amount = int(investment_input.value)
                self.db.set_setting("investment_goal", str(amount))
                self.page.dialog.open = False
                self.page.update()
                self.load_data()
                snack = ft.SnackBar(ft.Text(f"Investment Goal set to ¥{amount:,}"))
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()
            except ValueError:
                pass

        def close_dlg(e):
            self.page.dialog.open = False
            self.page.update()

        current_investment = self.db.get_setting("investment_goal", "0")
        investment_input = ft.TextField(label="Investment Goal", value=current_investment, keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Set Monthly Investment Goal"),
            content=investment_input,
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.TextButton("Save", on_click=save_investment),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def show_budget_dialog(self, e):
        def save_budget(e):
            try:
                amount = int(budget_input.value)
                self.db.set_budget(self.current_month, amount)
                self.page.dialog.open = False
                self.page.update()
                self.load_data()
                snack = ft.SnackBar(ft.Text(f"Budget for {self.current_month} set to ¥{amount:,}"))
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()
            except ValueError:
                pass

        def close_dlg(e):
            self.page.dialog.open = False
            self.page.update()

        current_budget = self.db.get_budget(self.current_month)
        budget_input = ft.TextField(label="Budget Amount", value=str(current_budget), keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Set Budget for {self.current_month}"),
            content=budget_input,
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.TextButton("Save", on_click=save_budget),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def show_fixed_costs_dialog(self, e):
        dlg = FixedCostsDialog(self.page, self.db, on_dismiss=self.load_data)
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def show_screenshot_import_dialog(self, e):
        from views.components.screenshot_importer import ScreenshotImporter
        
        def on_complete():
            self.page.dialog.open = False
            self.page.update()
            self.load_data()
            snack = ft.SnackBar(ft.Text("Transactions imported successfully!"))
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()

        importer = ScreenshotImporter(self.page, self.db, on_import_complete=on_complete)
        
        dlg = ft.AlertDialog(
            content=importer,
            actions=[
                ft.TextButton("Close", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update())
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def export_csv(self, e: ft.FilePickerResultEvent):
        if e.path:
            try:
                encoding = self.db.get_setting("csv_encoding", "Shift-JIS")
                transactions = self.db.get_transactions(self.current_month)
                with open(e.path, 'w', newline='', encoding=encoding, errors='replace') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'Date', 'Type', 'Category', 'Amount', 'Note'])
                    for t in transactions:
                        writer.writerow([t['id'], t['date'], t['type'], t['category'], t['amount'], t['note']])
                
                snack = ft.SnackBar(ft.Text(f"Exported to {e.path} (Encoding: {encoding})"))
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()
            except Exception as ex:
                snack = ft.SnackBar(ft.Text(f"Error exporting CSV: {ex}"))
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()
