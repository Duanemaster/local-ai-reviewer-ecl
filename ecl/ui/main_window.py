"""Main window: binds ang lahat ng panels at humahawak ng actions + events."""
import datetime
import os
import queue
import threading
import tkinter as tk
import tkinter.filedialog as fd

import customtkinter as ctk

from ecl.config import (
    APP_FULL_NAME, FILE_TYPES, ICON_PATH, MAX_FILE_BYTES, MAX_HISTORY_MESSAGES,
    WARN_CODE_CHARS, WINDOW_MIN_H, WINDOW_MIN_W, WINDOW_SIZE,
)
from ecl.formatting import number_lines
from ecl.ollama_service import OllamaService
from ecl.paths import resource_path
from ecl.prompts import build_system_prompt
from ecl.state import Session
from ecl.theme import COLORS
from ecl.ui.dialogs import confirm, notify
from ecl.ui.editor_panel import EditorPanel
from ecl.ui.review_panel import ReviewPanel
from ecl.ui.statusbar import StatusBar
from ecl.ui.toolbar import Toolbar


class MainWindow(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        super().__init__()

        self.title(APP_FULL_NAME)
        self.geometry(WINDOW_SIZE)
        self.minsize(WINDOW_MIN_W, WINDOW_MIN_H)
        self.configure(fg_color=COLORS["bg"])
        self._apply_icon()

        self.session = Session()
        self.events = queue.Queue()
        self.service = OllamaService(self.events)

        self._build()
        self._bind_keys()

        self.status.set_status("Connecting to Ollama...", "idle")
        self.service.fetch_models()
        self.after(30, self._poll_events)
        self.after(400, self._animate_status)

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _apply_icon(self):
        ico = resource_path(ICON_PATH)
        if not os.path.exists(ico):
            return

        def set_icon():
            try:
                self.iconbitmap(ico)
            except tk.TclError:
                pass

        set_icon()
        # Ni-re-reset ng customtkinter ang icon after ~200ms, kaya ulitin
        self.after(300, set_icon)

    def _build(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.toolbar = Toolbar(self, handlers={
            "open": self.open_file,
            "clear": self.clear_code,
            "run": self.run_review,
            "stop": self.stop_generation,
            "new": self.new_session,
            "save": self.save_report,
            "copy": self.copy_last,
        })
        self.toolbar.grid(row=0, column=0, sticky="ew")

        self.paned = tk.PanedWindow(self, orient="horizontal", sashwidth=5, sashrelief="flat",
                                    bg=COLORS["border"], bd=0, opaqueresize=True)
        self.paned.grid(row=1, column=0, sticky="nsew")

        self.editor = EditorPanel(self.paned, on_edit=self._on_editor_edit, on_cursor=self._on_editor_cursor)
        self.review = ReviewPanel(self.paned, on_submit=self.run_review, on_goto=self._goto_line)
        self.paned.add(self.editor, minsize=380, stretch="always")
        self.paned.add(self.review, minsize=420, stretch="always")

        self.status = StatusBar(self)
        self.status.grid(row=2, column=0, sticky="ew")

        self.toolbar.model_var.trace_add("write", lambda *a: self.status.set_model(self.toolbar.get_model()))
        self.status.set_model(self.toolbar.get_model())

        self.after(150, lambda: self.paned.sash_place(0, self.winfo_width() // 2, 0))

    def _bind_keys(self):
        self.bind("<Control-o>", lambda e: self.open_file() or "break")
        self.bind("<Control-s>", lambda e: self.save_report() or "break")
        self.bind("<F5>", lambda e: self.run_review() or "break")
        self.bind("<Escape>", lambda e: self.stop_generation())

    # ------------------------------------------------------------------
    # Editor callbacks
    # ------------------------------------------------------------------

    def _on_editor_edit(self, lines, chars):
        self.status.set_counts(lines, chars)

    def _on_editor_cursor(self, line, col):
        self.status.set_cursor(line, col)

    def _goto_line(self, start, end=None):
        """Tinatawag kapag na-click ang line reference sa review."""
        label = f"line {start}" + (f"-{end}" if end and end > start else "")
        if self.editor.goto_line(start, end):
            self.status.set_status(f"Jumped to {label}", "ok")
        else:
            self.status.set_status(f"{label.capitalize()} is not in the editor", "idle")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def open_file(self):
        if self.session.generating:
            return
        path = fd.askopenfilename(title="Open Code File", filetypes=FILE_TYPES)
        if not path:
            return
        try:
            if os.path.getsize(path) > MAX_FILE_BYTES:
                notify(self, "File too large",
                       f"Max supported size is {MAX_FILE_BYTES // 1000} KB.", kind="warning")
                return
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError as e:
            notify(self, "Cannot open file", str(e), kind="error")
            return

        name = os.path.basename(path)
        self.session.loaded_name = name
        self.editor.set_code(content, name)
        self.status.set_status(f"Loaded {name}", "ok")

    def clear_code(self):
        self.session.loaded_name = None
        self.editor.clear()

    def run_review(self):
        s = self.session
        if s.generating:
            return

        user_text = self.review.get_instruction()
        code_text = self.editor.get_code().strip()
        if not user_text and not code_text:
            return

        if len(code_text) > WARN_CODE_CHARS:
            if not confirm(
                self, "Large input",
                "Malaki ang code. Maaaring hindi lahat magkasya sa context ng model at "
                "bumaba ang accuracy ng review.",
                yes="Continue", no="Cancel",
            ):
                return

        parts = []
        if code_text:
            n = code_text.count("\n") + 1
            parts.append(
                f"Code to review ({n} lines). Line numbers are for reference only and are not part of the source:\n"
                f"```\n{number_lines(code_text)}\n```"
            )
        if user_text:
            parts.append(f"Instruction: {user_text}")
            shown = user_text
        else:
            parts.append("Review the code above. Report only issues that are verifiable in the provided code.")
            shown = "[Code submitted for review]"

        full_prompt = "\n".join(parts)
        short_prompt = (f"[Code attached earlier: {code_text.count(chr(10)) + 1} lines] " if code_text else "") + (
            user_text or "Review the code."
        )

        mode = self.toolbar.get_mode()
        messages = [{"role": "system", "content": build_system_prompt(mode)}]
        messages += s.history[-MAX_HISTORY_MESSAGES:]
        messages.append({"role": "user", "content": full_prompt})

        self.review.append_user(mode, shown)
        s.transcript.append(("You", shown))
        self.review.clear_instruction()

        s.pending_user = short_prompt
        s.reply = ""
        s.reply_started = False
        s.phase = "analyzing"
        s.dots = 0
        s.generating = True
        s.stop_event = threading.Event()

        self.toolbar.set_generating(True)
        self.service.stream_review(messages, self.toolbar.get_model(), s.stop_event)

    def stop_generation(self):
        s = self.session
        if s.generating and s.stop_event is not None:
            s.stop_event.set()
            self.status.set_status("Stopping...", "busy")

    def new_session(self):
        s = self.session
        if s.generating:
            return
        if s.history and not confirm(
            self, "New session",
            "Are you sure? Hindi na mababalik 'yan bossing",
            yes="Clear history", no="Cancel", danger=True,
        ):
            return
        s.clear_history()
        self.review.clear()
        self.status.set_status("New session started", "ok")

    def copy_last(self):
        if not self.session.last_reply:
            self.status.set_status("Nothing to copy yet", "idle")
            return
        self.clipboard_clear()
        self.clipboard_append(self.session.last_reply)
        self.status.set_status("Last review copied to clipboard", "ok")

    def save_report(self):
        s = self.session
        if not s.transcript:
            self.status.set_status("Nothing to save yet", "idle")
            return
        default = f"ECL_Review_{datetime.datetime.now():%Y%m%d_%H%M}.md"
        path = fd.asksaveasfilename(
            title="Save Review Report", defaultextension=".md", initialfile=default,
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt")],
        )
        if not path:
            return
        lines = [
            "# ECL Code Review Report",
            f"- Date: {datetime.datetime.now():%Y-%m-%d %H:%M}",
            f"- Model: {self.toolbar.get_model()}",
            f"- File: {s.loaded_name or 'Pasted code'}",
            "",
        ]
        for who, text in s.transcript:
            lines += [f"## {who}", text, ""]
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            self.status.set_status(f"Report saved: {os.path.basename(path)}", "ok")
        except OSError as e:
            notify(self, "Save failed", str(e), kind="error")

    # ------------------------------------------------------------------
    # Events from worker thread
    # ------------------------------------------------------------------

    def _poll_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                self._handle_event(kind, payload)
        except queue.Empty:
            pass
        self.after(30, self._poll_events)

    def _handle_event(self, kind, payload):
        s = self.session

        if kind == "token":
            if not s.reply_started:
                s.reply_started = True
                s.phase = "typing"
                self.status.set_status("Writing review", "busy")
                self.review.begin_reply()
            s.reply += payload
            self.review.add_token(payload)

        elif kind == "done":
            stopped = payload
            reply = s.reply.strip()
            self.review.finish_reply(reply, stopped)
            if reply:
                s.history.append({"role": "user", "content": s.pending_user})
                s.history.append({"role": "assistant", "content": reply})
                s.transcript.append(("ECL", reply))
                s.last_reply = reply
            self._finish_run("Stopped" if stopped else "Ready", "idle" if stopped else "ok")

        elif kind == "error":
            self.review.show_error(payload)
            self._finish_run("Error - see review panel", "error")

        elif kind == "models":
            if payload:
                self.toolbar.set_models(payload)
                self.status.set_model(self.toolbar.get_model())
                self.status.set_status("Ready", "ok")
            else:
                self.status.set_status("Ollama not reachable or no models found", "error")

    def _finish_run(self, text, level):
        self.session.reset_run()
        self.session.generating = False
        self.toolbar.set_generating(False)
        self.status.set_status(text, level)

    def _animate_status(self):
        s = self.session
        if s.phase == "analyzing":
            s.dots = (s.dots + 1) % 4
            self.status.set_status("Analyzing" + "." * s.dots, "busy")
        self.after(400, self._animate_status)