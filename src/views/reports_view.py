import flet as ft
from database import Database
import datetime

class ReportsView(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.db = Database()
        self.comparison_chart_container = ft.Container(height=300)
        self.trend_chart_container = ft.Container(height=300)
        self.category_dropdown = ft.Dropdown(
            label="Select Category",
            width=200,
            on_change=self.on_category_change
        )

    def build(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Advanced Analysis", size=24, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    
                    # Monthly Comparison Section
                    ft.Text("Monthly Comparison (Last 6 Months)", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=self.comparison_chart_container,
                        bgcolor=ft.colors.WHITE10,
                        border_radius=10,
                        padding=20,
                    ),
                    
                    ft.Divider(),
                    
                    # Category Trend Section
                    ft.Row([
                        ft.Text("Category Spending Trend", size=18, weight=ft.FontWeight.BOLD),
                        self.category_dropdown
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Container(
                        content=self.trend_chart_container,
                        bgcolor=ft.colors.WHITE10,
                        border_radius=10,
                        padding=20,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=20,
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
        self.load_comparison_chart()
        self.load_categories()
        # Load default category trend if available
        if self.category_dropdown.options:
            self.category_dropdown.value = self.category_dropdown.options[0].key
            self.load_trend_chart(self.category_dropdown.value)

    def load_categories(self):
        categories = self.db.get_categories("Expense")
        self.category_dropdown.options = [ft.dropdown.Option(c['name']) for c in categories]
        self.update()

    def on_category_change(self, e):
        if self.category_dropdown.value:
            self.load_trend_chart(self.category_dropdown.value)

    def load_comparison_chart(self):
        data = self.db.get_monthly_comparison(months=6)
        
        if not data:
            self.comparison_chart_container.content = ft.Text("No data available", color=ft.colors.WHITE54)
            self.update()
            return

        bar_groups = []
        max_y = 0
        
        for i, item in enumerate(data):
            income = item['income']
            expense = item['expense']
            max_y = max(max_y, income, expense)
            
            max_y = max(max_y, income, expense)
            
            bar_groups.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            to_y=income,
                            color=ft.colors.GREEN_400,
                            width=20,
                            tooltip=f"{item['month']}, Income: ¥{income:,}",
                            border_radius=ft.border_radius.vertical(top=5)
                        ),
                        ft.BarChartRod(
                            to_y=expense,
                            color=ft.colors.RED_400,
                            width=20,
                            tooltip=f"{item['month']}, Expense: ¥{expense:,}",
                            border_radius=ft.border_radius.vertical(top=5)
                        ),
                    ]
                )
            )

        chart = ft.BarChart(
            bar_groups=bar_groups,
            border=ft.border.all(1, ft.colors.WHITE10),
            left_axis=ft.ChartAxis(
                labels_size=40,
                title=ft.Text("Amount", size=10),
                title_size=20,
            ),
            bottom_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(
                        value=i,
                        label=ft.Text(d['month'][5:], size=10, weight=ft.FontWeight.BOLD)
                    ) for i, d in enumerate(data)
                ],
                labels_size=20,
            ),
            tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.BLUE_GREY_900),
            max_y=max_y * 1.1,
            expand=True,
        )
        
        self.comparison_chart_container.content = chart
        self.update()

    def load_trend_chart(self, category):
        data = self.db.get_category_trend(category, months=6)
        
        if not data:
            self.trend_chart_container.content = ft.Text("No data available", color=ft.colors.WHITE54)
            self.update()
            return

        data_points = []
        max_y = 0
        
        for i, item in enumerate(data):
            amount = item['amount']
            max_y = max(max_y, amount)
            
            data_points.append(
                ft.LineChartDataPoint(
                    i, 
                    amount,
                    tooltip=f"{item['month']}\n¥{amount:,}",
                )
            )
            
        chart = ft.LineChart(
            data_series=[
                ft.LineChartData(
                    data_points=data_points,
                    stroke_width=3,
                    color=ft.colors.CYAN,
                    curved=True,
                    stroke_cap_round=True,
                    below_line_bgcolor=ft.colors.with_opacity(0.2, ft.colors.CYAN),
                )
            ],
            border=ft.border.all(1, ft.colors.WHITE10),
            left_axis=ft.ChartAxis(
                labels_size=40,
                title=ft.Text("Amount", size=10),
                title_size=20,
            ),
            bottom_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(
                        value=i,
                        label=ft.Text(d['month'][5:], size=10, weight=ft.FontWeight.BOLD)
                    ) for i, d in enumerate(data)
                ],
                labels_size=20,
            ),
            tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.BLUE_GREY_900),
            max_y=max_y * 1.1 if max_y > 0 else 1000,
            expand=True,
        )

        self.trend_chart_container.content = chart
        self.update()
