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

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
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
                    )
                ],
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=30,
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.BLUE_GREY_900, ft.colors.BLACK],
            )
        )

    def save_settings(self, e):
        encoding = self.encoding_dropdown.value
        self.db.set_setting("csv_encoding", encoding)
        self.page.snack_bar = ft.SnackBar(ft.Text("Settings saved!"))
        self.page.snack_bar.open = True
        self.page.update()
