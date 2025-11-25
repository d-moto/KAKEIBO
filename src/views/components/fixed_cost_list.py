import flet as ft
from config.theme import AppTheme

class FixedCostList(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.items_column = ft.Column(spacing=5)
        self.container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.REPEAT, color=AppTheme.colors["text_primary"], size=20),
                    ft.Text("Fixed Costs", size=16, weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"])
                ], spacing=10),
                ft.Divider(color=AppTheme.colors["divider"], height=1),
                self.items_column
            ], spacing=15),
            bgcolor=AppTheme.colors["surface"],
            padding=20,
            border_radius=10,
        )

    def build(self):
        return self.container

    def update_list(self, fixed_costs):
        self.items_column.controls.clear()
        
        if not fixed_costs:
            self.items_column.controls.append(
                ft.Text("No fixed costs registered.", color=ft.colors.WHITE54, size=12)
            )
        else:
            # Sort by day of month
            sorted_costs = sorted(fixed_costs, key=lambda x: x['day_of_month'])
            
            for fc in sorted_costs:
                name = fc['name']
                amount = fc['amount']
                day = fc['day_of_month']
                
                row = ft.Row([
                    ft.Row([
                        ft.Container(
                            content=ft.Text(str(day), size=10, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                            bgcolor=AppTheme.colors["primary"],
                            padding=ft.padding.all(4),
                            border_radius=4,
                            width=24,
                            alignment=ft.alignment.center
                        ),
                        ft.Text(name, size=14, color=AppTheme.colors["text_primary"]),
                    ], spacing=10),
                    ft.Text(f"¥{amount:,}", size=14, weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                
                self.items_column.controls.append(row)
        
        self.update()
