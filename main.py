import flet as ft
import traceback
import os
import sys
import logging

# Configure logging
app_data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Kakeibo')
os.makedirs(app_data_dir, exist_ok=True)
log_file = os.path.join(app_data_dir, 'kakeibo.log')
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main(page: ft.Page):
    logging.info("App started.")
    page.title = "KAKEIBO - Premium"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1000
    page.window_height = 800
    
    # Show initial loading state
    page.add(ft.Text("Initializing Application...", size=20, color="white"))
    page.update()

    try:
        from views.dashboard import DashboardView
        from views.input_form import InputFormView
        
        # Define views
        dashboard = DashboardView(page)
        
        def on_save_transaction():
            # Refresh dashboard data when a new transaction is saved
            dashboard.load_data()
            # Switch to dashboard
            rail.selected_index = 0
            change_route(None)
            page.update()

        input_form = InputFormView(page, on_save=on_save_transaction)

        body_container = ft.Container(content=dashboard, expand=True)

        def change_route(e):
            index = rail.selected_index
            if index == 0:
                body_container.content = dashboard
            elif index == 1:
                body_container.content = input_form
            body_container.update()

        rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=400,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.DASHBOARD_OUTLINED, 
                    selected_icon=ft.icons.DASHBOARD, 
                    label="Dashboard"
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.ADD_CIRCLE_OUTLINE, 
                    selected_icon=ft.icons.ADD_CIRCLE, 
                    label="Add"
                ),
            ],
            on_change=change_route,
            bgcolor=ft.colors.BLUE_GREY_900,
        )

        # Layout
        layout = ft.Row(
            [
                rail,
                ft.VerticalDivider(width=1, color=ft.colors.WHITE24),
                body_container,
            ],
            expand=True,
        )

        page.clean()
        page.add(layout)
        page.update()
        logging.info("Main UI rendered.")

    except Exception as e:
        logging.error(f"CRITICAL ERROR: {e}")
        logging.error(traceback.format_exc())
        page.clean()
        page.add(
            ft.Column([
                ft.Text("An error occurred:", color="red", size=20),
                ft.Text(str(e), color="red"),
                ft.Text("See kakeibo.log for details.", color="white")
            ])
        )
        page.update()

if __name__ == "__main__":
    try:
        ft.app(target=main)
    except Exception as e:
        logging.error(f"Startup Error: {e}")
        logging.error(traceback.format_exc())
