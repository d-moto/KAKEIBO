import flet as ft
from database import Database
from datetime import datetime
import plotly.graph_objects as go

class MoneyFlowView(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.db = Database()
        self.current_month = datetime.now().strftime("%Y-%m")
        self.chart_container = ft.Container(expand=True)
        self.month_text = ft.Text(
            self.current_month, 
            size=20, 
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE
        )

    def build(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.icons.ARROW_BACK_IOS, 
                                on_click=self.prev_month,
                                icon_color=ft.colors.WHITE
                            ),
                            self.month_text,
                            ft.IconButton(
                                icon=ft.icons.ARROW_FORWARD_IOS, 
                                on_click=self.next_month,
                                icon_color=ft.colors.WHITE
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Divider(),
                    self.chart_container
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
        self.load_data()

    def prev_month(self, e):
        year, month = map(int, self.current_month.split('-'))
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1
        self.current_month = f"{year}-{month:02d}"
        self.month_text.value = self.current_month
        self.load_data()
        self.update()

    def next_month(self, e):
        year, month = map(int, self.current_month.split('-'))
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
        self.current_month = f"{year}-{month:02d}"
        self.month_text.value = self.current_month
        self.load_data()
        self.update()

    def load_data(self):
        try:
            data = self.db.get_monthly_summary(self.current_month)
            
            income_list = data['income']
            expense_list = data['expenses']
            total_income = data['total_income']
            total_expenses = data['total_expenses']
            
            if total_income == 0 and total_expenses == 0:
                self.chart_container.content = ft.Center(ft.Text("No data for this month.", color=ft.colors.WHITE54))
                self.update()
                return

            # Prepare Sankey Data
            labels = []
            source = []
            target = []
            value = []
            colors = []
            
            # Node Indices
            # 0: Total (Center)
            # 1..N: Income Categories
            # N+1..M: Expense Categories
            # M+1: Savings (if any)
            
            budget_node_idx = 0
            budget_node_idx = 0
            labels.append("Total")
            colors.append("darkslategray") # Center node color
            
            current_idx = 1
            
            # Income Nodes (Left side) -> Total Node
            for item in income_list:
                labels.append(item['category'])
                colors.append("mediumseagreen") # Income color
                source.append(current_idx)
                target.append(budget_node_idx)
                value.append(item['amount'])
                current_idx += 1
                
            # Total Node -> Expense Nodes (Right side)
            for item in expense_list:
                labels.append(item['category'])
                colors.append("crimson") # Expense color
                source.append(budget_node_idx)
                target.append(current_idx)
                value.append(item['amount'])
                current_idx += 1
                
            # Total Node -> Savings (if income > expenses)
            if total_income > total_expenses:
                savings = total_income - total_expenses
                labels.append("Savings")
                colors.append("gold") # Savings color
                source.append(budget_node_idx)
                target.append(current_idx)
                value.append(savings)
                current_idx += 1
                
            # Calculate dynamic height based on number of nodes
            # Base height 600, plus 50px for each additional category over 5
            max_categories = max(len(income_list), len(expense_list))
            dynamic_height = max(600, 400 + (max_categories * 60))

            # Create Plotly Figure
            fig = go.Figure(data=[go.Sankey(
                node = dict(
                pad = 30, # Increased padding to separate nodes
                thickness = 20,
                line = dict(color = "black", width = 0.5),
                label = labels,
                color = colors,
                hovertemplate='<b>%{label}</b><br>¥%{value:,}<extra></extra>'
                ),
                link = dict(
                source = source,
                target = target,
                value = value,
                hovertemplate='%{source.label} → %{target.label}<br><b>¥%{value:,}</b><extra></extra>'
            ))])

            fig.update_layout(
                title_text=f"Money Flow - {self.current_month}",
                font_size=10,
                paper_bgcolor='rgba(0,0,0,0)', # Transparent background
                plot_bgcolor='rgba(0,0,0,0)',
                font_color="white",
                margin=dict(l=10, r=10, t=30, b=10),
                height=dynamic_height # Use dynamic height
            )

            from flet.plotly_chart import PlotlyChart
            self.chart_container.content = PlotlyChart(fig, expand=True)
            self.update()
        except Exception as e:
            import traceback
            error_msg = f"Error loading Money Flow:\n{str(e)}\n{traceback.format_exc()}"
            self.chart_container.content = ft.Column([
                ft.Text("Error loading chart", color=ft.colors.RED, size=20),
                ft.Text(error_msg, color=ft.colors.RED_200, size=12, selectable=True)
            ], scroll=ft.ScrollMode.AUTO)
            self.update()
