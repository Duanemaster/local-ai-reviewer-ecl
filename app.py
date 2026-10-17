import os
import re
import queue
import datetime
import threading
import tkinter.filedialog as fd
import tkinter.messagebox as mb

import customtkinter as ctk
import ollama

# ==========================================
# 1. CONFIG
# ==========================================

DEFAULT_MODEL = "qwen2.5:7b-instruct"
NUM_CTX = 8192              # Default ng Ollama ay 2048 lang -> natatrunc ang code. Dinagdagan natin.
TEMPERATURE = 0.2
MAX_HISTORY_MESSAGES = 8    # Ilang huling messages lang ang ipapadala sa model
MAX_FILE_BYTES = 300_000    # Limit sa file na ilo-load
WARN_CODE_CHARS = 20_000    # Warning kapag sobrang haba ng code (lampas context)

COLORS = {
    "bg": "#11111B",
    "header": "#1E1E2E",
    "panel": "#181825",
    "chat": "#1E1E2E",
    "border": "#313244",
    "text": "#CDD6F4",
    "muted": "#A6ADC8",
    "accent": "#89B4FA",
    "ok": "#A6E3A1",
    "busy": "#F9E2AF",
    "danger": "#F38BA8",
    "neutral_btn": "#45475A",
    "neutral_hover": "#585B70",
}

BASE_PROMPT = """You are ECL, an expert Senior Software Engineer and Code Reviewer.
Focus on architecture, logic bugs, security, and performance. Be highly analytical.
Categorize every finding by severity using exactly one of these labels at the start of the line: Bug, Warning, Suggestion.

STRICT ACCURACY RULES (anti-hallucination):
1. Report ONLY issues that are directly visible in the code provided. Never invent errors, functions, variables, files, or libraries that are not in the code.
2. For every finding, cite the line number (the line numbers shown are for reference only and are not part of the source) and quote the relevant snippet.
3. If you cannot verify something because it depends on code you cannot see, say so explicitly instead of guessing.
4. If the code has no real problems in the requested focus area, say clearly that no issues were found. Do not pad the review with fake findings.
5. Do not claim that code will crash or fail unless you can explain the exact reason from the given code.
6. When proposing a fix, keep it minimal and show only the corrected lines.

LANGUAGE AND STYLE:
Provide your explanation and feedback strictly in Taglish (Tagalog-English mix).
DO NOT use emojis. Be extremely professional and direct."""

MODES = {
    "General Review": "Review the code across architecture, logic, security, and performance.",
    "Bugs and Logic": "Focus ONLY on logic errors, edge cases, and runtime bugs.",
    "Security": "Focus ONLY on security vulnerabilities (injection, unsafe input handling, secrets, auth, unsafe file/network use).",
    "Performance": "Focus ONLY on performance problems (complexity, blocking calls, memory, redundant work).",
    "Architecture": "Focus ONLY on structure, separation of concerns, maintainability, and naming.",
}

SEVERITY_RE = re.compile(r"^(\W*)(Bug|Warning|Suggestion)\b", re.IGNORECASE)

WELCOME = (
    "ECL is ready.\n"
    "Paste or open a file on the left, choose a review mode, then press Enter to start the review.\n"
    "Shift+Enter for a new line in the instruction box.\n\n"
)


# ==========================================
# 2. APP STATE
# ==========================================

events = queue.Queue()          # worker thread -> UI thread
state = {
    "generating": False,
    "phase": "ready",           # ready | analyzing | typing
    "dots": 0,
    "reply": "",
    "reply_start": None,
    "pending_user": None,       # (short text) na ilalagay sa history kapag natapos
    "history": [],              # {'role','content'} - compact lang (walang buong code)
    "transcript": [],           # para sa Save Report
    "last_reply": "",
    "stop_event": None,
    "loaded_name": None,
}


# ==========================================
# 3. AI WORKER (background thread, walang UI calls dito)
# ==========================================

def ai_worker(msgs, model, stop_event):
    try:
        stream = ollama.chat(
            model=model,
            messages=msgs,
            stream=True,
            options={"temperature": TEMPERATURE, "num_ctx": NUM_CTX},
        )
        for chunk in stream:
            if stop_event.is_set():
                break
            events.put(("token", chunk["message"]["content"]))
        events.put(("done", stop_event.is_set()))
    except Exception as e:
        events.put(("error", str(e)))


