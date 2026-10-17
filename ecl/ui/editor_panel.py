"""Kaliwang panel: code editor na may line numbers at current-line highlight."""
import tkinter as tk

import customtkinter as ctk

from ecl.theme import COLORS, F_MONO, F_UI
from ecl.ui.gutter import LineNumberGutter


class EditorPanel(ctk.CTkFrame):
    def __init__(self, master, on_edit=None, on_cursor=None):
        super().__init__(master, corner_radius=0, fg_color=COLORS["editor"])
        self.on_edit = on_edit
        self.on_cursor = on_cursor
        self._flash_job = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ---- file tab ----
        tab = ctk.CTkFrame(self, height=34, corner_radius=0, fg_color=COLORS["surface"])
        tab.grid(row=0, column=0, sticky="ew")
        tab.pack_propagate(False)
        ctk.CTkFrame(tab, height=2, corner_radius=0, fg_color=COLORS["accent"]).pack(side="bottom", fill="x")
        self.title_label = ctk.CTkLabel(tab, text="Untitled", font=F_UI, text_color=COLORS["text"])
        self.title_label.pack(side="left", padx=14)

        # ---- editor body ----
        body = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["editor"])
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        self.text = tk.Text(
            body, wrap="none", undo=True, font=F_MONO, bd=0, relief="flat", highlightthickness=0,
            bg=COLORS["editor"], fg=COLORS["text"], insertbackground=COLORS["text"],
            selectbackground=COLORS["selection"], inactiveselectbackground=COLORS["selection"],
            padx=8, pady=6,
        )
        self.gutter = LineNumberGutter(body, self.text)
        self.vbar = ctk.CTkScrollbar(body, command=self.text.yview, width=12,
                                     fg_color=COLORS["editor"], button_color=COLORS["input"],
                                     button_hover_color=COLORS["hover"])
        self.hbar = ctk.CTkScrollbar(body, orientation="horizontal", command=self.text.xview, height=12,
                                     fg_color=COLORS["editor"], button_color=COLORS["input"],
                                     button_hover_color=COLORS["hover"])
        self.text.configure(yscrollcommand=self._on_yscroll, xscrollcommand=self.hbar.set)

        self.gutter.grid(row=0, column=0, sticky="ns")
        self.text.grid(row=0, column=1, sticky="nsew")
        self.vbar.grid(row=0, column=2, sticky="ns")
        self.hbar.grid(row=1, column=1, sticky="ew")

        self.text.tag_configure("current_line", background=COLORS["current_line"])
        self.text.tag_lower("current_line")
        self.text.tag_configure("goto_flash", background=COLORS["flash"])

        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<KeyRelease>", self._on_cursor_event)
        self.text.bind("<ButtonRelease-1>", self._on_cursor_event)
        self.text.bind("<Configure>", lambda e: self.gutter.redraw())
        self.text.bind("<Tab>", self._insert_tab)
        self.text.bind("<Control-a>", self._select_all)

        self.after(50, self._refresh)

    # ---- internal ----

    def _on_yscroll(self, first, last):
        self.vbar.set(first, last)
        self.gutter.redraw()

    def _on_modified(self, event=None):
        if self.text.edit_modified():
            self.text.edit_modified(False)
            self._refresh()

    def _on_cursor_event(self, event=None):
        self._update_cursor()

    def _insert_tab(self, event=None):
        self.text.insert("insert", "    ")
        return "break"

    def _select_all(self, event=None):
        self.text.tag_add("sel", "1.0", "end-1c")
        return "break"

    def _update_cursor(self):
        self.text.tag_remove("current_line", "1.0", "end")
        self.text.tag_add("current_line", "insert linestart", "insert lineend+1c")
        line, col = self.text.index("insert").split(".")
        if self.on_cursor:
            self.on_cursor(int(line), int(col) + 1)
        self.gutter.redraw()

    def _refresh(self):
        code = self.get_code()
        lines = code.count("\n") + 1 if code else 0
        if self.on_edit:
            self.on_edit(lines, len(code))
        self._update_cursor()

    def _clear_flash(self):
        self._flash_job = None
        self.text.tag_remove("goto_flash", "1.0", "end")

    # ---- public ----

    def get_code(self):
        return self.text.get("1.0", "end-1c")

    def set_code(self, content, name=None):
        self.text.delete("1.0", "end")
        self.text.insert("end", content)
        self.text.edit_reset()
        self.text.mark_set("insert", "1.0")
        self.text.see("1.0")
        self.set_title(name or "Untitled")
        self._refresh()

    def clear(self):
        self.set_code("")

    def set_title(self, name):
        self.title_label.configure(text=name)

    def goto_line(self, start, end=None):
        """I-scroll at i-flash ang line (o range). Return False kung wala sa editor."""
        total = int(self.text.index("end-1c").split(".")[0])
        if start < 1 or start > total:
            return False
        end = min(end, total) if end and end >= start else start

        if self._flash_job is not None:
            self.after_cancel(self._flash_job)
        self.text.tag_remove("goto_flash", "1.0", "end")
        self.text.tag_add("goto_flash", f"{start}.0", f"{end}.0 lineend+1c")

        self.text.mark_set("insert", f"{start}.0")
        self.text.yview(f"{max(1, start - 6)}.0")
        self.text.see(f"{start}.0")
        self._update_cursor()
        self._flash_job = self.after(2000, self._clear_flash)
        return True