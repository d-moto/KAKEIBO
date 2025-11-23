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
            on_change=self.on_type_change,
        )

        self.category_dropdown = ft.Dropdown(
            label="Category",
            width=200,
            border_color=ft.colors.WHITE54,
        )

        self.add_category_btn = ft.IconButton(
            icon=ft.icons.ADD,
            icon_color=ft.colors.GREEN_400,
            tooltip="Add Category",
            on_click=self.show_add_category_dialog
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

        self.payment_method_dropdown = ft.Dropdown(
            label="Payment Method",
            width=200,
            border_color=ft.colors.WHITE54,
            options=[ft.dropdown.Option("Cash")],
            value="Cash",
            visible=False # Only visible for Expense
        )

        # Pre-fill data if editing
        if self.transaction:
            self.date_picker.value = datetime.strptime(self.transaction['date'], "%Y-%m-%d")
            self.date_button.text = self.transaction['date']
            self.type_dropdown.value = self.transaction['type']
            self.amount_input.value = str(self.transaction['amount'])
            self.note_input.value = self.transaction['note']
            # Load categories for the selected type and set value
            self.load_categories(self.transaction['type'])
            self.category_dropdown.value = self.transaction['category']
            
            # Set payment method visibility and value
            if self.transaction['type'] == 'Expense':
                self.payment_method_dropdown.visible = True
                self.load_payment_methods()
                if self.transaction.get('credit_card_id'):
                    self.payment_method_dropdown.value = f"card_{self.transaction['credit_card_id']}"
                elif self.transaction.get('account_id'):
                    self.payment_method_dropdown.value = f"acc_{self.transaction['account_id']}"
                else:
                    self.payment_method_dropdown.value = "Cash"
            else:
                self.payment_method_dropdown.visible = False
        else:
            # Use initial_date if provided, otherwise today
            if self.initial_date:
                self.date_button.text = self.initial_date
                try:
                    self.date_picker.value = datetime.strptime(self.initial_date, "%Y-%m-%d")
                except:
                    pass
            else:
                self.date_button.text = datetime.now().strftime("%Y-%m-%d")
            self.type_dropdown.value = "Expense"
            self.load_categories("Expense")
            self.payment_method_dropdown.visible = True
            self.load_payment_methods()

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Edit Transaction" if self.transaction else "Add Transaction", size=24, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    self.date_button,
                    self.type_dropdown,
                    ft.Row([self.category_dropdown, self.add_category_btn], alignment=ft.MainAxisAlignment.CENTER),
                    self.amount_input,
                    self.payment_method_dropdown,
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

    def on_type_change(self, e):
        self.load_categories(self.type_dropdown.value)
        self.category_dropdown.value = None
        self.category_dropdown.update()
        
        if self.type_dropdown.value == "Expense":
            self.payment_method_dropdown.visible = True
            self.load_payment_methods()
        else:
            self.payment_method_dropdown.visible = False
        self.payment_method_dropdown.update()

    def load_payment_methods(self):
        options = [ft.dropdown.Option(key="Cash", text="Cash (Default)")]
        
        # Load Banks
        accounts = self.db.get_accounts()
        for acc in accounts:
            options.append(ft.dropdown.Option(key=f"acc_{acc['id']}", text=f"{acc['name']} (¥{acc['balance']:,})"))
            
        # Load Credit Cards
        cards = self.db.get_credit_cards()
        for card in cards:
            options.append(ft.dropdown.Option(key=f"card_{card['id']}", text=f"{card['name']} (Card)"))
            
        self.payment_method_dropdown.options = options
        # self.payment_method_dropdown.update()

    def load_categories(self, type_filter):
        categories = self.db.get_categories(type_filter)
        self.category_dropdown.options = [ft.dropdown.Option(c['name']) for c in categories]
        # self.category_dropdown.update() # Cannot update here as it might not be in tree yet

    def show_add_category_dialog(self, e):
        def close_dlg(e):
            self.page.dialog.open = False
            self.page.update()

        def add_category(e):
            name = new_category_name.value
            if name:
                self.db.add_category(name, self.type_dropdown.value)
                self.load_categories(self.type_dropdown.value)
                self.category_dropdown.value = name
                self.category_dropdown.update()
                close_dlg(e)

        new_category_name = ft.TextField(label="New Category Name", autofocus=True)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add Category"),
            content=new_category_name,
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.TextButton("Add", on_click=add_category),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def change_date(self, e):
        self.date_button.text = self.date_picker.value.strftime("%Y-%m-%d")
        self.date_button.update()

    def save_transaction(self, e):
        try:
            date = self.date_button.text
            type_ = self.type_dropdown.value
            category = self.category_dropdown.value
            amount = int(self.amount_input.value)
            note = self.note_input.value

            if not category or not amount:
                self.page.snack_bar = ft.SnackBar(ft.Text("Please fill in all fields"))
                self.page.snack_bar.open = True
                self.page.update()
                return

            account_id = None
            credit_card_id = None
            
            if type_ == "Expense" and self.payment_method_dropdown.value != "Cash":
                val = self.payment_method_dropdown.value
                if val.startswith("acc_"):
                    account_id = int(val.split("_")[1])
                elif val.startswith("card_"):
                    credit_card_id = int(val.split("_")[1])

            if self.transaction:
                self.db.update_transaction(self.transaction['id'], date, type_, category, amount, note, account_id, credit_card_id)
                self.page.snack_bar = ft.SnackBar(ft.Text("Transaction updated!"))
            else:
                self.db.add_transaction(date, type_, category, amount, note, account_id, credit_card_id)
                
                # Update account balance if bank account used
                if account_id:
                    self.db.update_account_balance(account_id, -amount)
                
                self.page.snack_bar = ft.SnackBar(ft.Text("Transaction saved!"))
            
            self.page.snack_bar.open = True
            self.page.update()

            # Clear form if adding new
            if not self.transaction:
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
