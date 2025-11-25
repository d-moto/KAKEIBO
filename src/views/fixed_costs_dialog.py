import flet as ft
from database import Database
from config.theme import AppTheme

class FixedCostsDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page, db: Database, on_dismiss=None):
        self.page_ref = page
        self.db = db
        self.on_dismiss_callback = on_dismiss
        
        self.fixed_costs_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=10,
            height=300,
        )
        
        super().__init__(
            modal=True,
            title=ft.Text("Manage Fixed Costs", style=AppTheme.text_styles["h2"]),
            content=ft.Container(), # Placeholder, set in show_main_view
            actions=[], # Placeholder
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=AppTheme.colors["surface_variant"],
        )
        self.show_main_view()

    def show_main_view(self):
        self.title = ft.Text("Manage Fixed Costs", style=AppTheme.text_styles["h2"])
        self.content = ft.Container(
            content=ft.Column([
                ft.Text("Automatically add these transactions every month.", style=AppTheme.text_styles["body"]),
                ft.Container(
                    content=self.fixed_costs_list,
                    bgcolor=AppTheme.colors["surface"],
                    border_radius=10,
                    padding=10,
                    expand=True
                ),
                ft.Row([
                    ft.ElevatedButton(
                        "Add New Fixed Cost", 
                        icon=ft.icons.ADD, 
                        on_click=lambda e: self.show_add_view(),
                        style=ft.ButtonStyle(
                            color=AppTheme.colors["text_primary"],
                            bgcolor=AppTheme.colors["primary"],
                            shape=ft.RoundedRectangleBorder(radius=10),
                        )
                    )
                ], alignment=ft.MainAxisAlignment.END)
            ], height=400, width=500),
            padding=10
        )
        self.actions = [
            ft.TextButton("Close", on_click=self.close_dialog),
        ]
        self.load_fixed_costs()
        self.page_ref.update()

    def load_fixed_costs(self):
        self.fixed_costs_list.controls.clear()
        fixed_costs = self.db.get_fixed_costs()
        
        if not fixed_costs:
            self.fixed_costs_list.controls.append(ft.Text("No fixed costs configured.", color=ft.colors.WHITE54))
        else:
            for fc in fixed_costs:
                self.fixed_costs_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(fc['name'], weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"]),
                                ft.Text(f"{fc['category']} - Day {fc['day_of_month']}", size=12, color=AppTheme.colors["text_secondary"]),
                                ft.Text(f"Via: {fc['payment_method'] if fc['payment_method'] else 'Cash'}", size=10, color=AppTheme.colors["accent"]),
                            ]),
                            ft.Row([
                                ft.Text(f"¥{fc['amount']:,}", weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"]),
                                ft.IconButton(
                                    icon=ft.icons.DELETE, 
                                    icon_color=ft.colors.RED_400, 
                                    icon_size=20,
                                    on_click=lambda e, fc_id=fc['id']: self.delete_fixed_cost(fc_id)
                                ),
                                ft.IconButton(
                                    icon=ft.icons.EDIT, 
                                    icon_color=ft.colors.BLUE_400, 
                                    icon_size=20,
                                    on_click=lambda e, f=fc: self.show_add_view(fixed_cost=f)
                                )
                            ])
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=10,
                        bgcolor=AppTheme.colors["background"],
                        border_radius=5,
                    )
                )
        self.page_ref.update()

    def delete_fixed_cost(self, fc_id):
        self.db.delete_fixed_cost(fc_id)
        self.load_fixed_costs()
        self.show_snack("Fixed cost deleted")

    def close_dialog(self, e):
        self.open = False
        self.page_ref.update()
        if self.on_dismiss_callback:
            self.on_dismiss_callback()

    def show_snack(self, message):
        snack = ft.SnackBar(ft.Text(message))
        self.page_ref.overlay.append(snack)
        snack.open = True
        self.page_ref.update()

    def show_add_view(self, fixed_cost=None):
        def save_fixed_cost(e):
            try:
                if not name_input.value:
                    self.show_snack("Please enter a name")
                    return
                if not amount_input.value:
                    self.show_snack("Please enter an amount")
                    return
                if not day_input.value:
                    self.show_snack("Please enter a day")
                    return

                name = name_input.value
                amount = int(amount_input.value)
                category = category_dropdown.value
                day = int(day_input.value)
                
                if day < 1 or day > 31:
                    self.show_snack("Day must be between 1 and 31")
                    return

                payment_method = "Cash"
                payment_account_id = None
                payment_card_id = None
                
                val = payment_method_dropdown.value
                if val:
                    if val.startswith("acc_"):
                        payment_method = "Bank"
                        payment_account_id = int(val.split("_")[1])
                    elif val.startswith("card_"):
                        payment_method = "Credit Card"
                        payment_card_id = int(val.split("_")[1])
                    else:
                        payment_method = "Cash"

                if fixed_cost:
                    self.db.update_fixed_cost(fixed_cost['id'], name, amount, category, "Expense", day, payment_method, payment_account_id, payment_card_id)
                    self.show_snack("Fixed cost updated")
                else:
                    self.db.add_fixed_cost(name, amount, category, "Expense", day, payment_method, payment_account_id, payment_card_id)
                    # Check and add immediately if applicable (only for new ones to avoid double entry logic complexity for now)
                    added_count = self.db.process_fixed_costs()
                    msg = "Fixed cost added"
                    if added_count > 0:
                        msg += f" and {added_count} transaction(s) generated."
                    self.show_snack(msg)
                
                self.show_main_view()
                
            except ValueError:
                self.show_snack("Invalid input. Please enter numbers for Amount and Day.")

        name_input = ft.TextField(label="Name", autofocus=True, value=fixed_cost['name'] if fixed_cost else "", border_color=AppTheme.colors["text_secondary"])
        amount_input = ft.TextField(label="Amount", keyboard_type=ft.KeyboardType.NUMBER, value=str(fixed_cost['amount']) if fixed_cost else "", border_color=AppTheme.colors["text_secondary"])
        day_input = ft.TextField(label="Day of Month (1-31)", keyboard_type=ft.KeyboardType.NUMBER, value=str(fixed_cost['day_of_month']) if fixed_cost else "", border_color=AppTheme.colors["text_secondary"])
        
        categories = self.db.get_categories("Expense")
        category_dropdown = ft.Dropdown(
            label="Category",
            options=[ft.dropdown.Option(c['name']) for c in categories],
            value=fixed_cost['category'] if fixed_cost else (categories[0]['name'] if categories else None),
            border_color=AppTheme.colors["text_secondary"]
        )

        # Payment Method Dropdown
        payment_options = [ft.dropdown.Option(key="Cash", text="Cash (Default)")]
        
        # Load Banks
        accounts = self.db.get_accounts()
        for acc in accounts:
            payment_options.append(ft.dropdown.Option(key=f"acc_{acc['id']}", text=f"{acc['name']} (¥{acc['balance']:,})"))
            
        # Load Credit Cards
        cards = self.db.get_credit_cards()
        for card in cards:
            payment_options.append(ft.dropdown.Option(key=f"card_{card['id']}", text=f"{card['name']} (Card)"))
            
        initial_payment_value = "Cash"
        if fixed_cost:
            if fixed_cost['payment_account_id']:
                initial_payment_value = f"acc_{fixed_cost['payment_account_id']}"
            elif fixed_cost['payment_card_id']:
                initial_payment_value = f"card_{fixed_cost['payment_card_id']}"

        payment_method_dropdown = ft.Dropdown(
            label="Payment Method",
            options=payment_options,
            value=initial_payment_value,
            border_color=AppTheme.colors["text_secondary"]
        )

        title = "Edit Fixed Cost" if fixed_cost else "Add Fixed Cost"
        
        self.title = ft.Text(title, style=AppTheme.text_styles["h2"])
        self.content = ft.Column([
            name_input,
            amount_input,
            category_dropdown,
            payment_method_dropdown,
            day_input
        ], height=350, width=500)
        
        self.actions = [
            ft.TextButton("Cancel", on_click=lambda e: self.show_main_view()),
            ft.TextButton("Save", on_click=save_fixed_cost),
        ]
        self.page_ref.update()
