"""Line number gutter para sa code editor."""
import tkinter as tk
import tkinter.font as tkfont

from ecl.theme import COLORS, F_MONO


class LineNumberGutter(tk.Canvas):
    def __init__(self, master, text_widget):
        super().__init__(master, width=48, bg=COLORS["editor"], highlightthickness=0, bd=0)
        self.text = text_widget
        self._font = tkfont.Font(font=F_MONO)
        self._width = 0

    def redraw(self):
        self.delete("all")
        total = int(self.text.index("end-1c").split(".")[0])
        digits = max(3, len(str(total)))
        width = self._font.measure("0") * digits + 22
        if width != self._width:
            self._width = width
            self.configure(width=width)

        current = int(self.text.index("insert").split(".")[0])
        index = self.text.index("@0,0")
        prev = -1
        while True:
            info = self.text.dlineinfo(index)
            if info is None:
                break
            line = int(index.split(".")[0])
            if line == prev:
                break
            prev = line
            color = COLORS["text"] if line == current else COLORS["gutter_text"]
            self.create_text(width - 12, info[1], anchor="ne", text=str(line),
                             font=self._font, fill=color)
            index = self.text.index(f"{index}+1line")