def fetch_models_worker():
    try:
        resp = ollama.list()
        models = getattr(resp, "models", None)
        if models is None and isinstance(resp, dict):
            models = resp.get("models", [])
        names = []
        for m in models or []:
            if isinstance(m, dict):
                n = m.get("model") or m.get("name")
            else:
                n = getattr(m, "model", None) or getattr(m, "name", None)
            if n:
                names.append(n)
        events.put(("models", names))
    except Exception:
        events.put(("models", []))


# ==========================================
# 4. UI HELPERS
# ==========================================

def set_status(text, color=None):
    status_label.configure(text=text, text_color=color or COLORS["muted"])


def chat_edit(fn):
    """Safe edit ng read-only chat box."""
    chat_box.configure(state="normal")
    try:
        fn()
    finally:
        chat_box.see("end")
        chat_box.configure(state="disabled")


def set_generating(flag):
    state["generating"] = flag
    send_btn.configure(state="disabled" if flag else "normal")
    stop_btn.configure(state="normal" if flag else "disabled")
    new_btn.configure(state="disabled" if flag else "normal")
    open_file_btn.configure(state="disabled" if flag else "normal")


def update_counter(event=None):
    text = code_editor.get("1.0", "end-1c")
    lines = text.count("\n") + 1 if text else 0
    counter_label.configure(text=f"Lines: {lines}   Characters: {len(text)}")


def number_lines(code):
    lines = code.split("\n")
    width = len(str(len(lines)))
    return "\n".join(f"{i + 1:>{width}} | {ln}" for i, ln in enumerate(lines))


def render_formatted(reply):
    """Linisin ang raw markdown at lagyan ng kulay ang severity at code blocks."""
    in_code = False
    for line in reply.strip("\n").split("\n"):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            chat_box.insert("end", line + "\n", "code")
            continue
        clean = re.sub(r"^#{1,6}\s*", "", line.replace("**", ""))
        m = SEVERITY_RE.match(clean)
        if m:
            tag = {"bug": "sev_bug", "warning": "sev_warn", "suggestion": "sev_sugg"}[m.group(2).lower()]
            chat_box.insert("end", clean[:m.start(2)], "text_body")
            chat_box.insert("end", clean[m.start(2):m.end(2)], tag)
            chat_box.insert("end", clean[m.end(2):] + "\n", "text_body")
        else:
            chat_box.insert("end", clean + "\n", "text_body")


# ==========================================
# 5. EVENT HANDLING (UI thread)
# ==========================================

def poll_events():
    try:
        while True:
            kind, payload = events.get_nowait()
            handle_event(kind, payload)
    except queue.Empty:
        pass
    app.after(30, poll_events)


def handle_event(kind, payload):
    if kind == "token":
        def add():
            if state["reply_start"] is None:
                state["phase"] = "typing"
                set_status("ECL is writing the review", COLORS["busy"])
                chat_box.insert("end", "ECL:\n", "bold_ecl")
                state["reply_start"] = chat_box.index("end-1c")
            state["reply"] += payload
            chat_box.insert("end", payload, "text_body")
        chat_edit(add)

    elif kind == "done":
        stopped = payload
        reply = state["reply"].strip()

        def finish():
            if reply:
                chat_box.delete(state["reply_start"], "end-1c")
                render_formatted(reply)
                if stopped:
                    chat_box.insert("end", "[Stopped by user]\n", "muted")
            chat_box.insert("end", "\n" + "-" * 60 + "\n\n", "muted")
        chat_edit(finish)

        if reply:
            state["history"].append({"role": "user", "content": state["pending_user"]})
            state["history"].append({"role": "assistant", "content": reply})
            state["transcript"].append(("ECL", reply))
            state["last_reply"] = reply
        reset_after_run("Stopped" if stopped else "ECL: Active and Ready")

    elif kind == "error":
        def show_err():
            if state["reply_start"] is None:
                chat_box.insert("end", "ECL:\n", "bold_ecl")
            chat_box.insert(
                "end",
                f"System Error: {payload}\n"
                "Check if Ollama is running and the selected model is installed "
                "(example: ollama pull qwen2.5:7b-instruct).\n\n",
                "sev_bug",
            )
        chat_edit(show_err)
        reset_after_run("Error - see feedback panel", COLORS["danger"])

    elif kind == "models":
        names = payload
        if names:
            model_menu.configure(values=names)
            if model_var.get() not in names:
                model_var.set(names[0])
            set_status("ECL: Active and Ready", COLORS["ok"])
        else:
            set_status("Ollama not reachable or no models found", COLORS["danger"])


