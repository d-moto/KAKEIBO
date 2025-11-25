import flet as ft
from config.theme import AppTheme
import logging

logger = logging.getLogger("Kakeibo")

class BudgetProgress(ft.UserControl):
    def __init__(self, on_set_budget):
        super().__init__()
        self.on_set_budget = on_set_budget
        
        self.budget_text = ft.Text(
            "Budget: ¥0 / ¥0",
            size=14,
            color=ft.colors.WHITE70
        )

        self.remaining_text = ft.Text(
            "Remaining: --",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE
        )

        self.budget_progress = ft.ProgressBar(
            width=300,
            color=ft.colors.GREEN_400,
            bgcolor=ft.colors.WHITE24,
            value=0
        )
        
        self.set_budget_btn = ft.IconButton(
            icon=ft.icons.EDIT,
            tooltip="Set Budget",
            icon_color=AppTheme.colors["text_secondary"],
            on_click=lambda e: self.on_set_budget(e) if self.on_set_budget else None
        )

    def build(self):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    self.remaining_text,
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([
                    self.budget_text,
                    self.set_budget_btn
                ], alignment=ft.MainAxisAlignment.CENTER),
                self.budget_progress
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=AppTheme.colors["surface"],
            padding=15,
            border_radius=10,
            margin=ft.margin.only(top=10)
        )

    def update_budget(self, living_budget, variable_expenses):
        if living_budget > 0:
            # Ensure variable_expenses is not negative (in case fixed costs > total expenses temporarily)
            variable_expenses = max(0, variable_expenses)
            
            progress = min(variable_expenses / living_budget, 1.0)
            free_money = living_budget - variable_expenses
            
            self.budget_progress.value = progress
            self.budget_text.value = f"Variable Expenses: ¥{variable_expenses:,} / ¥{living_budget:,}"
            self.remaining_text.value = f"Free Money: ¥{free_money:,}"
            
            if free_money < 0:
                self.remaining_text.color = ft.colors.RED_400
                self.budget_progress.color = ft.colors.RED_400
            elif progress >= 0.8:
                self.remaining_text.color = ft.colors.ORANGE_400
                self.budget_progress.color = ft.colors.ORANGE_400
            else:
                self.remaining_text.color = ft.colors.GREEN_400
                self.budget_progress.color = ft.colors.GREEN_400
        else:
            self.budget_progress.value = 0
            self.budget_text.value = "Living Budget: Not Set"
            self.remaining_text.value = "Free Money: --"
            self.remaining_text.color = ft.colors.GREY_400
            self.budget_progress.color = ft.colors.GREY_400
            
        self.update()
