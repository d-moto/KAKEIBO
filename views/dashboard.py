import flet as ft
from database import Database
import traceback

class DashboardView(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.db = Database()

    def build(self):
        self.balance_text = ft.Text(
            "¥0", 
            size=40, 
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE
        )
        
        self.transactions_list = ft.ListView(
            expand=True, 
            spacing=10, 
            padding=20,
            auto_scroll=False
        )

        # Do not call load_data() here, as the control is not mounted yet.
        # self.load_data() 

        return ft.Container(
            content=ft.Column(
                controls=[
                    self._build_header(),
                    ft.Divider(color=ft.colors.WHITE24),
                    ft.Text("Recent Transactions", size=20, weight=ft.FontWeight.W_500, color=ft.colors.WHITE70),
                    self.transactions_list
                ],
                spacing=20,
            ),
            padding=30,
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.BLUE_GREY_900, ft.colors.BLACK],
            )
        )

    def did_mount(self):
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
            balance = self.db.get_balance()
            self.balance_text.value = f"¥{balance:,}"
            
            transactions = self.db.get_transactions()
            self.transactions_list.controls = []
            
            for t in transactions:
                icon = ft.icons.ARROW_DOWNWARD if t['type'] == 'Expense' else ft.icons.ARROW_UPWARD
                color = ft.colors.RED_400 if t['type'] == 'Expense' else ft.colors.GREEN_400
                
                item = ft.Container(
                    content=ft.Row(
                        [
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
                                expand=True,
                                spacing=2,
                            ),
                            ft.Text(
                                f"{'-' if t['type'] == 'Expense' else '+'}{t['amount']:,}",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=color
                            )
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
