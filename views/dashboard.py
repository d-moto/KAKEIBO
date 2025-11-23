import flet as ft
from database import Database
import traceback
from datetime import datetime

import csv

class DashboardView(ft.UserControl):
    def __init__(self, page: ft.Page, on_edit_click=None):
        super().__init__()
        self.page = page
        self.on_edit_click = on_edit_click
        self.db = Database()
        self.current_month = datetime.now().strftime("%Y-%m")

    def build(self):
        self.file_picker = ft.FilePicker(on_result=self.export_csv)
        # self.page.overlay.append(self.file_picker) # Removed from overlay

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

        self.transactions_list = ft.ListView(
            expand=True, 
            spacing=10, 
            padding=20,
            auto_scroll=False
        )

        self.chart = ft.PieChart(
            sections=[],
            sections_space=0,
            center_space_radius=40,
            expand=True,
        )
        
        self.chart_container = ft.Container(
            content=self.chart,
            expand=True, 
            padding=20
        )

        # Do not call load_data() here, as the control is not mounted yet.
        # self.load_data() 

        return ft.Container(
            content=ft.Row(
                controls=[
                    self.file_picker, # Add FilePicker to the tree
                    # Left side: Transaction List
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self._build_header(),
                                ft.Divider(color=ft.colors.WHITE24),
                                ft.Row(
                                    [
                                        ft.IconButton(icon=ft.icons.CHEVRON_LEFT, on_click=self.prev_month),
                                        self.month_text,
                                        ft.IconButton(icon=ft.icons.CHEVRON_RIGHT, on_click=self.next_month),
                                        ft.IconButton(
                                            icon=ft.icons.DOWNLOAD, 
                                            tooltip="Export CSV", 
                                            on_click=lambda _: self.file_picker.save_file(allowed_extensions=["csv"], file_name=f"kakeibo_{self.current_month}.csv")
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                ft.Text("Recent Transactions", size=20, weight=ft.FontWeight.W_500, color=ft.colors.WHITE70),
                                self.transactions_list
                            ],
                            spacing=20,
                        ),
                        expand=2, # Take up 2/3 of space
                        padding=30,
                    ),
                    # Right side: Chart
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Expense Analysis", size=20, weight=ft.FontWeight.W_500, color=ft.colors.WHITE70),
                                self.chart_container,
                            ],
                            spacing=20,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        expand=1, # Take up 1/3 of space
                        padding=30,
                        bgcolor=ft.colors.WHITE10,
                        border_radius=ft.border_radius.only(top_left=20, bottom_left=20),
                    )
                ],
                expand=True,
                spacing=0,
            ),
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.BLUE_GREY_900, ft.colors.BLACK],
            )
        )

    def did_mount(self):
        self.load_data()

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
                
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Exported to {e.path} (Encoding: {encoding})"))
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error exporting CSV: {ex}"))
                self.page.snack_bar.open = True
                self.page.update()

    def prev_month(self, e):
        year, month = map(int, self.current_month.split('-'))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        self.current_month = f"{year}-{month:02d}"
        self.month_text.value = self.current_month
        self.month_text.update()
        self.load_data()

    def next_month(self, e):
        year, month = map(int, self.current_month.split('-'))
        month += 1
        if month == 13:
            month = 1
            year += 1
        self.current_month = f"{year}-{month:02d}"
        self.month_text.value = self.current_month
        self.month_text.update()
        self.load_data()

    def _build_header(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Total Balance", size=16, color=ft.colors.WHITE54),
                    self.balance_text,
                ],
                spacing=5
            ),
            padding=20,
            border_radius=15,
            bgcolor=ft.colors.WHITE10,
        )

    def load_data(self):
        try:
            balance = self.db.get_balance(self.current_month)
            self.balance_text.value = f"¥{balance:,}"
            
            transactions = self.db.get_transactions(self.current_month)
            self.transactions_list.controls = []
            
            # Calculate totals for chart
            category_totals = {}
            for t in transactions:
                if t['type'] == 'Expense':
                    cat = t['category']
                    amount = t['amount']
                    category_totals[cat] = category_totals.get(cat, 0) + amount

            # Update Chart
            if category_totals:
                self.chart.sections = []
                colors = [ft.colors.BLUE, ft.colors.RED, ft.colors.GREEN, ft.colors.YELLOW, ft.colors.PURPLE, ft.colors.ORANGE, ft.colors.TEAL, ft.colors.PINK]
                for i, (cat, amount) in enumerate(category_totals.items()):
                    self.chart.sections.append(
                        ft.PieChartSection(
                            amount,
                            title=f"{cat}\n¥{amount:,}",
                            title_style=ft.TextStyle(size=12, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                            color=colors[i % len(colors)],
                            radius=100,
                        )
                    )
                self.chart_container.content = self.chart
            else:
                self.chart_container.content = ft.Container(
                    content=ft.Text("No expenses for this month", color=ft.colors.WHITE54),
                    alignment=ft.alignment.center,
                    expand=True
                )

            for t in transactions:
                icon = ft.icons.ARROW_DOWNWARD if t['type'] == 'Expense' else ft.icons.ARROW_UPWARD
                color = ft.colors.RED_400 if t['type'] == 'Expense' else ft.colors.GREEN_400
                
                item = ft.Container(
                    content=ft.Row(
                        [
                            ft.Row([
                                ft.Container(
                                    content=ft.Icon(icon, color=color),
                                    padding=10,
                                    bgcolor=ft.colors.WHITE10,
                                    border_radius=10,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(t['category'], size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                        ft.Text(t['date'], size=12, color=ft.colors.WHITE54),
                                    ],
                                    spacing=2,
                                ),
                            ]),
                            ft.Row([
                                ft.Text(
                                    f"{'-' if t['type'] == 'Expense' else '+'}{t['amount']:,}",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=color
                                ),
                                ft.IconButton(
                                    icon=ft.icons.EDIT,
                                    icon_color=ft.colors.BLUE_400,
                                    tooltip="Edit",
                                    on_click=lambda e, t=t: self.edit_transaction(t)
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    icon_color=ft.colors.RED_400,
                                    tooltip="Delete",
                                    on_click=lambda e, t=t: self.delete_transaction(t)
                                ),
                            ])
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=15,
                    border_radius=15,
                    bgcolor=ft.colors.GREY_900,
                )
                self.transactions_list.controls.append(item)
            
            self.update()
        except Exception as e:
            traceback.print_exc()

    def edit_transaction(self, transaction):
        # This will be handled by the main app routing
        if hasattr(self, 'on_edit_click'):
            self.on_edit_click(transaction)

    def delete_transaction(self, transaction):
        def close_dlg(e):
            self.page.dialog.open = False
            self.page.update()

        def confirm_delete(e):
            self.db.delete_transaction(transaction['id'])
            close_dlg(e)
            self.load_data()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Are you sure you want to delete this transaction?\n\n{transaction['category']}: {transaction['amount']}"),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
