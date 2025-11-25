import flet as ft
from config.theme import AppTheme
from config.locales import get_text
from datetime import datetime

class AssetSummaryCard(ft.UserControl):
    def __init__(self, on_set_savings=None, on_set_investment=None, on_period_click=None, lang="en"):
        super().__init__()
        self.lang = lang
        self.on_set_savings = on_set_savings
        self.on_set_investment = on_set_investment
        self.on_period_click = on_period_click
        
        # Initialize text controls
        self.period_text = ft.Text("", size=12, color=ft.colors.WHITE54)
        
        self.total_income_text = ft.Text("¥0", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_400)
        self.budget_text = ft.Text("¥0", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_200)
        self.surplus_text = ft.Text("¥0", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.TEAL_400)
        
        self.savings_text = ft.Text("¥0", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_400)
        self.investment_text = ft.Text("¥0", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.CYAN_400)
        self.fixed_costs_text = ft.Text("¥0", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.ORANGE_400)
        
        self.living_budget_text = ft.Text("¥0", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.AMBER_400)
        
        # Secondary info
        self.total_assets_text = ft.Text("¥0", size=12, color=ft.colors.WHITE54)

    def build(self):
        # Helper for flow cards
        def flow_card(title, value_control, color, icon, on_click=None, width=None, bgcolor=AppTheme.colors["surface"]):
            content = ft.Column([
                ft.Row([
                    ft.Icon(icon, color=color, size=16),
                    ft.Text(title, size=12, color=AppTheme.colors["text_secondary"])
                ], spacing=5),
                value_control
            ], spacing=2, alignment=ft.MainAxisAlignment.CENTER)
            
            container = ft.Container(
                content=content,
                bgcolor=bgcolor,
                padding=15,
                border_radius=10,
                width=width,
                expand=True if width is None else False,
            )
            
            if on_click:
                return ft.GestureDetector(
                    content=container,
                    on_tap=on_click,
                    mouse_cursor=ft.MouseCursor.CLICK
                )
            return container

        # Period Header
        period_header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.CALENDAR_MONTH, size=14, color=ft.colors.WHITE54),
                self.period_text
            ], alignment=ft.MainAxisAlignment.END),
            on_click=self.on_period_click,
            padding=ft.padding.only(bottom=5)
        )

        # Row 1: Total Income -> Surplus
        income_row = ft.Row([
            flow_card("Total Income", self.total_income_text, ft.colors.GREEN_400, ft.icons.ACCOUNT_BALANCE_WALLET),
            ft.Icon(ft.icons.ARROW_FORWARD, color=ft.colors.WHITE24, size=20),
            flow_card("Surplus (Income - Budget)", self.surplus_text, ft.colors.TEAL_400, ft.icons.SAVINGS, bgcolor=ft.colors.with_opacity(0.1, ft.colors.TEAL)),
        ])

        # Row 2: Budget (Planned)
        budget_row = ft.Row([
            ft.Icon(ft.icons.ARROW_DOWNWARD, color=ft.colors.WHITE24, size=20),
            flow_card("Budget (Planned)", self.budget_text, ft.colors.BLUE_200, ft.icons.ASSIGNMENT),
        ], alignment=ft.MainAxisAlignment.START) # Align start to match flow from Income

        # Row 3: Deductions (Savings, Investment, Fixed Costs)
        deductions_row = ft.Row([
            ft.Icon(ft.icons.ARROW_DOWNWARD, color=ft.colors.WHITE24, size=20),
            flow_card("Savings", self.savings_text, ft.colors.BLUE_400, ft.icons.SAVINGS, on_click=self.on_set_savings),
            flow_card("Investment", self.investment_text, ft.colors.CYAN_400, ft.icons.TRENDING_UP, on_click=self.on_set_investment),
            flow_card(get_text("fixed_costs", self.lang), self.fixed_costs_text, ft.colors.ORANGE_400, ft.icons.REPEAT),
        ], alignment=ft.MainAxisAlignment.CENTER)

        # Row 4: Result (Living Budget)
        result_row = ft.Row([
            ft.Icon(ft.icons.ARROW_DOWNWARD, color=ft.colors.WHITE24, size=20),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.icons.WALLET, color=ft.colors.AMBER_400, size=24),
                        ft.Text("Money for Living", size=16, color=AppTheme.colors["text_primary"], weight=ft.FontWeight.BOLD)
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    self.living_budget_text
                ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=AppTheme.colors["surface"],
                padding=20,
                border_radius=10,
                expand=True,
                border=ft.border.all(1, ft.colors.AMBER_400)
            ),
        ], alignment=ft.MainAxisAlignment.CENTER)

        # Secondary Info Row (Total Assets)
        secondary_row = ft.Row([
            ft.Icon(ft.icons.INFO_OUTLINE, size=12, color=ft.colors.WHITE54),
            ft.Text("Total Assets: ", size=12, color=ft.colors.WHITE54),
            self.total_assets_text
        ], alignment=ft.MainAxisAlignment.END)

        return ft.Column([
            period_header,
            income_row,
            budget_row,
            deductions_row,
            result_row,
            secondary_row
        ], spacing=10)

    def update_data(self, period_str, total_income, budget, fixed_costs, savings_goal, investment_goal, total_assets):
        self.period_text.value = f"Period: {period_str}"
        
        self.total_income_text.value = f"¥{total_income:,}"
        self.budget_text.value = f"¥{budget:,}"
        
        surplus = total_income - budget
        self.surplus_text.value = f"¥{surplus:,}"
        self.surplus_text.color = ft.colors.TEAL_400 if surplus >= 0 else ft.colors.RED_400
        
        self.fixed_costs_text.value = f"¥{fixed_costs:,}"
        self.savings_text.value = f"¥{savings_goal:,}"
        self.investment_text.value = f"¥{investment_goal:,}"
        
        living_budget = budget - fixed_costs - savings_goal - investment_goal
        self.living_budget_text.value = f"¥{living_budget:,}"
        
        self.total_assets_text.value = f"¥{total_assets:,}"
            
        self.update()
