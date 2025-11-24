import flet as ft
from database import Database
import plotly.graph_objects as go
from flet.plotly_chart import PlotlyChart

class AssetsView(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.db = Database()
        self.accounts_list = ft.Column(spacing=10)
        self.credit_cards_list = ft.Column(spacing=10)
        self.chart_container = ft.Container(padding=20)

    def build(self):


        return ft.Container(
            content=ft.Tabs(
                selected_index=0,
                animation_duration=300,
                tabs=[
                    ft.Tab(
                        text="Overview",
                        icon=ft.icons.SHOW_CHART,
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("Asset Trends (30 Days)", size=20, weight=ft.FontWeight.BOLD),
                                self.chart_container
                            ]),
                            padding=20
                        )
                    ),
                    ft.Tab(
                        text="Banks / Accounts",
                        icon=ft.icons.ACCOUNT_BALANCE,
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text("Manage Accounts", size=20, weight=ft.FontWeight.BOLD),
                                    ft.IconButton(icon=ft.icons.ADD, on_click=self.show_add_account_dialog, tooltip="Add Account")
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Divider(),
                                self.accounts_list
                            ], scroll=ft.ScrollMode.AUTO),
                            padding=20
                        ),
                    ),
                    ft.Tab(
                        text="Credit Cards",
                        icon=ft.icons.CREDIT_CARD,
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text("Manage Credit Cards", size=20, weight=ft.FontWeight.BOLD),
                                    ft.IconButton(icon=ft.icons.ADD, on_click=self.show_add_card_dialog, tooltip="Add Credit Card")
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Divider(),
                                self.credit_cards_list
                            ], scroll=ft.ScrollMode.AUTO),
                            padding=20
                        ),
                    ),
                ],
                expand=True,
            ),
            padding=20,
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.BLUE_GREY_900, ft.colors.BLACK],
            )
        )

    def did_mount(self):
        self.load_accounts()
        self.load_credit_cards()
        self.load_chart()

    def load_chart(self):
        trend_data = self.db.get_asset_trend(days=30)
        
        dates = [d['date'] for d in trend_data]
        amounts = [d['amount'] for d in trend_data]
        
        fig = go.Figure(data=go.Scatter(
            x=dates, 
            y=amounts, 
            mode='lines+markers',
            line=dict(color='#00E5FF', width=3),
            marker=dict(size=6, color='#00E5FF'),
            hovertemplate='<b>%{x}</b><br>¥%{y:,}<extra></extra>'
        ))

        fig.update_layout(
            title='Total Assets (Last 30 Days)',
            title_font_color="white",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color="white",
            xaxis=dict(
                showgrid=False, 
                zeroline=False, 
                tickformat="%m-%d",
                dtick=86400000.0 * 5  # Show tick every 5 days roughly
            ),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', zeroline=False),
            margin=dict(t=40, b=20, l=40, r=20),
            height=400
        )

        self.chart_container.content = PlotlyChart(fig, expand=True)
        self.update()

    def load_accounts(self):
        self.accounts_list.controls.clear()
        accounts = self.db.get_accounts()
        
        if not accounts:
            self.accounts_list.controls.append(ft.Text("No accounts registered.", color=ft.colors.WHITE54))
        
        for acc in accounts:
            self.accounts_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET, color=ft.colors.BLUE_400),
                            ft.Column([
                                ft.Text(acc['name'], weight=ft.FontWeight.BOLD, size=16),
                                ft.Text(f"Type: {acc['type']}", size=12, color=ft.colors.WHITE54),
                            ], spacing=2),
                        ]),
                        ft.Row([
                            ft.Text(f"¥{acc['balance']:,}", size=16, weight=ft.FontWeight.BOLD),
                            ft.IconButton(
                                icon=ft.icons.DELETE, 
                                icon_color=ft.colors.RED_400, 
                                on_click=lambda e, aid=acc['id']: self.delete_account(aid)
                            )
                        ])
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=15,
                    bgcolor=ft.colors.WHITE10,
                    border_radius=10
                )
            )
        self.update()

    def load_credit_cards(self):
        self.credit_cards_list.controls.clear()
        cards = self.db.get_credit_cards()
        
        if not cards:
            self.credit_cards_list.controls.append(ft.Text("No credit cards registered.", color=ft.colors.WHITE54))
            
        for card in cards:
            linked_acc = card['linked_account_name'] if card['linked_account_name'] else "None"
            self.credit_cards_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Icon(ft.icons.CREDIT_CARD, color=ft.colors.ORANGE_400),
                            ft.Column([
                                ft.Text(card['name'], weight=ft.FontWeight.BOLD, size=16),
                                ft.Text(f"Linked: {linked_acc} (Day {card['withdrawal_day']})", size=12, color=ft.colors.WHITE54),
                            ], spacing=2),
                        ]),
                        ft.IconButton(
                            icon=ft.icons.DELETE, 
                            icon_color=ft.colors.RED_400, 
                            on_click=lambda e, cid=card['id']: self.delete_credit_card(cid)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=15,
                    bgcolor=ft.colors.WHITE10,
                    border_radius=10
                )
            )
        self.update()

    def show_add_account_dialog(self, e):
        name_field = ft.TextField(label="Account Name", autofocus=True)
        type_field = ft.Dropdown(
            label="Type",
            options=[
                ft.dropdown.Option("Bank"),
                ft.dropdown.Option("Cash"),
                ft.dropdown.Option("E-Money"),
                ft.dropdown.Option("Investment"),
            ],
            value="Bank"
        )
        balance_field = ft.TextField(label="Initial Balance", value="0", keyboard_type=ft.KeyboardType.NUMBER)

        def save(e):
            if not name_field.value:
                return
            try:
                bal = int(balance_field.value)
                self.db.add_account(name_field.value, type_field.value, bal)
                self.page.dialog.open = False
                self.page.update()
                self.load_accounts()
                self.show_snack("Account added")
            except ValueError:
                pass

        self.show_dialog("Add Account", [name_field, type_field, balance_field], save)

    def show_add_card_dialog(self, e):
        accounts = self.db.get_accounts()
        if not accounts:
            self.show_snack("Please add a bank account first.")
            return

        name_field = ft.TextField(label="Card Name", autofocus=True)
        account_field = ft.Dropdown(
            label="Linked Account",
            options=[ft.dropdown.Option(key=a['id'], text=a['name']) for a in accounts],
            value=accounts[0]['id']
        )
        day_field = ft.TextField(label="Withdrawal Day (1-31)", value="27", keyboard_type=ft.KeyboardType.NUMBER)

        def save(e):
            if not name_field.value:
                return
            try:
                day = int(day_field.value)
                if not (1 <= day <= 31):
                    raise ValueError
                self.db.add_credit_card(name_field.value, int(account_field.value), day)
                self.page.dialog.open = False
                self.page.update()
                self.load_credit_cards()
                self.show_snack("Credit Card added")
            except ValueError:
                self.show_snack("Invalid day")

        self.show_dialog("Add Credit Card", [name_field, account_field, day_field], save)

    def show_dialog(self, title, content_list, on_save):
        def close(e):
            self.page.dialog.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Column(content_list, tight=True, width=300),
            actions=[
                ft.TextButton("Cancel", on_click=close),
                ft.TextButton("Save", on_click=on_save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def delete_account(self, aid):
        self.db.delete_account(aid)
        self.load_accounts()
        self.show_snack("Account deleted")

    def delete_credit_card(self, cid):
        self.db.delete_credit_card(cid)
        self.load_credit_cards()
        self.show_snack("Credit Card deleted")

    def show_snack(self, message):
        snack = ft.SnackBar(ft.Text(message))
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
