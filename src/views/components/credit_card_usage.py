import flet as ft
from datetime import datetime
from config.theme import AppTheme

class CreditCardUsage(ft.UserControl):
    def __init__(self, lang="en"):
        super().__init__()
        self.lang = lang
        self.cards_column = ft.Column(spacing=10)
        self.container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.CREDIT_CARD, color=AppTheme.colors["text_primary"], size=20),
                    ft.Text("Credit Card Usage", size=16, weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"])
                ], spacing=10),
                ft.Divider(color=AppTheme.colors["divider"], height=1),
                self.cards_column
            ], spacing=15),
            bgcolor=AppTheme.colors["surface"],
            padding=20,
            border_radius=10,
        )

    def build(self):
        return self.container

    def update_usage(self, cards, usage_data, fixed_costs_data, next_payment_data):
        self.cards_column.controls.clear()
        
        if not cards:
            self.cards_column.controls.append(
                ft.Text("No credit cards registered.", color=ft.colors.WHITE54, size=12)
            )
        else:
            for card in cards:
                card_id = card['id']
                usage_amount = usage_data.get(card_id, 0)
                fixed_amount = fixed_costs_data.get(card_id, 0)
                next_payment = next_payment_data.get(card_id, {})
                
                # Format: 
                # Current: ¥10,000 + ¥5,000 (Fixed)
                # Next Payment (12/10): ¥45,000
                
                usage_text = f"Current: ¥{usage_amount:,}"
                if fixed_amount > 0:
                    usage_text += f" + ¥{fixed_amount:,} (Fixed)"
                
                content_col = ft.Column([
                    ft.Text(usage_text, size=14, weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"]),
                ], spacing=2)
                
                if next_payment:
                    date_str = next_payment['payment_date']
                    # Format date to MM/DD
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        date_display = dt.strftime("%m/%d")
                    except:
                        date_display = date_str
                        
                    amount = next_payment['amount']
                    content_col.controls.append(
                        ft.Text(f"Next Payment ({date_display}): ¥{amount:,}", size=12, color=ft.colors.ORANGE_300)
                    )
                
                row = ft.Row([
                    ft.Row([
                        ft.Icon(ft.icons.CREDIT_CARD, size=16, color=ft.colors.BLUE_200),
                        ft.Text(card['name'], size=14, color=AppTheme.colors["text_primary"]),
                    ], spacing=10),
                    content_col
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                
                self.cards_column.controls.append(row)
        
        self.update()
