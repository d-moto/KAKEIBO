import flet
import pkgutil
import importlib

def find_colors(package):
    for importer, modname, ispkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if "colors" in modname:
            print(f"Found: {modname}")
            try:
                mod = importlib.import_module(modname)
                print(f"  Has WHITE? {'WHITE' in dir(mod)}")
            except Exception as e:
                print(f"  Import failed: {e}")

find_colors(flet)
