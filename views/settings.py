import flet as ft
from database import Database

class SettingsView(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.db = Database()

    def build(self):
        current_encoding = self.db.get_setting("csv_encoding", "Shift-JIS")

        self.encoding_dropdown = ft.Dropdown(
            label="CSV Encoding",
            options=[
                ft.dropdown.Option("Shift-JIS"),
                ft.dropdown.Option("utf-8"),
                ft.dropdown.Option("utf-8-sig"),
            ],
            value=current_encoding,
            width=200,
            border_color=ft.colors.WHITE54,
        )

        self.fixed_costs_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=10,
            height=300,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    
                    # CSV Settings
                    ft.Text("CSV Export Settings", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text("Select the encoding for CSV files. Use 'Shift-JIS' for Excel on Windows.", size=12, color=ft.colors.WHITE54),
                    self.encoding_dropdown,
                    ft.ElevatedButton(
                        "Save Settings",
                        on_click=self.save_settings,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.BLUE_600,
                            padding=15,
                        ),
                        width=200,
                    ),
                    
                    ft.Divider(),

                    # Fixed Costs Settings
                    ft.Row([
                        ft.Text("Fixed Costs (Recurring)", size=16, weight=ft.FontWeight.BOLD),
                        ft.IconButton(icon=ft.icons.ADD_CIRCLE, icon_color=ft.colors.GREEN_400, on_click=self.show_add_fixed_cost_dialog, tooltip="Add Fixed Cost")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text("Automatically add these transactions every month.", size=12, color=ft.colors.WHITE54),
                    
                    ft.Container(
                        content=self.fixed_costs_list,
                        bgcolor=ft.colors.WHITE10,
                        border_radius=10,
                        padding=10,
                    )
                ],
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=30,
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.BLUE_GREY_900, ft.colors.BLACK],
            )
        )

    def did_mount(self):
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
        self.update()

    def delete_fixed_cost(self, fc_id):
        self.db.delete_fixed_cost(fc_id)
        self.load_fixed_costs()
        snack = ft.SnackBar(ft.Text("Fixed cost deleted"))
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def show_add_fixed_cost_dialog(self, e):
        def close_dlg(e):
            self.page.dialog.open = False
            self.page.update()

        def add_fixed_cost(e):
            try:
                if not name_input.value:
                    snack = ft.SnackBar(ft.Text("Please enter a name"))
                    self.page.overlay.append(snack)
                    snack.open = True
                    self.page.update()
                    return

                if not amount_input.value:
                    snack = ft.SnackBar(ft.Text("Please enter an amount"))
                    self.page.overlay.append(snack)
                    snack.open = True
                    self.page.update()
                    return

                if not day_input.value:
                    snack = ft.SnackBar(ft.Text("Please enter a day"))
                    self.page.overlay.append(snack)
                    snack.open = True
                    self.page.update()
                    return

                name = name_input.value
                amount = int(amount_input.value)
                category = category_dropdown.value
                day = int(day_input.value)
                
                if day < 1 or day > 31:
                    snack = ft.SnackBar(ft.Text("Day must be between 1 and 31"))
                    self.page.overlay.append(snack)
                    snack.open = True
                    self.page.update()
                    return

                self.db.add_fixed_cost(name, amount, category, "Expense", day)
                self.load_fixed_costs()
                
                # Check and add immediately if applicable
                added_count = self.db.process_fixed_costs()
                
                close_dlg(e)
                msg = "Fixed cost added"
                if added_count > 0:
                    msg += f" and {added_count} transaction(s) generated."
                
                snack = ft.SnackBar(ft.Text(msg))
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()
            except ValueError:
                snack = ft.SnackBar(ft.Text("Invalid input. Please enter numbers for Amount and Day."))
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()

        name_input = ft.TextField(label="Name", autofocus=True)
        amount_input = ft.TextField(label="Amount", keyboard_type=ft.KeyboardType.NUMBER)
        day_input = ft.TextField(label="Day of Month (1-31)", keyboard_type=ft.KeyboardType.NUMBER)
        
        # Load categories for dropdown
        categories = self.db.get_categories("Expense")
        category_dropdown = ft.Dropdown(
            label="Category",
            options=[ft.dropdown.Option(c['name']) for c in categories],
            value=categories[0]['name'] if categories else None
        )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add Fixed Cost"),
            content=ft.Column([
                name_input,
                amount_input,
                category_dropdown,
                day_input
            ], height=300),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.TextButton("Add", on_click=add_fixed_cost),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def save_settings(self, e):
        encoding = self.encoding_dropdown.value
        self.db.set_setting("csv_encoding", encoding)
        snack = ft.SnackBar(ft.Text("Settings saved!"))
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