def reset_after_run(status_text, color=None):
    state["phase"] = "ready"
    state["reply"] = ""
    state["reply_start"] = None
    state["pending_user"] = None
    state["stop_event"] = None
    set_generating(False)
    set_status(status_text, color or COLORS["ok"])


def animate_status():
    if state["phase"] == "analyzing":
        state["dots"] = (state["dots"] + 1) % 4
        set_status("ECL is analyzing" + "." * state["dots"], COLORS["busy"])
    app.after(400, animate_status)


# ==========================================
# 6. ACTIONS
# ==========================================

def open_file(event=None):
    if state["generating"]:
        return "break"
    path = fd.askopenfilename(
        title="Select Code File",
        filetypes=[
            ("All Files", "*.*"), ("Python", "*.py"), ("C#", "*.cs"), ("Java", "*.java"),
            ("JavaScript", "*.js"), ("TypeScript", "*.ts"), ("HTML/CSS", "*.html *.css"),
            ("SQL", "*.sql"),
        ],
    )
    if not path:
        return "break"
    try:
        if os.path.getsize(path) > MAX_FILE_BYTES:
            mb.showwarning("File too large", f"Max supported size is {MAX_FILE_BYTES // 1000} KB.")
            return "break"
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError as e:
        mb.showerror("Cannot open file", str(e))
        return "break"

    code_editor.delete("1.0", "end")
    code_editor.insert("end", content)
    state["loaded_name"] = os.path.basename(path)
    file_label.configure(text=state["loaded_name"])
    update_counter()
    set_status(f"File loaded: {state['loaded_name']}", COLORS["ok"])
    return "break"


def clear_code():
    code_editor.delete("1.0", "end")
    state["loaded_name"] = None
    file_label.configure(text="Untitled")
    update_counter()


def send_message(event=None):
    if state["generating"]:
        return "break"

    user_text = chat_input.get("1.0", "end-1c").strip()
    code_text = code_editor.get("1.0", "end-1c").strip()
    if not user_text and not code_text:
        return "break"

    if len(code_text) > WARN_CODE_CHARS:
        if not mb.askyesno(
            "Large input",
            "Malaki ang code. Maaaring hindi lahat magkasya sa context ng model at "
            "bumaba ang accuracy ng review.\n\nPatuloy pa rin?",
        ):
            return "break"

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

    mode = mode_var.get()
    system_prompt = BASE_PROMPT + "\n\nFOCUS MODE: " + MODES[mode]
    msgs = [{"role": "system", "content": system_prompt}]
    msgs += state["history"][-MAX_HISTORY_MESSAGES:]
    msgs.append({"role": "user", "content": full_prompt})

    def show_user():
        chat_box.insert("end", f"Duane  |  {mode}:\n{shown}\n\n", "bold_user")
    chat_edit(show_user)
    state["transcript"].append(("Duane", shown))

    chat_input.delete("1.0", "end")
    state["pending_user"] = short_prompt
    state["reply"] = ""
    state["reply_start"] = None
    state["phase"] = "analyzing"
    state["dots"] = 0
    state["stop_event"] = threading.Event()

    set_generating(True)
    threading.Thread(
        target=ai_worker, args=(msgs, model_var.get(), state["stop_event"]), daemon=True
    ).start()
    return "break"


def stop_generation():
    if state["stop_event"] is not None:
        state["stop_event"].set()
        set_status("Stopping...", COLORS["busy"])


def new_session():
    if state["generating"]:
        return
    if state["history"] and not mb.askyesno("New session", "Burahin ang current review history?"):
        return
    state["history"].clear()
    state["transcript"].clear()
    state["last_reply"] = ""
    def reset():
        chat_box.delete("1.0", "end")
        chat_box.insert("end", WELCOME, "text_body")
    chat_edit(reset)
    set_status("New session started", COLORS["ok"])


