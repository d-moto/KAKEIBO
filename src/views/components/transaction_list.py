import flet as ft
from datetime import datetime
from config.theme import AppTheme
from config.locales import get_text
import logging

logger = logging.getLogger("Kakeibo")

class TransactionList(ft.UserControl):
    def __init__(self, page: ft.Page, db, on_edit, on_refresh):
        super().__init__()
        self.page_ref = page # Store as page_ref to avoid conflict with UserControl.page
        self.db = db
        self.on_edit = on_edit
        self.on_refresh = on_refresh
        self.all_transactions = []
        self.filtered_transactions = []
        
        self.search_field = ft.TextField(
            hint_text="Search",
            prefix_icon=ft.icons.SEARCH,
            on_change=self.filter_transactions,
            width=300,
            height=40,
            content_padding=10,
            text_size=14,
            border_radius=20,
            bgcolor=ft.colors.WHITE10,
            border_color=ft.colors.TRANSPARENT,
        )
        
        # Two columns for Income and Expense
        self.income_list = ft.Column(expand=True, spacing=10, scroll=ft.ScrollMode.AUTO)
        self.expense_list = ft.Column(expand=True, spacing=10, scroll=ft.ScrollMode.AUTO)

    def build(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([
                        ft.Text("Recent Transactions", style=AppTheme.text_styles["h3"]),
                        self.search_field
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    # Split View
                    ft.Row(
                        controls=[
                            # Income Column
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("Income", color=ft.colors.GREEN_400, weight=ft.FontWeight.BOLD),
                                    ft.Container(content=self.income_list, expand=True)
                                ], spacing=10),
                                expand=1,
                                bgcolor=ft.colors.with_opacity(0.05, ft.colors.GREEN),
                                border_radius=10,
                                padding=10,
                            ),
                            # Expense Column
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("Expense", color=ft.colors.RED_400, weight=ft.FontWeight.BOLD),
                                    ft.Container(content=self.expense_list, expand=True)
                                ], spacing=10),
                                expand=1,
                                bgcolor=ft.colors.with_opacity(0.05, ft.colors.RED),
                                border_radius=10,
                                padding=10,
                            )
                        ],
                        expand=True,
                        spacing=20,
                        vertical_alignment=ft.CrossAxisAlignment.START
                    )
                ],
                spacing=20,
                expand=True,
            ),
            expand=True, 
            padding=10,
        )

    def set_transactions(self, transactions):
        self.all_transactions = transactions
        self.filter_transactions(None)

    def filter_transactions(self, e):
        query = self.search_field.value.lower() if self.search_field.value else ""
        
        self.filtered_transactions = []
        for t in self.all_transactions:
            if (query in t['category'].lower() or 
                query in t.get('note', '').lower() or 
                query in str(t['amount'])):
                self.filtered_transactions.append(t)
        
        self.income_list.controls.clear()
        self.expense_list.controls.clear()
        
        income_items = [t for t in self.filtered_transactions if t['type'] == 'Income']
        expense_items = [t for t in self.filtered_transactions if t['type'] == 'Expense']

        if not income_items:
             self.income_list.controls.append(ft.Text("No income", color=ft.colors.WHITE54, text_align=ft.TextAlign.CENTER))
        
        if not expense_items:
             self.expense_list.controls.append(ft.Text("No expenses", color=ft.colors.WHITE54, text_align=ft.TextAlign.CENTER))
        
        for t in income_items:
            self.income_list.controls.append(self._create_transaction_card(t))
            
        for t in expense_items:
            self.expense_list.controls.append(self._create_transaction_card(t))
            
        self.update()

    def _create_transaction_card(self, t):
        icon = ft.icons.ADD_CIRCLE if t['type'] == 'Income' else ft.icons.REMOVE_CIRCLE
        color = ft.colors.GREEN_400 if t['type'] == 'Income' else ft.colors.RED_400
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(icon, color=color, size=24),
                            padding=10,
                            bgcolor=ft.colors.with_opacity(0.1, color),
                            border_radius=10,
                        ),
                        ft.Column([
                            ft.Text(t['category'], weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"]),
                            ft.Text(datetime.strptime(t['date'], "%Y-%m-%d").strftime("%b %d"), size=12, color=AppTheme.colors["text_secondary"]),
                            self._get_payment_info_text(t),
                        ], spacing=2),
                    ]),
                    ft.Column([
                        ft.Text(f"¥{t['amount']:,}", size=14, weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"]),
                        ft.Row([
                            ft.IconButton(
                                icon=ft.icons.EDIT, 
                                icon_size=18, 
                                tooltip="Edit",
                                icon_color=AppTheme.colors["text_secondary"],
                                on_click=lambda e, t=t: self.on_edit(t) if self.on_edit else None
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE, 
                                icon_size=18, 
                                icon_color=AppTheme.colors["danger"],
                                tooltip="Delete",
                                on_click=lambda e, t_id=t['id']: self.delete_transaction(t_id)
                            ),
                        ], spacing=0)
                    ], horizontal_alignment=ft.CrossAxisAlignment.END)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=10,
            bgcolor=AppTheme.colors["surface"],
            border_radius=10,
            on_hover=lambda e: self.on_card_hover(e),
        )

    def on_card_hover(self, e):
        e.control.bgcolor = AppTheme.colors["surface_variant"] if e.data == "true" else AppTheme.colors["surface"]
        e.control.update()

    def delete_transaction(self, transaction_id):
        def confirm_delete(e):
            logger.info(f"Deleting transaction {transaction_id}")
            self.db.delete_transaction(transaction_id)
            self.page_ref.dialog.open = False
            self.page_ref.update()
            self.on_refresh() # Reload data in parent
            snack = ft.SnackBar(ft.Text("Transaction deleted"))
            self.page_ref.overlay.append(snack)
            snack.open = True
            self.page_ref.update()

        def cancel_delete(e):
            self.page_ref.dialog.open = False
            self.page_ref.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text("Are you sure you want to delete this transaction?"),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page_ref.dialog = dlg
        dlg.open = True
        self.page_ref.update()

    def _get_payment_info_text(self, t):
        # Helper to format payment info
        if t['type'] == 'Transfer' and t['account_name'] and t['credit_card_name']:
             return ft.Row([
                ft.Icon(ft.icons.ACCOUNT_BALANCE, size=12, color=ft.colors.BLUE_200),
                ft.Text(f"{t['account_name']}", size=10, color=ft.colors.BLUE_200),
                ft.Icon(ft.icons.ARROW_FORWARD, size=10, color=AppTheme.colors["text_secondary"]),
                ft.Icon(ft.icons.CREDIT_CARD, size=12, color=ft.colors.ORANGE_200),
                ft.Text(f"{t['credit_card_name']}", size=10, color=ft.colors.ORANGE_200)
            ], spacing=2)
        elif t['account_name']:
            return ft.Row([
                ft.Icon(ft.icons.ACCOUNT_BALANCE, size=12, color=ft.colors.BLUE_200),
                ft.Text(f"{t['account_name']}", size=10, color=ft.colors.BLUE_200)
            ], spacing=2)
        elif t['credit_card_name']:
            return ft.Row([
                ft.Icon(ft.icons.CREDIT_CARD, size=12, color=ft.colors.ORANGE_200),
                ft.Text(f"{t['credit_card_name']}", size=10, color=ft.colors.ORANGE_200)
            ], spacing=2)
        else:
            return ft.Row([
                ft.Icon(ft.icons.MONEY, size=12, color=ft.colors.GREEN_200),
                ft.Text("Cash", size=10, color=ft.colors.GREEN_200)
            ], spacing=2)
