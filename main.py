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
    
    # Load theme
    from database import Database
    db = Database()
    theme = db.get_setting("theme", "dark")
    page.theme_mode = ft.ThemeMode.DARK if theme == "dark" else ft.ThemeMode.LIGHT
    
    page.window.width = 1000
    page.window.height = 800
    
    # Show initial loading state
    page.add(ft.Text("Initializing Application...", size=20, color="white"))
    page.update()

    try:
        from views.dashboard import DashboardView
        from views.input_form import InputFormView
        from views.settings import SettingsView
        from views.money_flow import MoneyFlowView
        from views.calendar_view import CalendarView
        from views.assets_view import AssetsView
        
        # Define views
        dashboard = None
        input_form = None
        settings_view = None
        money_flow_view = None
        calendar_view = None
        assets_view = None

        def on_save_transaction():
            # Switch to dashboard
            # Note: dashboard.load_data() will be called by dashboard.did_mount() when it's re-added
            rail.selected_index = 0
            change_route(None)
            page.update()

        def on_edit_transaction(transaction):
            # Switch to input form with transaction data
            nonlocal input_form
            input_form = InputFormView(page, on_save=on_save_transaction, transaction=transaction)
            rail.selected_index = 1
            change_route(None)
            page.update()

        dashboard = DashboardView(page, on_edit_click=on_edit_transaction)
        input_form = InputFormView(page, on_save=on_save_transaction)
        settings_view = SettingsView(page)
        money_flow_view = MoneyFlowView(page)
        calendar_view = CalendarView(page)
        assets_view = AssetsView(page)

        def check_fixed_costs(page):
            added_count = db.process_fixed_costs()
            
            if added_count > 0:
                snack = ft.SnackBar(ft.Text(f"Auto-added {added_count} fixed cost(s)."))
                page.overlay.append(snack)
                snack.open = True
                page.update()
                # Dashboard will load data when mounted, so no need to call load_data() here if it's startup.
                # If we ever call this later, we should check if dashboard is mounted.
                if hasattr(dashboard, 'balance_text'):
                    dashboard.load_data()

        # Check for fixed costs on startup
        check_fixed_costs(page)

        body_container = ft.Container(content=dashboard, expand=True)

        def toggle_theme(e):
            if page.theme_mode == ft.ThemeMode.DARK:
                page.theme_mode = ft.ThemeMode.LIGHT
                e.control.icon = ft.icons.DARK_MODE
                db.set_setting("theme", "light")
            else:
                page.theme_mode = ft.ThemeMode.DARK
                e.control.icon = ft.icons.LIGHT_MODE
                db.set_setting("theme", "dark")
            page.update()

        # AppBar with Theme Toggle
        page.appbar = ft.AppBar(
            title=ft.Text("KAKEIBO"),
            center_title=True,
            bgcolor=ft.colors.SURFACE_VARIANT,
            actions=[
                ft.IconButton(
                    icon=ft.icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else ft.icons.LIGHT_MODE,
                    on_click=toggle_theme,
                    tooltip="Toggle Theme"
                )
            ]
        )

        def change_route(e):
            from datetime import datetime
            index = rail.selected_index
            
            if index == 0:
                body_container.content = dashboard
            elif index == 1:
                # Reset input form when switching manually (add mode)
                if e is not None: # e is None when called programmatically for edit
                    nonlocal input_form
                    # Smart default date logic
                    now = datetime.now()
                    current_real_month = now.strftime("%Y-%m")
                    
                    if dashboard.current_month == current_real_month:
                        initial_date = now.strftime("%Y-%m-%d")
                    else:
                        initial_date = f"{dashboard.current_month}-01"
                        
                    input_form = InputFormView(page, on_save=on_save_transaction, initial_date=initial_date)
                body_container.content = input_form
            elif index == 2:
                # Money Flow
                body_container.content = money_flow_view
            elif index == 3:
                body_container.content = calendar_view
            elif index == 4:
                body_container.content = assets_view
            elif index == 5:
                body_container.content = settings_view
            
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
                ft.NavigationRailDestination(
                    icon=ft.icons.WATERFALL_CHART, 
                    selected_icon=ft.icons.WATERFALL_CHART, 
                    label="Money Flow"
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.CALENDAR_MONTH_OUTLINED, 
                    selected_icon=ft.icons.CALENDAR_MONTH, 
                    label="Calendar"
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.ACCOUNT_BALANCE_OUTLINED, 
                    selected_icon=ft.icons.ACCOUNT_BALANCE, 
                    label="Assets"
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.SETTINGS_OUTLINED, 
                    selected_icon=ft.icons.SETTINGS, 
                    label="Settings"
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