def copy_last():
    if not state["last_reply"]:
        set_status("Nothing to copy yet", COLORS["muted"])
        return
    app.clipboard_clear()
    app.clipboard_append(state["last_reply"])
    set_status("Last review copied to clipboard", COLORS["ok"])


def save_report():
    if not state["transcript"]:
        set_status("Nothing to save yet", COLORS["muted"])
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
        f"- Model: {model_var.get()}",
        f"- File: {state['loaded_name'] or 'Pasted code'}",
        "",
    ]
    for who, text in state["transcript"]:
        lines += [f"## {who}", text, ""]
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        set_status(f"Report saved: {os.path.basename(path)}", COLORS["ok"])
    except OSError as e:
        mb.showerror("Save failed", str(e))


# ==========================================
# 7. GUI LAYOUT
# ==========================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("ECL - Professional Code Reviewer")
app.geometry("1200x760")
app.minsize(980, 620)
app.configure(fg_color=COLORS["bg"])

app.grid_rowconfigure(1, weight=1)
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)

model_var = ctk.StringVar(value=DEFAULT_MODEL)
mode_var = ctk.StringVar(value="General Review")

# ---- Header ----
header = ctk.CTkFrame(app, height=56, corner_radius=0, fg_color=COLORS["header"])
header.grid(row=0, column=0, columnspan=2, sticky="ew")

ctk.CTkLabel(
    header, text="ECL  |  AI CODE REVIEWER", font=("Segoe UI", 16, "bold"), text_color=COLORS["accent"]
).pack(side="left", padx=(18, 20), pady=12)

ctk.CTkLabel(header, text="Model", font=("Segoe UI", 11), text_color=COLORS["muted"]).pack(side="left")
model_menu = ctk.CTkOptionMenu(
    header, variable=model_var, values=[DEFAULT_MODEL], width=190, height=28,
    fg_color=COLORS["panel"], button_color=COLORS["neutral_btn"], button_hover_color=COLORS["neutral_hover"],
)
model_menu.pack(side="left", padx=(6, 16))

ctk.CTkLabel(header, text="Review Mode", font=("Segoe UI", 11), text_color=COLORS["muted"]).pack(side="left")
mode_menu = ctk.CTkOptionMenu(
    header, variable=mode_var, values=list(MODES.keys()), width=160, height=28,
    fg_color=COLORS["panel"], button_color=COLORS["neutral_btn"], button_hover_color=COLORS["neutral_hover"],
)
mode_menu.pack(side="left", padx=(6, 0))

status_label = ctk.CTkLabel(
    header, text="Connecting to Ollama...", font=("Consolas", 12, "italic"), text_color=COLORS["muted"]
)
status_label.pack(side="right", padx=20)

# ---- Left panel (code) ----
left = ctk.CTkFrame(app, fg_color="transparent")
left.grid(row=1, column=0, sticky="nsew", padx=(15, 7), pady=(12, 6))

left_head = ctk.CTkFrame(left, fg_color="transparent")
left_head.pack(fill="x", pady=(0, 6))
ctk.CTkLabel(left_head, text="CODE EDITOR", font=("Segoe UI", 12, "bold"), text_color=COLORS["muted"]).pack(side="left")
file_label = ctk.CTkLabel(left_head, text="Untitled", font=("Consolas", 11), text_color=COLORS["accent"])
file_label.pack(side="right")

code_editor = ctk.CTkTextbox(
    left, font=("Consolas", 14), wrap="none", border_width=1,
    border_color=COLORS["border"], fg_color=COLORS["panel"], undo=True,
)
code_editor.pack(fill="both", expand=True)
code_editor.bind("<KeyRelease>", update_counter)

left_bar = ctk.CTkFrame(left, fg_color="transparent")
left_bar.pack(fill="x", pady=(10, 0))
open_file_btn = ctk.CTkButton(
    left_bar, text="Open File", width=100, fg_color=COLORS["neutral_btn"],
    hover_color=COLORS["neutral_hover"], command=open_file,
)
open_file_btn.pack(side="left")
ctk.CTkButton(
    left_bar, text="Clear", width=80, fg_color=COLORS["neutral_btn"],
    hover_color=COLORS["neutral_hover"], command=clear_code,
).pack(side="left", padx=(8, 0))
counter_label = ctk.CTkLabel(left_bar, text="Lines: 0   Characters: 0", font=("Consolas", 11), text_color=COLORS["muted"])
counter_label.pack(side="right")

