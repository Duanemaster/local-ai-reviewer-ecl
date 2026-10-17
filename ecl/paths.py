import os
import sys


def resource_path(relative):
    """Gumagana sa normal run at sa PyInstaller .exe."""
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)