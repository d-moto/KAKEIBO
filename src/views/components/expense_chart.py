import flet as ft
from config.theme import AppTheme
from config.locales import get_text
import logging
import traceback

logger = logging.getLogger("Kakeibo")

class ExpenseChart(ft.UserControl):
    def __init__(self, lang="en"):
        super().__init__()
        self.lang = lang
        self.chart_container = ft.Container(
            expand=True, 
            padding=20
        )

    def build(self):
        return ft.Container(
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

    def update_chart(self, expenses):
        try:
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
                        radius=45, # Donut thickness
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
                center_space_radius=95, #40, # Hole size
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
                    height=300,#250, # Fixed height for chart
                    # expand=True,
                ),
                ft.Container(
                    content=ft.Row(legend_items, wrap=True, spacing=10, run_spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    padding=10
                )
            ], spacing=10)
            
            self.update()
        except Exception as e:
            logger.error(f"Error updating chart: {e}")
            traceback.print_exc()
