"""Custom dark dialogs na pamalit sa native messagebox."""
import customtkinter as ctk

from ecl.config import ICON_PATH
from ecl.paths import resource_path
from ecl.theme import COLORS, F_UI, F_UI_BOLD

KIND_COLORS = {
    "info": COLORS["accent"],
    "warning": COLORS["busy"],
    "error": COLORS["danger"],
    "confirm": COLORS["accent"],
    "danger": COLORS["danger"],
}


class Dialog(ctk.CTkToplevel):
    """buttons = [(label, value, style)], style: primary | danger | ghost."""

    def __init__(self, parent, title, message, buttons, kind="info", cancel_value=None, default=0):
        super().__init__(parent)
        self.withdraw()
        self.result = cancel_value
        self._cancel_value = cancel_value

        self.title(title)
        self.resizable(False, False)
        self.configure(fg_color=COLORS["surface"])
        self.transient(parent)

        # kulay na strip sa taas depende sa klase ng dialog
        ctk.CTkFrame(self, height=3, corner_radius=0, fg_color=KIND_COLORS.get(kind, COLORS["accent"])).pack(fill="x")

        ctk.CTkLabel(self, text=title, font=F_UI_BOLD, text_color=COLORS["text"], anchor="w").pack(
            fill="x", padx=22, pady=(18, 4))
        ctk.CTkLabel(self, text=message, font=F_UI, text_color=COLORS["muted"], anchor="w",
                     justify="left", wraplength=380).pack(fill="x", padx=22, pady=(0, 18))

        bar = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["toolbar"])
        bar.pack(fill="x")
        ctk.CTkFrame(bar, height=1, corner_radius=0, fg_color=COLORS["border"]).pack(fill="x")
        row = ctk.CTkFrame(bar, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=12)

        self._buttons = []
        for label, value, style in reversed(buttons):      # unang button = pinakakanan
            btn = self._make_button(row, label, value, style)
            btn.pack(side="right", padx=(8, 0))
            self._buttons.insert(0, btn)

        self.bind("<Escape>", lambda e: self._close(self._cancel_value))
        self.bind("<Return>", lambda e: self._buttons[default].invoke())
        self.protocol("WM_DELETE_WINDOW", lambda: self._close(self._cancel_value))

        self._center(parent)
        self.deiconify()
        self.after(50, self._take_focus)
        self.after(250, self._set_icon)     # ni-re-reset ng customtkinter ang icon

    def _make_button(self, master, label, value, style):
        colors = {
            "primary": (COLORS["accent"], COLORS["accent_hover"], "#FFFFFF"),
            "danger": (COLORS["danger"], "#D9504D", "#FFFFFF"),
            "ghost": (COLORS["input"], COLORS["hover"], COLORS["text"]),
        }[style]
        return ctk.CTkButton(
            master, text=label, width=92, height=30, corner_radius=4, font=F_UI,
            fg_color=colors[0], hover_color=colors[1], text_color=colors[2],
            command=lambda v=value: self._close(v),
        )

    def _center(self, parent):
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _take_focus(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _set_icon(self):
        try:
            self.iconbitmap(resource_path(ICON_PATH))
        except Exception:
            pass

    def _close(self, value):
        self.result = value
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


def confirm(parent, title, message, yes="Yes", no="Cancel", danger=False):
    """Return True kung pinindot ang yes."""
    dlg = Dialog(
        parent, title, message,
        buttons=[(yes, True, "danger" if danger else "primary"), (no, False, "ghost")],
        kind="danger" if danger else "confirm", cancel_value=False,
    )
    parent.wait_window(dlg)
    return bool(dlg.result)


def notify(parent, title, message, kind="info", ok="OK"):
    """Simpleng mensahe na may isang button. kind: info | warning | error."""
    dlg = Dialog(parent, title, message, buttons=[(ok, True, "primary")], kind=kind, cancel_value=True)
    parent.wait_window(dlg)