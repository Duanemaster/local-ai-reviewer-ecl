"""Lahat ng settings na madalas baguhin. Dito ka mag-edit, hindi sa UI code."""

APP_NAME = "ECL"
APP_FULL_NAME = "ECL Code Reviewer"
APP_ID = "duane.ecl.codereviewer"      # Windows taskbar identity
VERSION = "0.2.0"

# --- Ollama ---
DEFAULT_MODEL = "qwen2.5:7b-instruct"
NUM_CTX = 8192              # Default ng Ollama ay 2048 lang -> natatrunc ang code
TEMPERATURE = 0.2
MAX_HISTORY_MESSAGES = 8    # Ilang huling messages lang ang ipapadala sa model

# --- Limits ---
MAX_FILE_BYTES = 300_000    # Limit sa file na ilo-load
WARN_CODE_CHARS = 20_000    # Warning kapag sobrang haba ng code

# --- Window ---
WINDOW_SIZE = "1240x780"
WINDOW_MIN_W = 1040
WINDOW_MIN_H = 620

# --- Files ---
ICON_PATH = "assets/ecl.ico"
FILE_TYPES = [
    ("All Files", "*.*"), ("Python", "*.py"), ("C#", "*.cs"), ("Java", "*.java"),
    ("JavaScript", "*.js"), ("TypeScript", "*.ts"), ("HTML/CSS", "*.html *.css"),
    ("SQL", "*.sql"),
]