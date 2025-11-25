import flet as ft
from database import Database
from datetime import datetime
from config.theme import AppTheme


class MoneyFlowView(ft.UserControl):
    def __init__(self, page: ft.Page, db: Database):
        super().__init__()
        self.page = page
        self.db = db
        self.current_month = datetime.now().strftime("%Y-%m")
        self.chart_container = ft.Container(expand=True)
        self.month_text = ft.Text(
            self.current_month, 
            style=AppTheme.text_styles["h2"]
        )

    def build(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.icons.ARROW_BACK_IOS, 
                                on_click=self.prev_month,
                                icon_color=AppTheme.colors["text_primary"]
                            ),
                            self.month_text,
                            ft.IconButton(
                                icon=ft.icons.ARROW_FORWARD_IOS, 
                                on_click=self.next_month,
                                icon_color=AppTheme.colors["text_primary"]
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Divider(color=AppTheme.colors["divider"]),
                    self.chart_container
                ],
                expand=True,
            ),
            padding=20,
            expand=True,
        )

    def did_mount(self):
        self.load_data()

    def prev_month(self, e):
        year, month = map(int, self.current_month.split('-'))
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1
        self.current_month = f"{year}-{month:02d}"
        self.month_text.value = self.current_month
        self.load_data()
        self.update()

    def next_month(self, e):
        year, month = map(int, self.current_month.split('-'))
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
        self.current_month = f"{year}-{month:02d}"
        self.month_text.value = self.current_month
        self.load_data()
        self.update()

    def load_data(self):
        try:
            data = self.db.get_monthly_summary(self.current_month)
            
            income_list = data['income']
            expense_list = data['expenses']
            total_income = data['total_income']
            total_expenses = data['total_expenses']
            
            if total_income == 0 and total_expenses == 0:
                self.chart_container.content = ft.Container(content=ft.Text("No data for this month.", color=AppTheme.colors["text_secondary"]), alignment=ft.alignment.center)
                self.update()
                return

            savings = max(0, total_income - total_expenses)
            savings_rate = (savings / total_income * 100) if total_income > 0 else 0

            # --- Chart Data Preparation ---
            income_list.sort(key=lambda x: x['amount'], reverse=True)
            expense_list.sort(key=lambda x: x['amount'], reverse=True)

            # Colors
            income_colors = [ft.colors.GREEN_400, ft.colors.TEAL_400, ft.colors.CYAN_400, ft.colors.BLUE_400]
            expense_colors = [
                ft.colors.RED_400, ft.colors.ORANGE_400, ft.colors.AMBER_400, ft.colors.DEEP_ORANGE_400,
                ft.colors.PINK_400, ft.colors.PURPLE_400, ft.colors.INDIGO_400
            ]

            # Income Stack
            income_stack = []
            current_y = 0
            for i, item in enumerate(income_list):
                income_stack.append(
                    ft.BarChartRodStackItem(
                        from_y=current_y,
                        to_y=current_y + item['amount'],
                        color=income_colors[i % len(income_colors)],
                    )
                )
                current_y += item['amount']
            
            income_rod = ft.BarChartRod(
                to_y=total_income,
                width=60,
                rod_stack_items=income_stack,
                tooltip=f"Total Income: {total_income:,}",
                border_radius=ft.border_radius.vertical(top=5)
            )

            # Outflow Stack (Expenses + Savings)
            outflow_stack = []
            current_y = 0
            for i, item in enumerate(expense_list):
                outflow_stack.append(
                    ft.BarChartRodStackItem(
                        from_y=current_y,
                        to_y=current_y + item['amount'],
                        color=expense_colors[i % len(expense_colors)],
                    )
                )
                current_y += item['amount']
            
            if savings > 0:
                outflow_stack.append(
                    ft.BarChartRodStackItem(
                        from_y=current_y,
                        to_y=current_y + savings,
                        color=ft.colors.YELLOW_400,
                    )
                )
                current_y += savings

            outflow_rod = ft.BarChartRod(
                to_y=current_y,
                width=60,
                rod_stack_items=outflow_stack,
                tooltip=f"Total Outflow: {current_y:,}",
                border_radius=ft.border_radius.vertical(top=5)
            )

            chart = ft.BarChart(
                bar_groups=[
                    ft.BarChartGroup(x=0, bar_rods=[income_rod]),
                    ft.BarChartGroup(x=1, bar_rods=[outflow_rod]),
                ],
                bottom_axis=ft.ChartAxis(
                    labels=[
                        ft.ChartAxisLabel(value=0, label=ft.Text("Income", weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"])),
                        ft.ChartAxisLabel(value=1, label=ft.Text("Outflow", weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"])),
                    ],
                ),
                left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("Amount", color=AppTheme.colors["text_secondary"]), title_size=20),
                border=ft.border.all(1, AppTheme.colors["divider"]),
                expand=True,
                tooltip_bgcolor=AppTheme.colors["surface_variant"],
                max_y=max(total_income, current_y) * 1.1
            )

            # --- Summary Section ---
            summary_row = ft.Row([
                self._build_summary_card("Total Income", total_income, ft.colors.GREEN_400),
                self._build_summary_card("Total Expenses", total_expenses, ft.colors.RED_400),
                self._build_summary_card("Savings", savings, ft.colors.YELLOW_400, f"{savings_rate:.1f}%"),
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)

            # --- Breakdown List ---
            breakdown_items = []
            
            # Income Breakdown
            breakdown_items.append(ft.Text("Income Breakdown", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_200))
            for i, item in enumerate(income_list):
                breakdown_items.append(self._build_list_item(item, income_colors[i % len(income_colors)]))
            
            breakdown_items.append(ft.Divider(color=ft.colors.WHITE24))
            
            # Expense Breakdown
            breakdown_items.append(ft.Text("Expense Breakdown", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.RED_200))
            for i, item in enumerate(expense_list):
                breakdown_items.append(self._build_list_item(item, expense_colors[i % len(expense_colors)]))
                
            if savings > 0:
                 breakdown_items.append(self._build_list_item({'category': 'Savings', 'amount': savings}, ft.colors.YELLOW_400))

            breakdown_container = ft.Container(
                content=ft.Column(breakdown_items, scroll=ft.ScrollMode.AUTO),
                padding=20,
                bgcolor=AppTheme.colors["surface"],
                border_radius=10,
                expand=True
            )

            # Layout
            self.chart_container.content = ft.Row([
                # Left: Chart + Summary
                ft.Container(
                    content=ft.Column([
                        ft.Container(content=chart, expand=2),
                        ft.Container(content=summary_row, padding=10, bgcolor=AppTheme.colors["surface"], border_radius=10)
                    ]),
                    expand=2,
                    padding=10
                ),
                # Right: Breakdown List
                ft.Container(
                    content=breakdown_container,
                    expand=1,
                    padding=10
                )
            ], expand=True)
            
            self.update()
        except Exception:
            import traceback
            traceback.print_exc()

    def _build_summary_card(self, title, amount, color, subtext=None):
        content = [
            ft.Text(title, size=12, color=AppTheme.colors["text_secondary"]),
            ft.Text(f"¥{amount:,}", size=18, weight=ft.FontWeight.BOLD, color=color)
        ]
        if subtext:
            content.append(ft.Text(subtext, size=12, color=AppTheme.colors["text_secondary"]))
            
        return ft.Column(content, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)

    def _build_list_item(self, item, color):
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(width=10, height=10, bgcolor=color, border_radius=2),
                    ft.Text(item['category'], size=14, color=AppTheme.colors["text_primary"])
                ]),
                ft.Text(f"¥{item['amount']:,}", size=14, weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=5
        )
