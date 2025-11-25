import flet as ft
from database import Database
from datetime import datetime
import calendar
from config.theme import AppTheme

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
            style=AppTheme.text_styles["h2"]
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.IconButton(icon=ft.icons.CHEVRON_LEFT, on_click=self.prev_month, icon_color=AppTheme.colors["text_primary"]),
                            self.month_text,
                            ft.IconButton(icon=ft.icons.CHEVRON_RIGHT, on_click=self.next_month, icon_color=AppTheme.colors["text_primary"]),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Divider(color=AppTheme.colors["divider"]),
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
        )

    def did_mount(self):
        self.load_data()

    def _build_week_header(self):
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        return ft.Row(
            [
                ft.Container(
                    content=ft.Text(day, weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_secondary"]),
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
        daily_data = {}
        for t in transactions:
            day = int(t['date'].split('-')[2])
            if day not in daily_data:
                daily_data[day] = {'income': 0, 'expense': 0}
            
            if t['type'] == 'Income':
                daily_data[day]['income'] += t['amount']
            elif t['type'] == 'Expense':
                daily_data[day]['expense'] += t['amount']

        for week in cal:
            week_row = ft.Row(spacing=2, expand=1)
            for day in week:
                if day == 0:
                    # Empty day
                    cell = ft.Container(expand=1, bgcolor=ft.colors.TRANSPARENT, height=80)
                else:
                    data = daily_data.get(day, {'income': 0, 'expense': 0})
                    income = data['income']
                    expense = data['expense']
                    balance = income - expense
                    
                    content_col = ft.Column(
                        [
                            ft.Text(str(day), weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0
                    )
                    
                    if income > 0:
                        content_col.controls.append(
                            ft.Text(f"+¥{income:,}", size=10, color=ft.colors.GREEN_400)
                        )
                    if expense > 0:
                        content_col.controls.append(
                            ft.Text(f"-¥{expense:,}", size=10, color=ft.colors.RED_400)
                        )
                    if income > 0 or expense > 0:
                         content_col.controls.append(
                            ft.Text(f"¥{balance:,}", size=10, color=AppTheme.colors["text_secondary"], weight=ft.FontWeight.BOLD)
                        )
                    
                    cell = ft.Container(
                        content=content_col,
                        expand=1,
                        bgcolor=AppTheme.colors["surface"],
                        border_radius=5,
                        padding=5,
                        height=90,
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
