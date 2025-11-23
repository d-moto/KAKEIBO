import flet as ft
from database import Database
from datetime import datetime
import calendar

class CalendarView(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.db = Database()
        self.current_month = datetime.now().strftime("%Y-%m")
        self.calendar_grid = ft.Column(spacing=2)

    def build(self):
        self.month_text = ft.Text(
            self.current_month,
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.IconButton(icon=ft.icons.CHEVRON_LEFT, on_click=self.prev_month),
                            self.month_text,
                            ft.IconButton(icon=ft.icons.CHEVRON_RIGHT, on_click=self.next_month),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Divider(),
                    self._build_week_header(),
                    ft.Container(
                        content=self.calendar_grid,
                        expand=True,
                    )
                ],
                spacing=10,
            ),
            padding=20,
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.BLUE_GREY_900, ft.colors.BLACK],
            )
        )

    def did_mount(self):
        self.load_data()

    def _build_week_header(self):
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        return ft.Row(
            [
                ft.Container(
                    content=ft.Text(day, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE70),
                    expand=1,
                    alignment=ft.alignment.center
                ) for day in days
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

    def load_data(self):
        self.calendar_grid.controls.clear()
        
        year, month = map(int, self.current_month.split('-'))
        cal = calendar.monthcalendar(year, month)
        
        # Fetch transactions
        transactions = self.db.get_transactions(self.current_month)
        daily_expenses = {}
        for t in transactions:
            if t['type'] == 'Expense':
                day = int(t['date'].split('-')[2])
                daily_expenses[day] = daily_expenses.get(day, 0) + t['amount']

        for week in cal:
            week_row = ft.Row(spacing=2, expand=1)
            for day in week:
                if day == 0:
                    # Empty day
                    cell = ft.Container(expand=1, bgcolor=ft.colors.TRANSPARENT, height=80)
                else:
                    amount = daily_expenses.get(day, 0)
                    content_col = ft.Column(
                        [
                            ft.Text(str(day), weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2
                    )
                    
                    if amount > 0:
                        content_col.controls.append(
                            ft.Text(f"¥{amount:,}", size=12, color=ft.colors.RED_200)
                        )
                    
                    cell = ft.Container(
                        content=content_col,
                        expand=1,
                        bgcolor=ft.colors.WHITE10,
                        border_radius=5,
                        padding=5,
                        height=80,
                        alignment=ft.alignment.top_center
                    )
                week_row.controls.append(cell)
            self.calendar_grid.controls.append(week_row)
        
        self.update()

    def prev_month(self, e):
        year, month = map(int, self.current_month.split('-'))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        self.current_month = f"{year}-{month:02d}"
        self.month_text.value = self.current_month
        self.load_data()

    def next_month(self, e):
        year, month = map(int, self.current_month.split('-'))
        month += 1
        if month == 13:
            month = 1
            year += 1
        self.current_month = f"{year}-{month:02d}"
        self.month_text.value = self.current_month
        self.load_data()
