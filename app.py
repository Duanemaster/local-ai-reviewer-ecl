"""ECL - Code Reviewer. Entry point lang ito; nasa ecl/ ang lahat ng logic."""
import sys

from ecl.config import APP_ID


def _set_windows_app_id():
    """Para sariling icon ng ECL ang lalabas sa taskbar (hindi icon ng python.exe)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass


def main():
    _set_windows_app_id()
    from ecl.ui.main_window import MainWindow
    MainWindow().mainloop()


if __name__ == "__main__":
    main()