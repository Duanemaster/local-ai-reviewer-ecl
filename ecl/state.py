"""Session state ng app (walang UI code dito)."""
import threading
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Session:
    generating: bool = False
    phase: str = "ready"                 # ready | analyzing | typing
    dots: int = 0
    reply: str = ""
    reply_started: bool = False
    pending_user: Optional[str] = None   # maikling bersyon na ilalagay sa history
    history: list = field(default_factory=list)      # {'role','content'} - compact lang
    transcript: list = field(default_factory=list)   # para sa Save Report
    last_reply: str = ""
    stop_event: Optional[threading.Event] = None
    loaded_name: Optional[str] = None

    def reset_run(self):
        self.phase = "ready"
        self.reply = ""
        self.reply_started = False
        self.pending_user = None
        self.stop_event = None

    def clear_history(self):
        self.history.clear()
        self.transcript.clear()
        self.last_reply = ""