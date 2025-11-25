import flet as ft
from database import Database
import traceback
from datetime import datetime
import csv
from views.fixed_costs_dialog import FixedCostsDialog
from config.theme import AppTheme
from config.locales import get_text


class DashboardView(ft.UserControl):
    def __init__(self, page: ft.Page, on_edit_click=None):
        super().__init__()
        self.page = page
        self.on_edit_click = on_edit_click
        self.db = Database()
        self.current_month = datetime.now().strftime("%Y-%m")
        self.all_transactions = [] # Store all transactions for current month for filtering

    def build(self):
        self.lang = self.db.get_setting("language", "en")
        self.file_picker = ft.FilePicker(on_result=self.export_csv)
        
        self.balance_text = ft.Text(
            "¥0", 
            size=40, 
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE
        )
        
        self.month_text = ft.Text(
            self.current_month,
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE
        )

        self.total_assets_text = ft.Text(
            "¥0",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GREEN_400
        )

        self.liquid_assets_text = ft.Text(
            "¥0",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.CYAN_400
        )

        self.total_liabilities_text = ft.Text(
            "¥0",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.RED_400
        )

        self.net_assets_text = ft.Text(
            "¥0",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLUE_400
        )

        self.fixed_costs_text = ft.Text(
            "¥0",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.ORANGE_400
        )

        self.disposable_budget_text = ft.Text(
            "¥0",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.AMBER_400
        )

        self.budget_text = ft.Text(
            "Budget: ¥0 / ¥0",
            size=14,
            color=ft.colors.WHITE70
        )

        self.budget_progress = ft.ProgressBar(
            width=300,
            color=ft.colors.GREEN_400,
            bgcolor=ft.colors.WHITE24,
            value=0
        )
        
        self.set_budget_btn = ft.Container() # Placeholder for button
        
        self.next_payment_text = ft.Text(
            "None",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=AppTheme.colors["text_primary"]
        )

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

        self.transactions_list = ft.ListView(
            expand=True, 
            spacing=10, 
            padding=20,
            auto_scroll=False
        )

        self.chart_container = ft.Container(
            expand=True, 
            padding=20
        )

        return ft.Container(
            content=ft.Row(
                controls=[
                    self.file_picker,
                    # Left side: Transaction List
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self._build_header(),
                                ft.Divider(color=AppTheme.colors["divider"]),
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
                                            icon=ft.icons.EDIT,
                                            tooltip="Set Budget",
                                            icon_color=AppTheme.colors["text_secondary"],
                                            on_click=self.show_budget_dialog
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
                                ft.Column([
                                    self.budget_text,
                                    self.budget_progress,
                                    self.set_budget_btn # Add Set Budget button container
                                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                ft.Row([
                                    ft.Text("Recent Transactions", style=AppTheme.text_styles["h3"]),
                                    self.search_field
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                self.transactions_list
                            ],
                            spacing=20,
                        ),
                        expand=2, 
                        padding=10,
                    ),
                    # Right side: Chart
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Expense Analysis", style=AppTheme.text_styles["h3"]),
                                self.chart_container,
                            ],
                            spacing=20,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        expand=1, 
                        padding=20,
                        bgcolor=AppTheme.colors["surface"],
                        border_radius=10,
                    )
                ],
                expand=True,
                spacing=20,
            ),
            expand=True,
            padding=10,
        )

    def did_mount(self):
        self.load_data()

    def show_budget_dialog(self, e):
        def close_dlg(e):
            self.page.dialog.open = False
            self.page.update()

        def save_budget(e):
            try:
                amount = int(budget_input.value)
                self.db.set_budget(self.current_month, amount)
                self.load_data()
                close_dlg(e)
            except ValueError:
                pass

        current_budget = self.db.get_budget(self.current_month)
        budget_input = ft.TextField(label="Monthly Budget", value=str(current_budget), keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)

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
        dlg = FixedCostsDialog(self.page, on_dismiss=self.load_data)
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

    def prev_month(self, e):
        year, month = map(int, self.current_month.split('-'))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        self.current_month = f"{year}-{month:02d}"
        self.month_text.value = self.current_month
        self.load_data()
        self.update()

    def next_month(self, e):
        year, month = map(int, self.current_month.split('-'))
        month += 1
        if month == 13:
            month = 1
            year += 1
        self.current_month = f"{year}-{month:02d}"
        self.month_text.value = self.current_month
        self.load_data()
        self.update()

    def _build_header(self):
        # Asset Equation: Total Assets - Liabilities = Net Assets
        
        # Helper for equation cards
        def equation_card(title, value_control, color, icon):
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, color=color, size=16),
                        ft.Text(get_text(title, self.lang), size=12, color=AppTheme.colors["text_secondary"])
                    ], spacing=5),
                    value_control
                ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=AppTheme.colors["surface"],
                padding=15,
                border_radius=10,
                expand=True,
            )
        equation_row = ft.Row([
            equation_card("total_assets", self.total_assets_text, ft.colors.GREEN_400, ft.icons.ACCOUNT_BALANCE),
            ft.Icon(ft.icons.REMOVE, color=AppTheme.colors["text_secondary"], size=20),
            equation_card("liabilities", self.total_liabilities_text, ft.colors.RED_400, ft.icons.CREDIT_CARD),
            ft.Text("=", color=AppTheme.colors["text_secondary"], size=20, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET, color=AppTheme.colors["primary"], size=20),
                        ft.Text(get_text("net_assets", self.lang), size=14, color=AppTheme.colors["text_primary"], weight=ft.FontWeight.BOLD)
                    ], spacing=5),
                    self.net_assets_text
                ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=AppTheme.colors["surface"],
                padding=15,
                border_radius=10,
                expand=True,
                border=ft.border.all(1, AppTheme.colors["primary"]) # Highlight Net Assets
            ),
        ], spacing=10, alignment=ft.MainAxisAlignment.CENTER)

        # Disposable Equation: Liquid Assets - Next Payment - Fixed Costs = Disposable
        
        self.next_payment_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.WARNING_AMBER, color=AppTheme.colors["warning"], size=16),
                    ft.Text(get_text("next_payment", self.lang), size=12, color=AppTheme.colors["text_secondary"])
                ], spacing=5),
                self.next_payment_text
            ], spacing=2),
            bgcolor=AppTheme.colors["surface"],
            padding=15,
            border_radius=10,
            expand=True
        )

        disposable_row = ft.Row([
            self._build_stat_card("liquid_assets", self.liquid_assets_text, ft.icons.WATER_DROP, ft.colors.CYAN_400),
            ft.Icon(ft.icons.REMOVE, color=AppTheme.colors["text_secondary"], size=20),
            self.next_payment_card,
            ft.Icon(ft.icons.REMOVE, color=AppTheme.colors["text_secondary"], size=20),
            self._build_stat_card("fixed_costs", self.fixed_costs_text, ft.icons.REPEAT, ft.colors.ORANGE_400),
            ft.Text("=", color=AppTheme.colors["text_secondary"], size=20, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.icons.WALLET, color=ft.colors.AMBER_400, size=20),
                        ft.Text(get_text("disposable", self.lang), size=14, color=AppTheme.colors["text_primary"], weight=ft.FontWeight.BOLD)
                    ], spacing=5),
                    self.disposable_budget_text
                ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=AppTheme.colors["surface"],
                padding=15,
                border_radius=10,
                expand=True,
                border=ft.border.all(1, ft.colors.AMBER_400) # Highlight Disposable
            ),
        ], spacing=10, alignment=ft.MainAxisAlignment.CENTER)

        return ft.Column([equation_row, disposable_row], spacing=10)

    def _build_stat_card(self, title_key, value_control, icon, color):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, color=color, size=16),
                    ft.Text(get_text(title_key, self.lang), size=12, color=AppTheme.colors["text_secondary"])
                ], spacing=5),
                value_control
            ], spacing=5),
            bgcolor=AppTheme.colors["surface"],
            padding=15,
            border_radius=10,
            expand=True,
        )

    def load_data(self):
        try:
            self.all_transactions = self.db.get_transactions(self.current_month)
            # balance = self.db.get_balance(self.current_month) # Not used in new header
            total_assets = self.db.get_total_assets()
            liquid_assets = self.db.get_liquid_assets()
            total_liabilities = self.db.get_total_liabilities()
            net_assets = self.db.get_net_assets()
            
            # Calculate total expenses for budget
            total_expenses = sum(t['amount'] for t in self.all_transactions if t['type'] == 'Expense')
            
            # Check for category budgets first
            category_budgets = self.db.get_category_budgets()
            total_category_budget = sum(category_budgets.values())
            
            if total_category_budget > 0:
                budget = total_category_budget
                budget_source = "(Category Sum)"
            else:
                budget = self.db.get_budget(self.current_month)
                budget_source = ""
            
            # self.balance_text.value = f"¥{balance:,}"
            self.total_assets_text.value = f"¥{total_assets:,}"
            self.liquid_assets_text.value = f"¥{liquid_assets:,}"
            self.total_liabilities_text.value = f"¥{total_liabilities:,}"
            self.net_assets_text.value = f"¥{net_assets:,}"
            
            # Fixed Costs Calculation
            fixed_costs = self.db.get_fixed_costs()
            total_fixed_costs = sum(fc['amount'] for fc in fixed_costs)
            disposable_budget = max(0, budget - total_fixed_costs)
            
            self.fixed_costs_text.value = f"¥{total_fixed_costs:,}"
            self.disposable_budget_text.value = f"¥{disposable_budget:,}"
            
            # Update budget display
            if budget > 0:
                self.budget_progress.visible = True
                progress = min(total_expenses / budget, 1.0)
                remaining = budget - total_expenses
                self.budget_progress.value = progress
                self.budget_text.value = f"{get_text('expense', self.lang)}: ¥{total_expenses:,} / {get_text('budget', self.lang)}: ¥{budget:,} ({int(progress*100)}%) - {get_text('remaining', self.lang)}: ¥{remaining:,}"
                self.set_budget_btn.content = None
                
                if progress >= 1.0:
                    self.budget_progress.color = ft.colors.RED_400
                elif progress >= 0.8:
                    self.budget_progress.color = ft.colors.ORANGE_400
                else:
                    self.budget_progress.color = ft.colors.GREEN_400
            else:
                self.budget_progress.visible = False
                self.budget_progress.value = 0
                self.budget_text.value = get_text("set_budget_message", self.lang)
                self.set_budget_btn.content = ft.ElevatedButton(
                    get_text("set_budget", self.lang), 
                    on_click=self.show_budget_dialog,
                    style=ft.ButtonStyle(
                        color=AppTheme.colors["text_primary"],
                        bgcolor=AppTheme.colors["primary"],
                    )
                )

            # Next Payment Logic
            next_payment = self.db.get_next_payment()
            if next_payment:
                date_obj = datetime.strptime(next_payment['date'], "%Y-%m-%d")
                date_str = date_obj.strftime("%b %d")
                self.next_payment_text.value = f"{date_str}: ¥{next_payment['amount']:,}"
                
                # Alert if Liquid Assets < Next Payment
                if liquid_assets < next_payment['amount']:
                    self.next_payment_card.bgcolor = ft.colors.with_opacity(0.2, AppTheme.colors["danger"])
                    self.next_payment_card.border = ft.border.all(1, AppTheme.colors["danger"])
                else:
                    self.next_payment_card.bgcolor = AppTheme.colors["surface"]
                    self.next_payment_card.border = None
            else:
                self.next_payment_text.value = "None"
                self.next_payment_card.bgcolor = AppTheme.colors["surface"]
                self.next_payment_card.border = None

            # Initial render with all transactions (or current filter)
            self.filter_transactions(None)
            
            # Update Chart
            self.update_chart()
            
            self.update()
        except Exception:
            traceback.print_exc()

    def filter_transactions(self, e):
        query = self.search_field.value.lower() if self.search_field.value else ""
        
        filtered = []
        for t in self.all_transactions:
            if (query in t['category'].lower() or 
                query in t.get('note', '').lower() or 
                query in str(t['amount'])):
                filtered.append(t)
        
        self.transactions_list.controls.clear()
        
        if not filtered:
             self.transactions_list.controls.append(ft.Text("No transactions found", color=ft.colors.WHITE54, text_align=ft.TextAlign.CENTER))
        
        for t in filtered:
            icon = ft.icons.ADD_CIRCLE if t['type'] == 'Income' else ft.icons.REMOVE_CIRCLE
            color = ft.colors.GREEN_400 if t['type'] == 'Income' else ft.colors.RED_400
            
            self.transactions_list.controls.append(
                ft.Container(
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
                                    ft.Text(datetime.strptime(t['date'], "%Y-%m-%d").strftime("%b %d (%a)"), size=12, color=AppTheme.colors["text_secondary"]),
                                    self._get_payment_info_text(t),
                                ], spacing=2),
                            ]),
                            ft.Row([
                                ft.Text(f"¥{t['amount']:,}", size=16, weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"]),
                                ft.IconButton(
                                    icon=ft.icons.EDIT, 
                                    icon_size=20, 
                                    tooltip="Edit",
                                    icon_color=AppTheme.colors["text_secondary"],
                                    on_click=lambda e, t=t: self.on_edit_click(t) if self.on_edit_click else None
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE, 
                                    icon_size=20, 
                                    icon_color=AppTheme.colors["danger"],
                                    tooltip="Delete",
                                    on_click=lambda e, t_id=t['id']: self.delete_transaction(t_id)
                                ),
                            ])
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=10,
                    bgcolor=AppTheme.colors["surface"],
                    border_radius=10,
                    on_hover=lambda e: self.on_card_hover(e),
                )
            )
        self.transactions_list.update()

    def on_card_hover(self, e):
        e.control.bgcolor = AppTheme.colors["surface_variant"] if e.data == "true" else AppTheme.colors["surface"]
        e.control.update()


    def delete_transaction(self, transaction_id):
        def confirm_delete(e):
            self.db.delete_transaction(transaction_id)
            self.page.dialog.open = False
            self.page.update()
            self.load_data()
            snack = ft.SnackBar(ft.Text("Transaction deleted"))
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()

        def cancel_delete(e):
            self.page.dialog.open = False
            self.page.update()

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
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def update_chart(self):
        try:
            summary = self.db.get_monthly_summary(self.current_month)
            expenses = summary['expenses']
            
            if not expenses:
                self.chart_container.content = ft.Container(content=ft.Text("No expenses for this month", color=ft.colors.WHITE54), alignment=ft.alignment.center)
                self.update()
                return

            # Group small categories into "Other"
            # Top 4 categories + Other
            if len(expenses) > 5:
                top_expenses = expenses[:4]
                other_amount = sum(item['amount'] for item in expenses[4:])
                top_expenses.append({'category': get_text('other', self.lang), 'amount': other_amount})
                expenses = top_expenses
            
            total_amount = sum(item['amount'] for item in expenses)
            
            # Colors for chart (Cool Tones)
            colors = [
                ft.colors.BLUE_400, ft.colors.CYAN_400, ft.colors.TEAL_400, ft.colors.INDIGO_400,
                ft.colors.PURPLE_400, ft.colors.LIGHT_BLUE_400, ft.colors.BLUE_GREY_400,
                ft.colors.DEEP_PURPLE_400, ft.colors.CYAN_ACCENT_400, ft.colors.TEAL_ACCENT_400
            ]
            
            sections = []
            legend_items = []
            
            for i, item in enumerate(expenses):
                color = colors[i % len(colors)]
                percentage = (item['amount'] / total_amount) * 100
                
                # Create Chart Section
                sections.append(
                    ft.PieChartSection(
                        value=item['amount'],
                        title=f"{int(percentage)}%",
                        title_style=ft.TextStyle(size=12, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                        color=color,
                        radius=50, # Donut thickness
                    )
                )
                
                # Create Legend Item
                legend_items.append(
                    ft.Row([
                        ft.Container(width=12, height=12, bgcolor=color, border_radius=2),
                        ft.Text(f"{item['category']}: {int(percentage)}%", size=12, color=ft.colors.WHITE70)
                    ], spacing=5)
                )

            chart = ft.PieChart(
                sections=sections,
                sections_space=2,
                center_space_radius=40, # Hole size
                expand=True,
            )
            
            # Stack to put Total Expense in center
            chart_stack = ft.Stack([
                chart,
                ft.Container(
                    content=ft.Column([
                        ft.Text(get_text("total_expense", self.lang), size=10, color=AppTheme.colors["text_secondary"]),
                        ft.Text(f"¥{total_amount:,}", size=14, weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"])
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                )
            ], expand=True)
            
            # Layout: Chart + Legend
            self.chart_container.content = ft.Column([
                ft.Container(
                    content=chart_stack,
                    height=250, # Fixed height for chart
                ),
                ft.Container(
                    content=ft.Row(legend_items, wrap=True, spacing=10, run_spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    padding=10
                )
            ], spacing=10)
            
            self.update()
        except Exception:
            traceback.print_exc()

    def _get_payment_info_text(self, t):
        if t['type'] == 'Transfer' and t['account_name'] and t['credit_card_name']:
             # Transfer Bank -> Card (Withdrawal)
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
            # Just show Card for usage
            return ft.Row([
                ft.Icon(ft.icons.CREDIT_CARD, size=12, color=ft.colors.ORANGE_200),
                ft.Text(f"{t['credit_card_name']}", size=10, color=ft.colors.ORANGE_200)
            ], spacing=2)
        else:
            # Cash or unspecified
            return ft.Row([
                ft.Icon(ft.icons.MONEY, size=12, color=ft.colors.GREEN_200),
                ft.Text(get_text("cash", self.lang), size=10, color=ft.colors.GREEN_200)
            ], spacing=2)
