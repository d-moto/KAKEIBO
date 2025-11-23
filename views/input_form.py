import flet as ft
from database import Database
from datetime import datetime

class InputFormView(ft.UserControl):
    def __init__(self, page: ft.Page, on_save):
        super().__init__()
        self.page = page
        self.on_save = on_save
        self.db = Database()

    def build(self):
        self.date_picker = ft.DatePicker(
            on_change=self.change_date,
        )
        self.page.overlay.append(self.date_picker)

        self.date_button = ft.ElevatedButton(
            "Pick Date",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: self.date_picker.pick_date(),
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.WHITE10,
            )
        )
        self.selected_date_text = ft.Text(datetime.now().strftime("%Y-%m-%d"), color=ft.colors.WHITE)

        self.type_dropdown = ft.Dropdown(
            label="Type",
            options=[
                ft.dropdown.Option("Income"),
                ft.dropdown.Option("Expense"),
            ],
            value="Expense",
            border_color=ft.colors.WHITE24,
            color=ft.colors.WHITE,
        )

        self.category_field = ft.TextField(
            label="Category", 
            hint_text="e.g. Food, Salary",
            border_color=ft.colors.WHITE24,
            color=ft.colors.WHITE,
        )
        
        self.amount_field = ft.TextField(
            label="Amount", 
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=ft.colors.WHITE24,
            color=ft.colors.WHITE,
        )
        
        self.note_field = ft.TextField(
            label="Note",
            border_color=ft.colors.WHITE24,
            color=ft.colors.WHITE,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Add Transaction", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                    ft.Divider(color=ft.colors.WHITE24),
                    ft.Row([self.date_button, self.selected_date_text], alignment=ft.MainAxisAlignment.START),
                    self.type_dropdown,
                    self.category_field,
                    self.amount_field,
                    self.note_field,
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "Save Transaction",
                        on_click=self.save_transaction,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE_600,
                            color=ft.colors.WHITE,
                            padding=15,
                        ),
                        width=200,
                    )
                ],
                spacing=15,
            ),
            padding=30,
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.BLUE_GREY_900, ft.colors.BLACK],
            )
        )

    def change_date(self, e):
        if self.date_picker.value:
            self.selected_date_text.value = self.date_picker.value.strftime("%Y-%m-%d")
            self.selected_date_text.update()

    def save_transaction(self, e):
        if not self.amount_field.value:
            self.amount_field.error_text = "Amount is required"
            self.amount_field.update()
            return
        
        try:
            amount = int(self.amount_field.value)
        except ValueError:
            self.amount_field.error_text = "Must be a number"
            self.amount_field.update()
            return

        self.db.add_transaction(
            date=self.selected_date_text.value,
            type=self.type_dropdown.value,
            category=self.category_field.value,
            amount=amount,
            note=self.note_field.value
        )
        
        # Clear fields
        self.amount_field.value = ""
        self.category_field.value = ""
        self.note_field.value = ""
        self.update()
        
        if self.on_save:
            self.on_save()
