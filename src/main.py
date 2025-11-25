import flet as ft
import traceback
import os
import sys
import logging

from utils.logger import setup_logger

# Configure logging
logger = setup_logger()

def main(page: ft.Page):
    logger.info("App started.")
    page.title = "KAKEIBO - Premium"
    
    # Load theme
    # Load theme
    from config.theme import AppTheme
    from database import Database
    db = Database()
    db.init_db() # Explicit initialization
    
    # Force Dark Mode for now as per design requirement
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = AppTheme.colors["background"]
    page.fonts = {
        "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap"
    }
    page.theme = AppTheme.get_theme()
    
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
        from views.reports_view import ReportsView
        
        # Define views
        dashboard = None
        input_form = None
        settings_view = None
        money_flow_view = None
        calendar_view = None
        assets_view = None
        reports_view = None

        def on_save_transaction():
            # Switch to dashboard
            # Note: dashboard.load_data() will be called by dashboard.did_mount() when it's re-added
            rail.selected_index = 0
            change_route(None)
            page.update()

        def on_edit_transaction(transaction):
            # Switch to input form with transaction data
            nonlocal input_form
            input_form = InputFormView(page, db, on_save=on_save_transaction, transaction=transaction)
            rail.selected_index = 1
            change_route(None)
            page.update()

        dashboard = DashboardView(page, db, on_edit_click=on_edit_transaction)
        input_form = InputFormView(page, db, on_save=on_save_transaction)
        settings_view = SettingsView(page, db)
        money_flow_view = MoneyFlowView(page, db)
        calendar_view = CalendarView(page, db)
        assets_view = AssetsView(page, db)
        reports_view = ReportsView(page, db)

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
        # AppBar (Simplified for modern look)
        # We can remove the default AppBar and use a custom header in the content area if needed.
        # For now, let's keep it minimal or remove it to match Discord style.
        page.appbar = None

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
                        
                    input_form = InputFormView(page, db, on_save=on_save_transaction, initial_date=initial_date)
                body_container.content = input_form
            elif index == 2:
                # Money Flow
                body_container.content = money_flow_view
            elif index == 3:
                body_container.content = calendar_view
            elif index == 4:
                body_container.content = assets_view
            elif index == 5:
                body_container.content = reports_view
            elif index == 6:
                body_container.content = settings_view
            
            body_container.update()

        rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.NONE, # Icon only for Discord style
            min_width=72,
            min_extended_width=72,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.DASHBOARD_OUTLINED, 
                    selected_icon=ft.icons.DASHBOARD, 
                    label="Dashboard",
                    padding=ft.padding.symmetric(vertical=10)
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.ADD_CIRCLE_OUTLINE, 
                    selected_icon=ft.icons.ADD_CIRCLE, 
                    label="Add",
                    padding=ft.padding.symmetric(vertical=10)
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.WATERFALL_CHART, 
                    selected_icon=ft.icons.WATERFALL_CHART, 
                    label="Money Flow",
                    padding=ft.padding.symmetric(vertical=10)
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.CALENDAR_MONTH_OUTLINED, 
                    selected_icon=ft.icons.CALENDAR_MONTH, 
                    label="Calendar",
                    padding=ft.padding.symmetric(vertical=10)
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.ACCOUNT_BALANCE_OUTLINED, 
                    selected_icon=ft.icons.ACCOUNT_BALANCE, 
                    label="Assets",
                    padding=ft.padding.symmetric(vertical=10)
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.ANALYTICS_OUTLINED, 
                    selected_icon=ft.icons.ANALYTICS, 
                    label="Reports",
                    padding=ft.padding.symmetric(vertical=10)
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.SETTINGS_OUTLINED, 
                    selected_icon=ft.icons.SETTINGS, 
                    label="Settings",
                    padding=ft.padding.symmetric(vertical=10)
                ),
            ],
            on_change=change_route,
            bgcolor=AppTheme.colors["background"],
            indicator_color=AppTheme.colors["surface_variant"], # Subtle indicator
        )

        # Main Layout
        layout = ft.Row(
            [
                rail,
                # Content Area with rounded corners
                ft.Container(
                    content=body_container,
                    expand=True,
                    bgcolor=AppTheme.colors["surface_variant"],
                    border_radius=ft.border_radius.only(top_left=15),
                    padding=20,
                )
            ],
            expand=True,
            spacing=0,
        )

        page.clean()
        page.add(layout)
        page.update()
        page.add(layout)
        page.update()
        logger.info("Main UI rendered.")

    except Exception as e:
        logger.error(f"CRITICAL ERROR: {e}")
        logger.error(traceback.format_exc())
        page.clean()
        page.add(
            ft.Column([
                ft.Text("An error occurred:", color="red", size=20),
                ft.Text(str(e), color="red"),
                ft.Text("See app.log for details.", color="white")
            ])
        )
        page.update()

if __name__ == "__main__":
    try:
        ft.app(target=main)
    except Exception as e:
        logger.error(f"Startup Error: {e}")
        logger.error(traceback.format_exc())
