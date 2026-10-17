"""Lahat ng usapan sa Ollama. Walang UI calls dito; events queue lang ang labasan."""
import threading

import ollama

from ecl.config import NUM_CTX, TEMPERATURE


class OllamaService:
    def __init__(self, events):
        self.events = events    # queue.Queue -> binabasa ng UI thread

    def stream_review(self, messages, model, stop_event):
        threading.Thread(
            target=self._stream_worker, args=(messages, model, stop_event), daemon=True
        ).start()

    def fetch_models(self):
        threading.Thread(target=self._models_worker, daemon=True).start()

    # ---- workers (background thread) ----

    def _stream_worker(self, messages, model, stop_event):
        try:
            stream = ollama.chat(
                model=model,
                messages=messages,
                stream=True,
                options={"temperature": TEMPERATURE, "num_ctx": NUM_CTX},
            )
            for chunk in stream:
                if stop_event.is_set():
                    break
                self.events.put(("token", chunk["message"]["content"]))
            self.events.put(("done", stop_event.is_set()))
        except Exception as e:
            self.events.put(("error", str(e)))

    def _models_worker(self):
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
            self.events.put(("models", names))
        except Exception:
            self.events.put(("models", []))