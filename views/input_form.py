import flet as ft
from database import Database
from datetime import datetime

class InputFormView(ft.UserControl):
    def __init__(self, page: ft.Page, on_save=None, transaction=None, initial_date=None):
        super().__init__()
        self.page = page
        self.on_save = on_save
        self.transaction = transaction
        self.initial_date = initial_date
        self.db = Database()

    def build(self):
        self.date_picker = ft.DatePicker(
            on_change=self.change_date,
        )
        self.page.overlay.append(self.date_picker)

        self.date_button = ft.ElevatedButton(
            "Select Date",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: self.date_picker.pick_date(),
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.BLUE_GREY_700,
            )
        )
        
        self.type_dropdown = ft.Dropdown(
            label="Type",
            options=[
                ft.dropdown.Option("Income"),
                ft.dropdown.Option("Expense"),
            ],
            width=200,
            border_color=ft.colors.WHITE54,
        )

        self.category_input = ft.TextField(
            label="Category", 
            hint_text="e.g. Salary, Food",
            border_color=ft.colors.WHITE54,
        )
        
        self.amount_input = ft.TextField(
            label="Amount", 
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=ft.colors.WHITE54,
        )
        
        self.note_input = ft.TextField(
            label="Note",
            multiline=True,
            border_color=ft.colors.WHITE54,
        )

        # Pre-fill data if editing
        if self.transaction:
            self.date_picker.value = datetime.strptime(self.transaction['date'], "%Y-%m-%d")
            self.date_button.text = self.transaction['date']
            self.type_dropdown.value = self.transaction['type']
            self.category_input.value = self.transaction['category']
            self.amount_input.value = str(self.transaction['amount'])
            self.note_input.value = self.transaction['note']
        else:
            # Use initial_date if provided, otherwise today
            if self.initial_date:
                self.date_button.text = self.initial_date
                # Try to set date picker value if valid date
                try:
                    self.date_picker.value = datetime.strptime(self.initial_date, "%Y-%m-%d")
                except:
                    pass
            else:
                self.date_button.text = datetime.now().strftime("%Y-%m-%d")
            self.type_dropdown.value = "Expense"

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Edit Transaction" if self.transaction else "Add Transaction", size=24, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    self.date_button,
                    self.type_dropdown,
                    self.category_input,
                    self.amount_input,
                    self.note_input,
                    ft.ElevatedButton(
                        "Update Transaction" if self.transaction else "Save Transaction", 
                        on_click=self.save_transaction,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.GREEN_600,
                            padding=15,
                        ),
                        width=200,
                    )
                ],
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
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
        self.date_button.text = self.date_picker.value.strftime("%Y-%m-%d")
        self.date_button.update()

    def save_transaction(self, e):
        try:
            date = self.date_button.text
            type_ = self.type_dropdown.value
            category = self.category_input.value
            amount = int(self.amount_input.value)
            note = self.note_input.value

            if not category or not amount:
                self.page.snack_bar = ft.SnackBar(ft.Text("Please fill in all fields"))
                self.page.snack_bar.open = True
                self.page.update()
                return

            if self.transaction:
                self.db.update_transaction(self.transaction['id'], date, type_, category, amount, note)
                self.page.snack_bar = ft.SnackBar(ft.Text("Transaction updated!"))
            else:
                self.db.add_transaction(date, type_, category, amount, note)
                self.page.snack_bar = ft.SnackBar(ft.Text("Transaction saved!"))
            
            self.page.snack_bar.open = True
            self.page.update()

            # Clear form if adding new
            if not self.transaction:
                self.category_input.value = ""
                self.amount_input.value = ""
                self.note_input.value = ""
                self.update()

            if self.on_save:
                self.on_save()

        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Amount must be a number"))
            self.page.snack_bar.open = True
            self.page.update()
        
        if self.on_save:
            self.on_save()
