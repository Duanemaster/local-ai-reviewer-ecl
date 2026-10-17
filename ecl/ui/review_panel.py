"""Kanang panel: review output (report style) + instruction box."""
import tkinter as tk
from contextlib import contextmanager

import customtkinter as ctk

from ecl.formatting import clean_markdown, match_severity, split_line_refs
from ecl.theme import COLORS, F_MONO, F_MONO_BOLD, F_MONO_SMALL, F_UI, F_UI_SMALL


class ReviewPanel(ctk.CTkFrame):
    def __init__(self, master, on_submit, on_goto=None):
        super().__init__(master, corner_radius=0, fg_color=COLORS["output"])
        self._reply_start = None
        self.on_goto = on_goto or (lambda start, end: None)
        self._link_count = 0
        self._link_tags = []

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ---- tab ----
        tab = ctk.CTkFrame(self, height=34, corner_radius=0, fg_color=COLORS["surface"])
        tab.grid(row=0, column=0, sticky="ew")
        tab.pack_propagate(False)
        ctk.CTkFrame(tab, height=2, corner_radius=0, fg_color=COLORS["accent"]).pack(side="bottom", fill="x")
        ctk.CTkLabel(tab, text="Review", font=F_UI, text_color=COLORS["text"]).pack(side="left", padx=14)

        # ---- output ----
        body = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["output"])
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        self.text = tk.Text(
            body, wrap="word", state="disabled", font=F_MONO, bd=0, relief="flat", highlightthickness=0,
            bg=COLORS["output"], fg=COLORS["text"], insertbackground=COLORS["text"],
            selectbackground=COLORS["selection"], inactiveselectbackground=COLORS["selection"],
            padx=16, pady=12, spacing1=2, spacing3=2,
        )
        self.vbar = ctk.CTkScrollbar(body, command=self.text.yview, width=12,
                                     fg_color=COLORS["output"], button_color=COLORS["input"],
                                     button_hover_color=COLORS["hover"])
        self.text.configure(yscrollcommand=self.vbar.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self._configure_tags()

        self.empty_label = ctk.CTkLabel(
            body, text="No review yet.\nLoad code on the left, then press Run Review (F5).",
            font=F_UI, text_color=COLORS["muted"], fg_color=COLORS["output"], justify="center",
        )
        self.empty_label.place(relx=0.5, rely=0.45, anchor="center")

        # ---- instruction box ----
        bottom = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["surface"])
        bottom.grid(row=2, column=0, sticky="ew")
        ctk.CTkFrame(bottom, height=1, corner_radius=0, fg_color=COLORS["border"]).pack(fill="x")
        head = ctk.CTkFrame(bottom, fg_color="transparent")
        head.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(head, text="Instruction (optional)", font=F_UI_SMALL, text_color=COLORS["muted"]).pack(side="left")
        ctk.CTkLabel(head, text="Enter: run   |   Shift+Enter: new line", font=F_UI_SMALL,
                     text_color=COLORS["disabled"]).pack(side="right")

        box = ctk.CTkFrame(bottom, corner_radius=4, border_width=1, border_color=COLORS["border"],
                           fg_color=COLORS["editor"])
        box.pack(fill="x", padx=12, pady=(0, 12))
        self.input = tk.Text(
            box, height=3, wrap="word", font=F_MONO, bd=0, relief="flat", highlightthickness=0,
            bg=COLORS["editor"], fg=COLORS["text"], insertbackground=COLORS["text"],
            selectbackground=COLORS["selection"], padx=6, pady=4,
        )
        self.input.pack(fill="x", padx=4, pady=3)
        self.input.bind("<Return>", lambda e: (on_submit(), "break")[1])
        self.input.bind("<Shift-Return>", lambda e: None)   # default newline

    # ---- setup ----

    def _configure_tags(self):
        t = self.text
        t.tag_configure("body", foreground=COLORS["text"])
        t.tag_configure("user_head", foreground=COLORS["accent_text"], font=F_MONO_BOLD)
        t.tag_configure("reply_head", foreground=COLORS["ok"], font=F_MONO_BOLD)
        t.tag_configure("code", foreground=COLORS["code_fg"], background=COLORS["code_bg"],
                        font=F_MONO_SMALL, lmargin1=16, lmargin2=16)
        t.tag_configure("code_inline", foreground=COLORS["code_fg"], background=COLORS["inline_bg"])
        t.tag_configure("sev_bug", foreground="#FFFFFF", background=COLORS["danger"], font=F_MONO_BOLD)
        t.tag_configure("sev_warn", foreground="#1E1E1E", background=COLORS["busy"], font=F_MONO_BOLD)
        t.tag_configure("sev_sugg", foreground="#FFFFFF", background=COLORS["info"], font=F_MONO_BOLD)
        t.tag_configure("muted", foreground=COLORS["muted"])
        t.tag_configure("rule", foreground=COLORS["border"])
        t.tag_configure("error", foreground=COLORS["danger"])

    @contextmanager
    def _unlocked(self):
        self.text.configure(state="normal")
        try:
            yield
        finally:
            self.text.see("end")
            self.text.configure(state="disabled")

    def _rule(self):
        self.text.insert("end", "\n" + "-" * 56 + "\n\n", "rule")

    def _insert_link(self, label, start, end):
        """Clickable line reference: pupunta ang editor sa line na iyon."""
        self._link_count += 1
        tag = f"link_{self._link_count}"
        self._link_tags.append(tag)
        self.text.tag_configure(tag, foreground=COLORS["link"], underline=True)
        self.text.tag_bind(tag, "<Button-1>", lambda e, s=start, en=end: self.on_goto(s, en))
        self.text.tag_bind(tag, "<Enter>", lambda e: self.text.configure(cursor="hand2"))
        self.text.tag_bind(tag, "<Leave>", lambda e: self.text.configure(cursor=""))
        self.text.insert("end", label, tag)

    def _insert_with_links(self, text, base_tag):
        for segment, start, end in split_line_refs(text):
            if start is None:
                self.text.insert("end", segment, base_tag)
            else:
                self._insert_link(segment, start, end)

    def _insert_inline(self, text, base_tag):
        """Hatiin sa `backticks` para maging inline code; ang labas ay sinusuri para sa line links."""
        for i, part in enumerate(text.split("`")):
            if not part:
                continue
            if i % 2:
                self.text.insert("end", part, "code_inline")
            else:
                self._insert_with_links(part, base_tag)

    def _render(self, reply):
        in_code = False
        for line in reply.strip("\n").split("\n"):
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                self.text.insert("end", line + "\n", "code")
                continue
            clean = clean_markdown(line)
            sev = match_severity(clean)
            if sev:
                prefix, label, rest, tag = sev
                self._insert_inline(prefix, "body")
                self.text.insert("end", f" {label.upper()} ", tag)
                self._insert_inline(rest + "\n", "body")
            else:
                self._insert_inline(clean + "\n", "body")

    # ---- public API ----

    def get_instruction(self):
        return self.input.get("1.0", "end-1c").strip()

    def clear_instruction(self):
        self.input.delete("1.0", "end")

    def append_user(self, mode, text):
        self.empty_label.place_forget()
        with self._unlocked():
            self.text.insert("end", f"You  |  {mode}\n", "user_head")
            self.text.insert("end", text + "\n\n", "body")

    def begin_reply(self):
        with self._unlocked():
            self.text.insert("end", "Review\n", "reply_head")
            self._reply_start = self.text.index("end-1c")

    def add_token(self, token):
        with self._unlocked():
            self.text.insert("end", token, "body")

    def finish_reply(self, reply, stopped):
        with self._unlocked():
            if reply and self._reply_start:
                self.text.delete(self._reply_start, "end-1c")
                self._render(reply)
                if stopped:
                    self.text.insert("end", "[Stopped by user]\n", "muted")
            self._rule()
        self._reply_start = None

    def show_error(self, message):
        with self._unlocked():
            if self._reply_start is None:
                self.text.insert("end", "Review\n", "reply_head")
            self.text.insert(
                "end",
                f"Error: {message}\n"
                "Check if Ollama is running and the selected model is installed "
                "(example: ollama pull qwen2.5:7b-instruct).\n",
                "error",
            )
            self._rule()
        self._reply_start = None

    def clear(self):
        with self._unlocked():
            self.text.delete("1.0", "end")
        for tag in self._link_tags:
            self.text.tag_delete(tag)
        self._link_tags.clear()
        self._reply_start = None
        self.empty_label.place(relx=0.5, rely=0.45, anchor="center")