# ---- Right panel (feedback) ----
right = ctk.CTkFrame(app, fg_color="transparent")
right.grid(row=1, column=1, sticky="nsew", padx=(7, 15), pady=(12, 6))

right_head = ctk.CTkFrame(right, fg_color="transparent")
right_head.pack(fill="x", pady=(0, 6))
ctk.CTkLabel(right_head, text="REVIEW FEEDBACK", font=("Segoe UI", 12, "bold"), text_color=COLORS["muted"]).pack(side="left")

new_btn = ctk.CTkButton(
    right_head, text="New Session", width=95, height=26, fg_color=COLORS["neutral_btn"],
    hover_color=COLORS["neutral_hover"], command=new_session,
)
new_btn.pack(side="right")
ctk.CTkButton(
    right_head, text="Save Report", width=95, height=26, fg_color=COLORS["neutral_btn"],
    hover_color=COLORS["neutral_hover"], command=save_report,
).pack(side="right", padx=(0, 6))
ctk.CTkButton(
    right_head, text="Copy Last", width=85, height=26, fg_color=COLORS["neutral_btn"],
    hover_color=COLORS["neutral_hover"], command=copy_last,
).pack(side="right", padx=(0, 6))

chat_box = ctk.CTkTextbox(
    right, font=("Consolas", 14), wrap="word", border_width=1,
    border_color=COLORS["border"], fg_color=COLORS["chat"],
)
chat_box.pack(fill="both", expand=True)

# Tags (sa underlying tk Text para makapag-set ng font/background)
_t = chat_box._textbox
_t.tag_config("bold_user", foreground=COLORS["accent"], font=("Consolas", 14, "bold"))
_t.tag_config("bold_ecl", foreground=COLORS["ok"], font=("Consolas", 14, "bold"))
_t.tag_config("text_body", foreground=COLORS["text"])
_t.tag_config("muted", foreground=COLORS["border"])
_t.tag_config("code", foreground="#F9E2AF", background="#11111B", font=("Consolas", 13), lmargin1=12, lmargin2=12)
_t.tag_config("sev_bug", foreground=COLORS["danger"], font=("Consolas", 14, "bold"))
_t.tag_config("sev_warn", foreground=COLORS["busy"], font=("Consolas", 14, "bold"))
_t.tag_config("sev_sugg", foreground="#94E2D5", font=("Consolas", 14, "bold"))

chat_box.configure(state="normal")
chat_box.insert("end", WELCOME, "text_body")
chat_box.configure(state="disabled")

# ---- Input area ----
input_frame = ctk.CTkFrame(right, fg_color="transparent")
input_frame.pack(fill="x", pady=(10, 0))

chat_input = ctk.CTkTextbox(
    input_frame, height=62, font=("Consolas", 14), border_width=1,
    border_color=COLORS["border"], fg_color=COLORS["panel"],
)
chat_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
chat_input.bind("<Return>", send_message)
chat_input.bind("<Shift-Return>", lambda e: None)   # default newline behavior

btn_col = ctk.CTkFrame(input_frame, fg_color="transparent")
btn_col.pack(side="right")
send_btn = ctk.CTkButton(
    btn_col, text="Review Code", width=110, height=34,
    font=("Segoe UI", 12, "bold"), command=send_message,
)
send_btn.pack(pady=(0, 4))
stop_btn = ctk.CTkButton(
    btn_col, text="Stop", width=110, height=24, state="disabled",
    fg_color=COLORS["neutral_btn"], hover_color=COLORS["danger"], command=stop_generation,
)
stop_btn.pack()

# ---- Footer ----
footer = ctk.CTkFrame(app, height=26, corner_radius=0, fg_color=COLORS["header"])
footer.grid(row=2, column=0, columnspan=2, sticky="ew")
ctk.CTkLabel(
    footer,
    text="Enter: Review   |   Shift+Enter: New line   |   Ctrl+O: Open file",
    font=("Consolas", 10), text_color=COLORS["muted"],
).pack(side="left", padx=15, pady=3)

app.bind("<Control-o>", open_file)

# ==========================================
# 8. START
# ==========================================

threading.Thread(target=fetch_models_worker, daemon=True).start()
poll_events()
animate_status()
app.mainloop()