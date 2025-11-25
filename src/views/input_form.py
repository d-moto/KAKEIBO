import flet as ft
from database import Database
from datetime import datetime
from config.theme import AppTheme
from config.locales import get_text
import logging

logger = logging.getLogger("Kakeibo")

class InputFormView(ft.UserControl):
    def __init__(self, page: ft.Page, db: Database, on_save=None, transaction=None, initial_date=None):
        super().__init__()
        self.page = page
        self.on_save = on_save
        self.transaction = transaction
        self.initial_date = initial_date
        self.db = db

    def build(self):
        self.lang = self.db.get_setting("language", "en")
        self.date_picker = ft.DatePicker(
            on_change=self.change_date,
        )
        
        self.date_button = ft.ElevatedButton(
            "Select Date",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: self.date_picker.pick_date(),
            style=ft.ButtonStyle(
                color=AppTheme.colors["text_primary"],
                bgcolor=AppTheme.colors["secondary"],
                shape=ft.RoundedRectangleBorder(radius=10),
            )
        )
        
        self.type_dropdown = ft.Dropdown(
            label="Type",
            options=[
                ft.dropdown.Option("Income"),
                ft.dropdown.Option("Expense"),
                ft.dropdown.Option("Transfer"),
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
            border_color=AppTheme.colors["text_secondary"],
            color=AppTheme.colors["text_primary"],
        )
        
        self.note_input = ft.TextField(
            label="Note",
            multiline=True,
            border_color=AppTheme.colors["text_secondary"],
            color=AppTheme.colors["text_primary"],
        )

        self.payment_method_dropdown = ft.Dropdown(
            label="Payment Method",
            width=200,
            border_color=ft.colors.WHITE54,
            options=[ft.dropdown.Option("Cash")],
            value="Cash",
            visible=False # Only visible for Expense
        )

        self.income_destination_dropdown = ft.Dropdown(
            label="Destination Account",
            width=200,
            border_color=ft.colors.WHITE54,
            options=[ft.dropdown.Option("Cash")],
            value="Cash",
            visible=False # Only visible for Income
        )

        self.transfer_source_dropdown = ft.Dropdown(
            label="From (Source)",
            width=200,
            border_color=ft.colors.WHITE54,
            visible=False # Only visible for Transfer
        )

        self.transfer_destination_dropdown = ft.Dropdown(
            label="To (Destination)",
            width=200,
            border_color=ft.colors.WHITE54,
            visible=False # Only visible for Transfer
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(get_text("edit_transaction", self.lang) if self.transaction else get_text("add_transaction", self.lang), style=AppTheme.text_styles["h1"]),
                    ft.Divider(color=AppTheme.colors["divider"]),
                    self.date_button,
                    self.type_dropdown,
                    ft.Row([self.category_dropdown, self.add_category_btn], alignment=ft.MainAxisAlignment.CENTER),
                    self.amount_input,
                    self.payment_method_dropdown,
                    self.income_destination_dropdown,
                    self.transfer_source_dropdown,
                    self.transfer_destination_dropdown,
                    self.note_input,
                    ft.ElevatedButton(
                        get_text("update", self.lang) if self.transaction else get_text("save", self.lang), 
                        on_click=self.save_transaction,
                        style=ft.ButtonStyle(
                            color=AppTheme.colors["text_primary"],
                            bgcolor=AppTheme.colors["success"],
                            padding=15,
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                        width=200,
                    )
                ],
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=30,
            expand=True,
            bgcolor=AppTheme.colors["surface_variant"],
            border_radius=ft.border_radius.only(top_left=15),
        )

    def did_mount(self):
        self.page.overlay.append(self.date_picker)
        self.page.update()
        
        # Initialize data
        if self.transaction:
            try:
                self.date_picker.value = datetime.strptime(self.transaction['date'], "%Y-%m-%d")
            except:
                pass
            self.date_button.text = self.transaction['date']
            self.type_dropdown.value = self.transaction['type']
            self.amount_input.value = str(self.transaction['amount'])
            self.note_input.value = self.transaction['note']
            
            self.load_categories(self.transaction['type'])
            self.category_dropdown.value = self.transaction['category']
            
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
            
        self.update()

    def will_unmount(self):
        if self.date_picker in self.page.overlay:
            self.page.overlay.remove(self.date_picker)
            self.page.update()

    def on_type_change(self, e):
        val = self.type_dropdown.value
        self.load_categories(val if val != "Transfer" else "Expense") # Use Expense categories for Transfer or create specific ones
        self.category_dropdown.value = None
        self.category_dropdown.update()
        
        self.payment_method_dropdown.visible = (val == "Expense")
        self.income_destination_dropdown.visible = (val == "Income")
        self.transfer_source_dropdown.visible = (val == "Transfer")
        self.transfer_destination_dropdown.visible = (val == "Transfer")
        
        if val == "Expense":
            self.load_payment_methods()
        elif val == "Income":
            self.load_income_destinations()
        elif val == "Transfer":
            self.load_transfer_options()
            
        self.update()

    def load_income_destinations(self):
        options = [ft.dropdown.Option(key="Cash", text="Cash (Default)")]
        accounts = self.db.get_accounts()
        for acc in accounts:
            # Allow depositing into any account type (Bank, Cash, Investment, etc.)
            options.append(ft.dropdown.Option(key=f"acc_{acc['id']}", text=f"{acc['name']} ({acc['type']})"))
        self.income_destination_dropdown.options = options

    def load_transfer_options(self):
        # Source: Banks and Cards
        source_options = [ft.dropdown.Option(key="Cash", text="Cash")]
        accounts = self.db.get_accounts()
        cards = self.db.get_credit_cards()
        
        for acc in accounts:
            if acc['type'] == 'Bank':
                source_options.append(ft.dropdown.Option(key=f"acc_{acc['id']}", text=f"{acc['name']} (¥{acc['balance']:,})"))
        
        for card in cards:
            source_options.append(ft.dropdown.Option(key=f"card_{card['id']}", text=f"{card['name']} (Card)"))
            
        self.transfer_source_dropdown.options = source_options
        
        # Destination: Investment, Stock, Savings, AND Credit Cards (for Repayment)
        dest_options = []
        for acc in accounts:
            # Allow transfer to any account type except the source itself (validation later)
            dest_options.append(ft.dropdown.Option(key=f"acc_{acc['id']}", text=f"{acc['name']} ({acc['asset_type']})"))
            
        for card in cards:
            dest_options.append(ft.dropdown.Option(key=f"card_{card['id']}", text=f"{card['name']} (Repayment)"))
            
        self.transfer_destination_dropdown.options = dest_options

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
        logger.info("Attempting to save transaction")
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
            
            if type_ == "Expense" and self.payment_method_dropdown.value and self.payment_method_dropdown.value != "Cash":
                val = self.payment_method_dropdown.value
                if val.startswith("acc_"):
                    account_id = int(val.split("_")[1])
                elif val.startswith("card_"):
                    credit_card_id = int(val.split("_")[1])

            if self.transaction:
                # Update logic is complex with transfers, for now simplistic update
                self.db.update_transaction(self.transaction['id'], date, type_, category, amount, note, account_id, credit_card_id)
                logger.info(f"Updated transaction {self.transaction['id']}")
                self.page.snack_bar = ft.SnackBar(ft.Text("Transaction updated!"))
            else:
                # Handle Transfer Logic
                if type_ == "Transfer":
                    source_val = self.transfer_source_dropdown.value
                    dest_val = self.transfer_destination_dropdown.value
                    
                    if not source_val or not dest_val:
                        raise ValueError("Please select source and destination")
                        
                    # Deduct from Source
                    if source_val.startswith("acc_"):
                        src_id = int(source_val.split("_")[1])
                        self.db.update_account_balance(src_id, -amount)
                        account_id = src_id # Record source in transaction
                    elif source_val.startswith("card_"):
                        credit_card_id = int(source_val.split("_")[1])
                        
                    # Add to Destination
                    if dest_val.startswith("acc_"):
                        dst_id = int(dest_val.split("_")[1])
                        self.db.update_account_balance(dst_id, amount)
                        note += f" [Transfer to acc_{dst_id}]"
                    elif dest_val.startswith("card_"):
                        # Repayment: Reduce Credit Card Liability
                        dst_card_id = int(dest_val.split("_")[1])
                        self.db.update_credit_card_balance(dst_card_id, -amount)
                        note += f" [Repayment to card_{dst_card_id}]"
                        credit_card_id = dst_card_id # Mark as related to this card

                    self.db.add_transaction(date, type_, category, amount, note, account_id, credit_card_id)
                    
                elif type_ == "Income":
                    dest_val = self.income_destination_dropdown.value
                    if dest_val and dest_val.startswith("acc_"):
                        acc_id = int(dest_val.split("_")[1])
                        self.db.update_account_balance(acc_id, amount)
                        account_id = acc_id
                    
                    self.db.add_transaction(date, type_, category, amount, note, account_id, credit_card_id)
                    
                else: # Expense
                    self.db.add_transaction(date, type_, category, amount, note, account_id, credit_card_id)
                    
                    # Update account balance if bank account used
                    if account_id:
                        self.db.update_account_balance(account_id, -amount)
                    # Note: Credit Card liability update is now handled inside add_transaction (side effect)
                
                self.page.snack_bar = ft.SnackBar(ft.Text("Transaction saved!"))
                logger.info("Transaction saved successfully")
            
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
        except Exception as ex:
            logger.error(f"Error saving transaction: {ex}")
            import traceback
            traceback.print_exc()
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()
