import flet as ft
from config.theme import AppTheme

class BankAccountSummary(ft.UserControl):
    def __init__(self, lang="en"):
        super().__init__()
        self.lang = lang
        self.accounts_column = ft.Column(spacing=10)
        self.container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.ACCOUNT_BALANCE, color=AppTheme.colors["text_primary"], size=20),
                    ft.Text("Bank Accounts", size=16, weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"])
                ], spacing=10),
                ft.Divider(color=AppTheme.colors["divider"], height=1),
                self.accounts_column
            ], spacing=15),
            bgcolor=AppTheme.colors["surface"],
            padding=20,
            border_radius=10,
        )

    def build(self):
        return self.container

    def update_accounts(self, accounts, fixed_costs_data, cc_payments_data):
        self.accounts_column.controls.clear()
        
        # Filter for Bank accounts only? Or all accounts?
        # Usually "Bank" type.
        bank_accounts = [a for a in accounts if a.get('asset_type') == 'Bank']
        
        if not bank_accounts:
            self.accounts_column.controls.append(
                ft.Text("No bank accounts registered.", color=ft.colors.WHITE54, size=12)
            )
        else:
            for account in bank_accounts:
                account_id = account['id']
                balance = account['balance']
                fixed_amount = fixed_costs_data.get(account_id, 0)
                cc_amount = cc_payments_data.get(account_id, 0)
                
                # Format: ¥100,000 - ¥50,000 (Fixed) - ¥20,000 (CC)
                balance_text = f"¥{balance:,}"
                
                deductions = []
                if fixed_amount > 0:
                    deductions.append(f"- ¥{fixed_amount:,} (Fixed)")
                if cc_amount > 0:
                    deductions.append(f"- ¥{cc_amount:,} (CC)")
                
                if deductions:
                    balance_text += " " + " ".join(deductions)
                
                row = ft.Row([
                    ft.Row([
                        ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET, size=16, color=ft.colors.GREEN_200),
                        ft.Text(account['name'], size=14, color=AppTheme.colors["text_primary"]),
                    ], spacing=10),
                    ft.Text(balance_text, size=14, weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                
                self.accounts_column.controls.append(row)
        
        self.update()
