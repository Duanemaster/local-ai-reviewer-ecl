"""Bottom status bar: status dot, cursor position, counts, model."""
import tkinter as tk

import customtkinter as ctk

from ecl.theme import COLORS, F_UI_SMALL

LEVEL_COLORS = {
    "idle": COLORS["muted"],
    "ok": COLORS["ok"],
    "busy": COLORS["busy"],
    "error": COLORS["danger"],
}


class StatusBar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, height=26, corner_radius=0, fg_color=COLORS["statusbar"])
        self.pack_propagate(False)
        ctk.CTkFrame(self, height=1, corner_radius=0, fg_color=COLORS["border"]).pack(side="top", fill="x")

        self.dot = tk.Canvas(self, width=10, height=10, bg=COLORS["statusbar"], highlightthickness=0, bd=0)
        self.dot_id = self.dot.create_oval(1, 1, 9, 9, fill=COLORS["muted"], outline="")
        self.dot.pack(side="left", padx=(12, 6))
        self.status_label = ctk.CTkLabel(self, text="Connecting to Ollama...", font=F_UI_SMALL,
                                         text_color=COLORS["muted"])
        self.status_label.pack(side="left")

        self.model_label = self._info("")
        self.counts_label = self._info("Lines 0   Chars 0")
        self.cursor_label = self._info("Ln 1, Col 1")

    def _info(self, text):
        label = ctk.CTkLabel(self, text=text, font=F_UI_SMALL, text_color=COLORS["muted"])
        label.pack(side="right", padx=(0, 16))
        return label

    def set_status(self, text, level="idle"):
        color = LEVEL_COLORS.get(level, COLORS["muted"])
        self.status_label.configure(text=text, text_color=COLORS["text"] if level != "idle" else COLORS["muted"])
        self.dot.itemconfigure(self.dot_id, fill=color)

    def set_cursor(self, line, col):
        self.cursor_label.configure(text=f"Ln {line}, Col {col}")

    def set_counts(self, lines, chars):
        self.counts_label.configure(text=f"Lines {lines}   Chars {chars}")

    def set_model(self, name):
        self.model_label.configure(text=name)