import flet as ft
from database import Database
from config.theme import AppTheme


class AssetsView(ft.UserControl):
    def __init__(self, page: ft.Page, db: Database):
        super().__init__()
        self.page = page
        self.db = db
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
                                ft.Text("Asset Trends (30 Days)", style=AppTheme.text_styles["h2"]),
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
                                    ft.Text("Manage Accounts", style=AppTheme.text_styles["h2"]),
                                    ft.IconButton(icon=ft.icons.ADD, on_click=self.show_add_account_dialog, tooltip="Add Account", icon_color=AppTheme.colors["primary"])
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Divider(color=AppTheme.colors["divider"]),
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
                                    ft.Text("Manage Credit Cards", style=AppTheme.text_styles["h2"]),
                                    ft.IconButton(icon=ft.icons.ADD, on_click=self.show_add_card_dialog, tooltip="Add Credit Card", icon_color=AppTheme.colors["primary"])
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Divider(color=AppTheme.colors["divider"]),
                                self.credit_cards_list
                            ], scroll=ft.ScrollMode.AUTO),
                            padding=20
                        ),
                    ),
                ],
                expand=True,
                indicator_color=AppTheme.colors["primary"],
                label_color=AppTheme.colors["primary"],
                unselected_label_color=AppTheme.colors["text_secondary"],
            ),
            padding=10,
            expand=True,
        )

    def did_mount(self):
        self.load_accounts()
        self.load_credit_cards()
        self.load_chart()

    def load_chart(self):
        trend_data = self.db.get_asset_trend(days=30)
        
        if not trend_data:
            self.chart_container.content = ft.Text("No data available", color=ft.colors.WHITE54)
            self.update()
            return

        # Prepare data points
        data_points = []
        min_y = float('inf')
        max_y = float('-inf')
        
        for i, d in enumerate(trend_data):
            amount = d['amount']
            data_points.append(
                ft.LineChartDataPoint(
                    i, 
                    amount,
                    tooltip=f"{d['date']}\n{amount:,} JPY",
                )
            )
            min_y = min(min_y, amount)
            max_y = max(max_y, amount)
            
        # Add buffer to Y axis
        y_span = max_y - min_y
        if y_span == 0:
            y_span = max_y * 0.1 if max_y != 0 else 1000
            
        min_y -= y_span * 0.1
        max_y += y_span * 0.1

        chart = ft.LineChart(
            data_series=[
                ft.LineChartData(
                    data_points=data_points,
                    stroke_width=3,
                    color=AppTheme.colors["accent"],
                    curved=True,
                    stroke_cap_round=True,
                    below_line_bgcolor=ft.colors.with_opacity(0.2, AppTheme.colors["accent"]),
                )
            ],
            border=ft.border.all(1, AppTheme.colors["divider"]),
            left_axis=ft.ChartAxis(
                labels_size=40,
                title=ft.Text("Amount", size=10, color=AppTheme.colors["text_secondary"]),
                title_size=20,
            ),
            bottom_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(
                        value=i,
                        label=ft.Text(d['date'][5:], size=10, weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_secondary"])
                    ) for i, d in enumerate(trend_data) if i % 5 == 0 # Show every 5th label
                ],
                labels_size=20,
            ),
            tooltip_bgcolor=AppTheme.colors["surface_variant"],
            min_y=min_y,
            max_y=max_y,
            expand=True,
        )

        self.chart_container.content = ft.Container(
            content=chart,
            height=300,
            padding=10
        )
        self.update()

    def load_accounts(self):
        self.accounts_list.controls.clear()
        accounts = self.db.get_accounts()
        
        if not accounts:
            self.accounts_list.controls.append(ft.Text("No accounts registered.", color=ft.colors.WHITE54))
            self.update()
            return

        # Calculate Total Assets
        total_assets = sum(acc['balance'] for acc in accounts)
        
        # Group by Asset Type
        assets_by_type = {}
        for acc in accounts:
            atype = acc.get('asset_type', 'Bank')
            if atype not in assets_by_type:
                assets_by_type[atype] = []
            assets_by_type[atype].append(acc)

        # Display Total Assets Summary
        self.accounts_list.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("Total Assets", size=14, color=ft.colors.WHITE70),
                    ft.Text(f"¥{total_assets:,}", size=32, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_400),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                bgcolor=ft.colors.WHITE10,
                border_radius=10,
                alignment=ft.alignment.center
            )
        )

        # Display Accounts Grouped by Type
        for atype, accs in assets_by_type.items():
            self.accounts_list.controls.append(ft.Text(atype, size=18, weight=ft.FontWeight.BOLD, color=ft.colors.CYAN_200))
            
            for acc in accs:
                self.accounts_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Row([
                                ft.Container(
                                    content=ft.Icon(self._get_icon_for_type(atype), color=AppTheme.colors["primary"]),
                                    padding=10,
                                    bgcolor=ft.colors.with_opacity(0.1, AppTheme.colors["primary"]),
                                    border_radius=10,
                                ),
                                ft.Column([
                                    ft.Text(acc['name'], weight=ft.FontWeight.BOLD, size=16, color=AppTheme.colors["text_primary"]),
                                    ft.Text(f"Type: {acc['type']}", size=12, color=AppTheme.colors["text_secondary"]),
                                ], spacing=2),
                            ]),
                            ft.Row([
                                ft.Text(f"¥{acc['balance']:,}", size=16, weight=ft.FontWeight.BOLD, color=AppTheme.colors["text_primary"]),
                                ft.IconButton(
                                    icon=ft.icons.EDIT, 
                                    icon_color=AppTheme.colors["text_secondary"], 
                                    tooltip="Edit Account",
                                    on_click=lambda e, a=acc: self.show_add_account_dialog(e, account=a)
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE, 
                                    icon_color=AppTheme.colors["danger"], 
                                    tooltip="Delete Account",
                                    on_click=lambda e, aid=acc['id']: self.delete_account(aid)
                                )
                            ])
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=15,
                        bgcolor=AppTheme.colors["surface"],
                        border_radius=10,
                        on_hover=lambda e: self.on_card_hover(e)
                    )
                )
        self.update()

    def _get_icon_for_type(self, asset_type):
        if asset_type == "Bank": return ft.icons.ACCOUNT_BALANCE
        if asset_type == "Cash": return ft.icons.MONEY
        if asset_type == "E-Money": return ft.icons.SMARTPHONE
        if asset_type == "Investment": return ft.icons.TRENDING_UP
        if asset_type == "Stock": return ft.icons.SHOW_CHART
        return ft.icons.ACCOUNT_BALANCE_WALLET

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
                            ft.Container(
                                content=ft.Icon(ft.icons.CREDIT_CARD, color=AppTheme.colors["warning"]),
                                padding=10,
                                bgcolor=ft.colors.with_opacity(0.1, AppTheme.colors["warning"]),
                                border_radius=10,
                            ),
                            ft.Column([
                                ft.Text(card['name'], weight=ft.FontWeight.BOLD, size=16, color=AppTheme.colors["text_primary"]),
                                ft.Text(f"Linked: {linked_acc} (Day {card['withdrawal_day']})", size=12, color=AppTheme.colors["text_secondary"]),
                            ], spacing=2),
                        ]),
                        ft.Row([
                            ft.Text(f"¥{card.get('balance', 0):,}", size=16, weight=ft.FontWeight.BOLD, color=AppTheme.colors["danger"]),
                            ft.IconButton(
                                icon=ft.icons.EDIT, 
                                icon_color=AppTheme.colors["text_secondary"], 
                                tooltip="Edit Card",
                                on_click=lambda e, c=card: self.show_add_card_dialog(e, card=c)
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE, 
                                icon_color=AppTheme.colors["danger"], 
                                tooltip="Delete Card",
                                on_click=lambda e, cid=card['id']: self.delete_credit_card(cid)
                            )
                        ])
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=15,
                    bgcolor=AppTheme.colors["surface"],
                    border_radius=10,
                    on_hover=lambda e: self.on_card_hover(e)
                )
            )

        self.update()

    def show_add_account_dialog(self, e, account=None):
        # Load potential link sources
        accounts = self.db.get_accounts()
        cards = self.db.get_credit_cards()
        
        name_field = ft.TextField(label="Account Name", autofocus=True, value=account['name'] if account else "")
        type_field = ft.Dropdown(
            label="Type",
            options=[
                ft.dropdown.Option("Bank"),
                ft.dropdown.Option("Cash"),
                ft.dropdown.Option("E-Money"),
                ft.dropdown.Option("Investment"),
                ft.dropdown.Option("Stock"),
                ft.dropdown.Option("Other"),
            ],
            value=account['asset_type'] if account else "Bank",
            on_change=lambda e: update_visibility()
        )
        balance_field = ft.TextField(label="Current Balance", value=str(account['balance']) if account else "0", keyboard_type=ft.KeyboardType.NUMBER)
        
        # Linking fields
        link_account_field = ft.Dropdown(
            label="Link Funding Account (Bank)",
            options=[ft.dropdown.Option(key=str(a['id']), text=a['name']) for a in accounts],
            visible=False,
            value=str(account['linked_account_id']) if account and account['linked_account_id'] else None
        )
        link_card_field = ft.Dropdown(
            label="Link Funding Card",
            options=[ft.dropdown.Option(key=str(c['id']), text=c['name']) for c in cards],
            visible=False,
            value=str(account['linked_card_id']) if account and account['linked_card_id'] else None
        )

        def update_visibility():
            is_investment = type_field.value in ["Investment", "Stock"]
            link_account_field.visible = is_investment
            link_card_field.visible = is_investment
            if self.page.dialog:
                self.page.dialog.update()

        # Initial visibility check
        is_investment = type_field.value in ["Investment", "Stock"]
        link_account_field.visible = is_investment
        link_card_field.visible = is_investment

        def save(e):
            if not name_field.value:
                return
            try:
                bal = int(balance_field.value)
                linked_acc_id = int(link_account_field.value) if link_account_field.value and link_account_field.visible else None
                linked_card_id = int(link_card_field.value) if link_card_field.value and link_card_field.visible else None
                
                if account:
                    self.db.update_account(
                        account['id'],
                        name_field.value,
                        type_field.value, # type and asset_type are same for now
                        bal,
                        asset_type=type_field.value,
                        linked_account_id=linked_acc_id,
                        linked_card_id=linked_card_id
                    )
                    self.show_snack("Account updated")
                else:
                    self.db.add_account(
                        name_field.value, 
                        type_field.value, 
                        bal, 
                        asset_type=type_field.value,
                        linked_account_id=linked_acc_id,
                        linked_card_id=linked_card_id
                    )
                    self.show_snack("Account added")
                
                self.page.dialog.open = False
                self.page.update()
                self.load_accounts()
            except ValueError:
                self.show_snack("Invalid input")
            except Exception as ex:
                import traceback
                traceback.print_exc()
                self.show_snack(f"Error: {ex}")

        title = "Edit Account" if account else "Add Account"
        self.show_dialog(title, [name_field, type_field, balance_field, link_account_field, link_card_field], save)

    def show_add_card_dialog(self, e, card=None):
        accounts = self.db.get_accounts()
        if not accounts:
            self.show_snack("Please add a bank account first.")
            return

        name_field = ft.TextField(label="Card Name", autofocus=True, value=card['name'] if card else "")
        account_field = ft.Dropdown(
            label="Linked Account",
            options=[ft.dropdown.Option(key=str(a['id']), text=a['name']) for a in accounts],
            value=str(card['linked_account_id']) if card else str(accounts[0]['id'])
        )
        day_field = ft.TextField(label="Withdrawal Day (1-31)", value=str(card['withdrawal_day']) if card else "27", keyboard_type=ft.KeyboardType.NUMBER)
        closing_day_field = ft.TextField(label="Closing Day (1-31)", value=str(card.get('closing_day', 31)) if card else "31", keyboard_type=ft.KeyboardType.NUMBER)

        def save(e):
            if not name_field.value:
                return
            try:
                day = int(day_field.value)
                closing_day = int(closing_day_field.value)
                if not (1 <= day <= 31) or not (1 <= closing_day <= 31):
                    raise ValueError
                
                if card:
                    self.db.update_credit_card(card['id'], name_field.value, int(account_field.value), day, closing_day)
                    self.show_snack("Credit Card updated")
                else:
                    self.db.add_credit_card(name_field.value, int(account_field.value), day, closing_day)
                    self.show_snack("Credit Card added")
                
                self.page.dialog.open = False
                self.page.update()
                self.load_credit_cards()
            except ValueError:
                self.show_snack("Invalid day")

        title = "Edit Credit Card" if card else "Add Credit Card"
        self.show_dialog(title, [name_field, account_field, day_field, closing_day_field], save)

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

    def on_card_hover(self, e):
        e.control.bgcolor = AppTheme.colors["surface_variant"] if e.data == "true" else AppTheme.colors["surface"]
        e.control.update()
