import flet as ft
try:
    print(f"Flet file: {ft.__file__}")
    print(f"Flet version: {getattr(ft, '__version__', 'Unknown')}")
    print(f"ft.colors: {getattr(ft, 'colors', 'Missing')}")
except Exception as e:
    print(f"Error: {e}")
print("Dir(ft):", dir(ft))
