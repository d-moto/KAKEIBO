import flet as ft

class AppTheme:
    # Color Palette (Discord-inspired)
    colors = {
        "background": "#202225",       # Deepest dark (Main background)
        "surface": "#2f3136",          # Sidebar / Cards
        "surface_variant": "#36393f",  # Chat / Content area
        "primary": "#5865F2",          # Blurple (Brand color)
        "secondary": "#4f545c",        # Secondary elements
        "accent": "#00A8FC",           # Cyan accent
        "success": "#3BA55C",          # Green
        "danger": "#ED4245",           # Red
        "warning": "#FAA61A",          # Yellow
        "text_primary": "#FFFFFF",     # White
        "text_secondary": "#B9BBBE",   # Light Gray
        "divider": "#202225",          # Divider color
    }

    # Text Styles
    text_styles = {
        "h1": ft.TextStyle(size=28, weight=ft.FontWeight.BOLD, color=colors["text_primary"]),
        "h2": ft.TextStyle(size=24, weight=ft.FontWeight.BOLD, color=colors["text_primary"]),
        "h3": ft.TextStyle(size=20, weight=ft.FontWeight.W_600, color=colors["text_primary"]),
        "body": ft.TextStyle(size=14, color=colors["text_secondary"]),
        "caption": ft.TextStyle(size=12, color=colors["text_secondary"]),
        "label": ft.TextStyle(size=14, weight=ft.FontWeight.BOLD, color=colors["text_secondary"]),
    }

    # Component Styles
    styles = {
        "card": {
            "bgcolor": colors["surface"],
            "border_radius": 10,
            "padding": 20,
        },
        "sidebar": {
            "bgcolor": colors["background"],
            "width": 80, # Slim sidebar
        },
        "content_area": {
            "bgcolor": colors["surface_variant"],
            "border_radius": ft.border_radius.only(top_left=15),
        }
    }

    @classmethod
    def get_theme(cls):
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                background=cls.colors["background"],
                surface=cls.colors["surface"],
                primary=cls.colors["primary"],
                secondary=cls.colors["secondary"],
                on_background=cls.colors["text_primary"],
                on_surface=cls.colors["text_primary"],
            ),
            font_family="Roboto", # Default font
        )
