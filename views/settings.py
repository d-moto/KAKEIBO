import flet as ft
from database import Database
from datetime import datetime
import csv

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

        self.category_budget_inputs = {} # Store references to input fields
        self.category_budgets_list = ft.Column(spacing=10)

        # Category Management UI
        self.new_category_name = ft.TextField(label="New Category Name", expand=True)
        self.new_category_type = ft.Dropdown(
            options=[
                ft.dropdown.Option("Expense"),
                ft.dropdown.Option("Income"),
            ],
            value="Expense",
            width=150
        )
        self.categories_list = ft.ListView(spacing=5, padding=10)

        self.file_picker = ft.FilePicker(on_result=self.export_csv)
        self.import_picker = ft.FilePicker(on_result=self.import_csv)
        self.page.overlay.extend([self.file_picker, self.import_picker])

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

                    # Data Management
                    ft.Text("Data Management", size=16, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.ElevatedButton(
                            "Export All Data",
                            icon=ft.icons.DOWNLOAD,
                            on_click=lambda _: self.file_picker.save_file(
                                allowed_extensions=["csv"], 
                                file_name=f"kakeibo_all_{datetime.now().strftime('%Y%m%d')}.csv"
                            ),
                            style=ft.ButtonStyle(
                                color=ft.colors.WHITE,
                                bgcolor=ft.colors.GREEN_600,
                            ),
                        ),
                        ft.ElevatedButton(
                            "Import from CSV",
                            icon=ft.icons.UPLOAD,
                            on_click=lambda _: self.import_picker.pick_files(
                                allowed_extensions=["csv"], 
                                allow_multiple=False
                            ),
                            style=ft.ButtonStyle(
                                color=ft.colors.WHITE,
                                bgcolor=ft.colors.ORANGE_600,
                            ),
                        ),
                    ]),
                    ft.Text("Importing will append data and skip duplicates.", size=12, color=ft.colors.WHITE54),

                    ft.Divider(),

                    # Category Budgets
                    ft.Text("Category Budgets (Default)", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text("Set default monthly budgets for each category.", size=12, color=ft.colors.WHITE54),
                    ft.Container(
                        content=self.category_budgets_list,
                        bgcolor=ft.colors.WHITE10,
                        border_radius=10,
                        padding=10,
                    ),
                    ft.ElevatedButton(
                        "Save Category Budgets",
                        on_click=self.save_category_budgets,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.BLUE_600,
                        ),
                    ),
                    
                    ft.Divider(),

                    # Category Management
                    ft.Text("Category Management", size=20, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        self.new_category_name,
                        self.new_category_type,
                        ft.IconButton(icon=ft.icons.ADD, on_click=self.add_category, bgcolor=ft.colors.GREEN_400, icon_color=ft.colors.WHITE)
                    ]),
                    ft.Container(
                        content=self.categories_list,
                        height=300,
                        bgcolor=ft.colors.WHITE10,
                        border_radius=10,
                        padding=0, # Padding handled by ListView
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
        self.load_category_budgets()
        self.load_categories()

    def load_category_budgets(self):
        self.category_budgets_list.controls.clear()
        self.category_budget_inputs = {}
        
        categories = self.db.get_categories("Expense")
        current_budgets = self.db.get_category_budgets()
        
        for cat in categories:
            c_name = cat['name']
            amount = current_budgets.get(c_name, 0)
            
            tf = ft.TextField(
                value=str(amount) if amount > 0 else "",
                label=c_name,
                keyboard_type=ft.KeyboardType.NUMBER,
                width=150,
                height=40,
                content_padding=10,
                text_size=14,
            )
            self.category_budget_inputs[c_name] = tf
            
            self.category_budgets_list.controls.append(
                ft.Row([
                    ft.Text(c_name, width=100),
                    tf,
                    ft.Text("¥", size=16),
                ], alignment=ft.MainAxisAlignment.START)
            )
        self.update()

    def save_category_budgets(self, e):
        try:
            for cat_name, tf in self.category_budget_inputs.items():
                val = tf.value
                if val and val.strip():
                    amount = int(val)
                    self.db.set_category_budget(cat_name, amount)
                else:
                    self.db.set_category_budget(cat_name, 0)
            
            snack = ft.SnackBar(ft.Text("Category budgets saved!"))
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()
        except ValueError:
            snack = ft.SnackBar(ft.Text("Invalid input. Please enter numbers only."))
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()

    def load_categories(self):
        self.categories_list.controls.clear()
        categories = self.db.get_categories()
        
        for cat in categories:
            self.categories_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"{cat['name']} ({cat['type']})"),
                        ft.IconButton(
                            icon=ft.icons.DELETE, 
                            icon_color=ft.colors.RED_400,
                            tooltip="Delete Category",
                            on_click=lambda e, c_id=cat['id']: self.delete_category(c_id)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=5,
                    bgcolor=ft.colors.WHITE10,
                    border_radius=5
                )
            )
        self.categories_list.update()

    def add_category(self, e):
        name = self.new_category_name.value
        type_ = self.new_category_type.value
        if name and type_:
            self.db.add_category(name, type_)
            self.new_category_name.value = ""
            self.load_categories()
            self.page.update()
            
            snack = ft.SnackBar(ft.Text(f"Category '{name}' added"))
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()

    def delete_category(self, category_id):
        def confirm_delete(e):
            self.db.delete_category(category_id)
            self.page.dialog.open = False
            self.page.update()
            self.load_categories()
            
            snack = ft.SnackBar(ft.Text("Category deleted"))
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()

        def cancel_delete(e):
            self.page.dialog.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text("Are you sure you want to delete this category?"),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

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

    def export_csv(self, e: ft.FilePickerResultEvent):
        if e.path:
            try:
                encoding = self.db.get_setting("csv_encoding", "Shift-JIS")
                transactions = self.db.get_all_transactions()
                
                with open(e.path, 'w', newline='', encoding=encoding, errors='replace') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'Date', 'Type', 'Category', 'Amount', 'Note'])
                    for t in transactions:
                        writer.writerow([t['id'], t['date'], t['type'], t['category'], t['amount'], t['note']])
                
                snack = ft.SnackBar(ft.Text(f"Exported {len(transactions)} transactions to {e.path}"))
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()
            except Exception as ex:
                snack = ft.SnackBar(ft.Text(f"Error exporting CSV: {ex}"))
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()

    def import_csv(self, e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            try:
                encoding = self.db.get_setting("csv_encoding", "Shift-JIS")
                transactions_to_import = []
                
                # Try to read with specified encoding, fallback to utf-8 if it fails
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        reader = csv.DictReader(f)
                        # Validate headers
                        required_headers = {'Date', 'Type', 'Category', 'Amount'}
                        if not required_headers.issubset(set(reader.fieldnames)):
                             # Try to be flexible with headers? For now strict.
                             raise ValueError(f"Missing required columns: {required_headers - set(reader.fieldnames)}")
                        
                        for row in reader:
                            # Basic validation
                            if not row['Date'] or not row['Amount']:
                                continue
                                
                            transactions_to_import.append({
                                'date': row['Date'],
                                'type': row['Type'],
                                'category': row['Category'],
                                'amount': int(row['Amount']),
                                'note': row.get('Note', '')
                            })
                except UnicodeDecodeError:
                    # Fallback to utf-8
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                             if not row['Date'] or not row['Amount']:
                                continue
                             transactions_to_import.append({
                                'date': row['Date'],
                                'type': row['Type'],
                                'category': row['Category'],
                                'amount': int(row['Amount']),
                                'note': row.get('Note', '')
                            })
                
                added_count = self.db.import_transactions(transactions_to_import)
                
                snack = ft.SnackBar(ft.Text(f"Imported {added_count} transactions. ({len(transactions_to_import) - added_count} skipped)"))
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()
                
            except Exception as ex:
                snack = ft.SnackBar(ft.Text(f"Error importing CSV: {ex}"))
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()
