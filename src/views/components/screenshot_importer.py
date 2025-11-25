import flet as ft
from database import Database
from services.ocr_service import OCRService
from config.theme import AppTheme
import datetime

class ScreenshotImporter(ft.UserControl):
    def __init__(self, page: ft.Page, db: Database, on_import_complete=None):
        super().__init__()
        self.page = page
        self.db = db
        self.on_import_complete = on_import_complete
        self.ocr_service = None
        self.imported_data = []
        self.accounts = []
        self.credit_cards = []
        
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Date")),
                ft.DataColumn(ft.Text("Type")),
                ft.DataColumn(ft.Text("Category")),
                ft.DataColumn(ft.Text("Amount")),
                ft.DataColumn(ft.Text("Payment")),
                ft.DataColumn(ft.Text("Note")),
                ft.DataColumn(ft.Text("Action")),
            ],
            rows=[]
        )
        
        # Wrap table in a scrollable Row (Horizontal) AND Column (Vertical)
        self.scrollable_table = ft.Column(
            controls=[
                ft.Row(
                    controls=[self.data_table],
                    scroll=ft.ScrollMode.ALWAYS, # Horizontal Scroll
                )
            ],
            scroll=ft.ScrollMode.ALWAYS, # Vertical Scroll
            height=400, # Fixed height to ensure vertical scrolling within view
        )

        self.table_container = ft.Container(
            content=self.scrollable_table,
            border=ft.border.all(1, AppTheme.colors["divider"]),
            border_radius=10,
            padding=10,
            visible=False,
            # Removed fixed width to allow expansion
        )
        self.status_text = ft.Text("", color=ft.colors.RED)
        self.import_btn = ft.ElevatedButton(
            "Import Selected", 
            on_click=self.import_data, 
            disabled=True,
            style=ft.ButtonStyle(bgcolor=AppTheme.colors["success"], color=AppTheme.colors["text_primary"])
        )

    def did_mount(self):
        self.page.overlay.append(self.file_picker)
        self.page.update()
        # Pre-fetch accounts and cards
        self.accounts = self.db.get_accounts()
        self.credit_cards = self.db.get_credit_cards()

    def build(self):
        return ft.Container(
            content=ft.Column([
                ft.Text("Import from Screenshot", style=AppTheme.text_styles["h2"]),
                ft.Text("Upload a receipt or transaction history screenshot. Gemini AI will extract the data.", size=12, color=AppTheme.colors["text_secondary"]),
                ft.ElevatedButton(
                    "Select Image", 
                    icon=ft.icons.IMAGE, 
                    on_click=lambda _: self.file_picker.pick_files(allow_multiple=False, allowed_extensions=["png", "jpg", "jpeg"]),
                    style=ft.ButtonStyle(bgcolor=AppTheme.colors["primary"], color=AppTheme.colors["text_primary"])
                ),
                self.status_text,
                self.table_container,
                self.import_btn
            ], spacing=20),
            padding=20,
            bgcolor=AppTheme.colors["surface"],
            border_radius=10,
        )

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return

        api_key = self.db.get_setting("gemini_api_key", "")
        if not api_key:
            self.status_text.value = "Please set your Gemini API Key in Settings first."
            self.status_text.update()
            return

        self.status_text.value = "Analyzing image... This may take a few seconds."
        self.status_text.color = AppTheme.colors["text_primary"]
        self.status_text.update()

        try:
            if not self.ocr_service:
                self.ocr_service = OCRService(api_key)
            
            file_path = e.files[0].path
            data = self.ocr_service.analyze_image(file_path)
            
            if not data:
                self.status_text.value = "No transaction data found in the image."
                self.status_text.color = ft.colors.RED
            else:
                self.imported_data = data
                self.populate_table(data)
                self.status_text.value = f"Found {len(data)} transactions. Please verify before importing."
                self.status_text.color = ft.colors.GREEN
                self.table_container.visible = True
                self.import_btn.disabled = False
                
        except Exception as ex:
            self.status_text.value = f"Error: {str(ex)}"
            self.status_text.color = ft.colors.RED
        
        self.update()

    def populate_table(self, data):
        self.data_table.rows.clear()
        all_categories = self.db.get_categories()
        
        # Prepare Payment Options
        payment_options = [ft.dropdown.Option("Cash", "Cash")]
        for acc in self.accounts:
            payment_options.append(ft.dropdown.Option(f"account_{acc['id']}", f"{acc['name']} (Bank)"))
        for card in self.credit_cards:
            payment_options.append(ft.dropdown.Option(f"card_{card['id']}", f"{card['name']} (Card)"))

        for i, item in enumerate(data):
            # Default values
            date_val = item.get('date', datetime.datetime.now().strftime("%Y-%m-%d"))
            amount_val = str(item.get('amount', 0))
            note_val = item.get('description', '') # Keep description in Note
            type_val = item.get('type', 'Expense')
            
            # Smart Category Default
            filtered_cats = [c['name'] for c in all_categories if c['type'] == type_val]
            if not filtered_cats:
                 filtered_cats = [c['name'] for c in all_categories] # Fallback
            
            # Default to "Other" if exists, else first one
            category_val = filtered_cats[0] if filtered_cats else "Uncategorized"
            if "Other" in filtered_cats:
                category_val = "Other"
            
            # Payment Method Guessing (Simple for now)
            payment_val = "Cash"

            # Create editable cells - WIDER WIDTHS
            date_field = ft.TextField(value=date_val, width=110, text_size=13)
            amount_field = ft.TextField(value=amount_val, width=90, text_size=13, keyboard_type=ft.KeyboardType.NUMBER)
            note_field = ft.TextField(value=note_val, width=400, text_size=13) # Increased from 300
            
            payment_dropdown = ft.Dropdown(
                options=payment_options,
                value=payment_val,
                width=180, # Slightly reduced to fit better
                text_size=13,
                border_color=AppTheme.colors["secondary"], # Fixed: Use valid color key
                border_radius=5,
            )
            
            type_dropdown = ft.Dropdown(
                options=[ft.dropdown.Option("Expense"), ft.dropdown.Option("Income")],
                value=type_val,
                width=110,
                text_size=13,
            )
            
            cat_dropdown = ft.Dropdown(
                options=[ft.dropdown.Option(c) for c in filtered_cats],
                value=category_val,
                width=160,
                text_size=13
            )

            # Store references to fields in the row data for easy access
            item['_controls'] = {
                'date': date_field,
                'type': type_dropdown,
                'category': cat_dropdown,
                'amount': amount_field,
                'note': note_field,
                'payment': payment_dropdown
            }

            self.data_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(date_field),
                    ft.DataCell(type_dropdown),
                    ft.DataCell(cat_dropdown),
                    ft.DataCell(amount_field),
                    ft.DataCell(payment_dropdown),
                    ft.DataCell(note_field),
                    ft.DataCell(ft.IconButton(
                        icon=ft.icons.DELETE, 
                        icon_color=ft.colors.RED,
                        on_click=lambda e, idx=i: self.remove_row(idx),
                        width=30, # Minimize width
                    )),
                ])
            )
        self.data_table.width = 1500 # Increased forced width
        self.data_table.update()
        self.table_container.update()

    def remove_row(self, index):
        if 0 <= index < len(self.imported_data):
            self.imported_data.pop(index)
            self.populate_table(self.imported_data)
            self.update()

    def import_data(self, e):
        count = 0
        try:
            for item in self.imported_data:
                controls = item['_controls']
                
                date = controls['date'].value
                type_ = controls['type'].value
                category = controls['category'].value
                amount_str = controls['amount'].value
                note = controls['note'].value
                payment_key = controls['payment'].value
                
                account_id = None
                credit_card_id = None
                
                if payment_key and payment_key.startswith("account_"):
                    account_id = int(payment_key.split("_")[1])
                elif payment_key and payment_key.startswith("card_"):
                    credit_card_id = int(payment_key.split("_")[1])
                
                try:
                    amount = int(amount_str)
                except ValueError:
                    continue # Skip invalid amounts
                
                self.db.add_transaction(
                    date=date, 
                    type=type_, 
                    category=category, 
                    amount=amount, 
                    note=note,
                    account_id=account_id,
                    credit_card_id=credit_card_id
                )
                count += 1
            
            self.status_text.value = f"Successfully imported {count} transactions!"
            self.status_text.color = ft.colors.GREEN
            self.imported_data = []
            self.data_table.rows.clear()
            self.table_container.visible = False
            self.import_btn.disabled = True
            self.update()
            
            if self.on_import_complete:
                self.on_import_complete()
                
        except Exception as ex:
            self.status_text.value = f"Error importing data: {ex}"
            self.status_text.color = ft.colors.RED
            self.update()
