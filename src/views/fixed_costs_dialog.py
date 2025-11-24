import flet as ft
from database import Database

class FixedCostsDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page, on_dismiss=None):
        self.page_ref = page
        self.db = Database()
        self.on_dismiss_callback = on_dismiss
        
        self.fixed_costs_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=10,
            height=300,
        )
        
        super().__init__(
            modal=True,
            title=ft.Text("Manage Fixed Costs"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Automatically add these transactions every month.", size=12, color=ft.colors.WHITE54),
                    ft.Container(
                        content=self.fixed_costs_list,
                        bgcolor=ft.colors.WHITE10,
                        border_radius=10,
                        padding=10,
                        expand=True
                    ),
                    ft.Row([
                        ft.ElevatedButton("Add New Fixed Cost", icon=ft.icons.ADD, on_click=self.show_add_form)
                    ], alignment=ft.MainAxisAlignment.END)
                ], height=400, width=500),
                padding=10
            ),
            actions=[
                ft.TextButton("Close", on_click=self.close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.load_fixed_costs()

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
                                ft.Text(fc['name'], weight=ft.FontWeight.BOLD),
                                ft.Text(f"{fc['category']} - Day {fc['day_of_month']}", size=12, color=ft.colors.WHITE54),
                                ft.Text(f"Via: {fc['payment_method'] if fc['payment_method'] else 'Cash'}", size=10, color=ft.colors.BLUE_200),
                            ]),
                            ft.Row([
                                ft.Text(f"¥{fc['amount']:,}", weight=ft.FontWeight.BOLD),
                                ft.IconButton(
                                    icon=ft.icons.DELETE, 
                                    icon_color=ft.colors.RED_400, 
                                    icon_size=20,
                                    on_click=lambda e, fc_id=fc['id']: self.delete_fixed_cost(fc_id)
                                )
                            ])
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=10,
                        bgcolor=ft.colors.GREY_900,
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
        self.page_ref.dialog = None
        self.page_ref.update()
        if self.on_dismiss_callback:
            self.on_dismiss_callback()

    def show_snack(self, message):
        snack = ft.SnackBar(ft.Text(message))
        self.page_ref.overlay.append(snack)
        snack.open = True
        self.page_ref.update()

    def show_add_form(self, e):
        # Nested dialog for adding
        def close_add_dlg(e):
            self.page_ref.dialog = self # Restore parent dialog
            self.open = True
            self.page_ref.update()

        def add_fixed_cost(e):
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

                self.db.add_fixed_cost(name, amount, category, "Expense", day, payment_method, payment_account_id, payment_card_id)
                
                # Check and add immediately if applicable
                added_count = self.db.process_fixed_costs()
                
                msg = "Fixed cost added"
                if added_count > 0:
                    msg += f" and {added_count} transaction(s) generated."
                self.show_snack(msg)
                
                self.load_fixed_costs()
                close_add_dlg(e)
                
            except ValueError:
                self.show_snack("Invalid input. Please enter numbers for Amount and Day.")

        name_input = ft.TextField(label="Name", autofocus=True)
        amount_input = ft.TextField(label="Amount", keyboard_type=ft.KeyboardType.NUMBER)
        day_input = ft.TextField(label="Day of Month (1-31)", keyboard_type=ft.KeyboardType.NUMBER)
        
        categories = self.db.get_categories("Expense")
        category_dropdown = ft.Dropdown(
            label="Category",
            options=[ft.dropdown.Option(c['name']) for c in categories],
            value=categories[0]['name'] if categories else None
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
            
        payment_method_dropdown = ft.Dropdown(
            label="Payment Method",
            options=payment_options,
            value="Cash"
        )

        add_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add Fixed Cost"),
            content=ft.Column([
                name_input,
                amount_input,
                category_dropdown,
                payment_method_dropdown,
                day_input
            ], height=350),
            actions=[
                ft.TextButton("Cancel", on_click=close_add_dlg),
                ft.TextButton("Add", on_click=add_fixed_cost),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        # We need to close self temporarily to show add_dlg if we want to avoid stacking issues, 
        # or just replace page.dialog. 
        # Flet supports only one dialog at a time in page.dialog usually, but we can switch them.
        self.open = False # Hide parent
        self.page_ref.dialog = add_dlg
        add_dlg.open = True
        self.page_ref.update()
