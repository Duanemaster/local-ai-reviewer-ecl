"""Top toolbar: file actions, mode/model pickers, run/stop."""
import customtkinter as ctk

from ecl.config import DEFAULT_MODEL
from ecl.prompts import DEFAULT_MODE, MODES
from ecl.theme import COLORS, F_UI, F_UI_SMALL


class Toolbar(ctk.CTkFrame):
    def __init__(self, master, handlers):
        super().__init__(master, height=46, corner_radius=0, fg_color=COLORS["toolbar"])
        self.pack_propagate(False)

        self.model_var = ctk.StringVar(value=DEFAULT_MODEL)
        self.mode_var = ctk.StringVar(value=DEFAULT_MODE)

        ctk.CTkFrame(self, height=1, corner_radius=0, fg_color=COLORS["border"]).pack(side="bottom", fill="x")

        # ---- left ----
        self.open_btn = self._button("Open File", handlers["open"], width=82)
        self.open_btn.pack(side="left", padx=(10, 2), pady=8)
        self.clear_btn = self._button("Clear", handlers["clear"], width=60)
        self.clear_btn.pack(side="left", padx=2, pady=8)
        self._separator("left")

        ctk.CTkLabel(self, text="Mode", font=F_UI_SMALL, text_color=COLORS["muted"]).pack(side="left", padx=(4, 6))
        self.mode_menu = self._menu(self.mode_var, list(MODES.keys()), 150)
        self.mode_menu.pack(side="left")

        ctk.CTkLabel(self, text="Model", font=F_UI_SMALL, text_color=COLORS["muted"]).pack(side="left", padx=(14, 6))
        self.model_menu = self._menu(self.model_var, [DEFAULT_MODEL], 190)
        self.model_menu.pack(side="left")

        # ---- right (unang pack = pinakakanan) ----
        self.run_btn = self._button("Run Review", handlers["run"], primary=True, width=104)
        self.run_btn.pack(side="right", padx=(4, 10), pady=8)
        self.stop_btn = self._button("Stop", handlers["stop"], width=56)
        self.stop_btn.configure(state="disabled")
        self.stop_btn.pack(side="right", padx=2, pady=8)
        self._separator("right")
        self.new_btn = self._button("New Session", handlers["new"], width=92)
        self.new_btn.pack(side="right", padx=2, pady=8)
        self.save_btn = self._button("Save Report", handlers["save"], width=90)
        self.save_btn.pack(side="right", padx=2, pady=8)
        self.copy_btn = self._button("Copy Last", handlers["copy"], width=78)
        self.copy_btn.pack(side="right", padx=2, pady=8)

    # ---- builders ----

    def _button(self, text, command, primary=False, width=80):
        return ctk.CTkButton(
            self, text=text, command=command, width=width, height=28, corner_radius=4, font=F_UI,
            fg_color=COLORS["accent"] if primary else "transparent",
            hover_color=COLORS["accent_hover"] if primary else COLORS["hover"],
            text_color="#FFFFFF" if primary else COLORS["text"],
            text_color_disabled=COLORS["disabled"],
        )

    def _menu(self, variable, values, width):
        return ctk.CTkOptionMenu(
            self, variable=variable, values=values, width=width, height=28, corner_radius=4,
            font=F_UI, dropdown_font=F_UI,
            fg_color=COLORS["input"], button_color=COLORS["input"], button_hover_color=COLORS["hover"],
            text_color=COLORS["text"], dropdown_fg_color=COLORS["surface"],
            dropdown_hover_color=COLORS["hover"], dropdown_text_color=COLORS["text"],
        )

    def _separator(self, side):
        ctk.CTkFrame(self, width=1, height=20, corner_radius=0, fg_color=COLORS["border"]).pack(
            side=side, padx=8, pady=13)

    # ---- public ----

    def get_mode(self):
        return self.mode_var.get()

    def get_model(self):
        return self.model_var.get()

    def set_models(self, names):
        self.model_menu.configure(values=names)
        if self.model_var.get() not in names:
            self.model_var.set(names[0])

    def set_generating(self, flag):
        busy = "disabled" if flag else "normal"
        self.run_btn.configure(state=busy)
        self.open_btn.configure(state=busy)
        self.clear_btn.configure(state=busy)
        self.new_btn.configure(state=busy)
        self.stop_btn.configure(state="normal" if flag else "disabled")