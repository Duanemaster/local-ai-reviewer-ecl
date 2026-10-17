"""Gumagawa ng assets/ecl.ico at assets/ecl.png. Run: python tools/make_icon.py"""
import os

from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def build(size=1024):
    S = size
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    pad, radius = S * 0.05, S * 0.22
    box = [pad, pad, S - pad, S - pad]
    d.rounded_rectangle(box, radius=radius, fill="#18212C")
    d.rounded_rectangle(box, radius=radius, outline="#2F3E52", width=int(S * 0.014))

    def stroke(points, color, width):
        pts = [(x * S, y * S) for x, y in points]
        d.line(pts, fill=color, width=int(width), joint="curve")
        for x, y in (pts[0], pts[-1]):
            r = width / 2
            d.ellipse([x - r, y - r, x + r, y + r], fill=color)

    w = S * 0.072
    bracket = "#8FA6C2"
    stroke([(0.34, 0.29), (0.16, 0.50), (0.34, 0.71)], bracket, w)
    stroke([(0.66, 0.29), (0.84, 0.50), (0.66, 0.71)], bracket, w)
    stroke([(0.40, 0.52), (0.485, 0.62), (0.61, 0.39)], "#3FD8A0", w * 1.2)
    return img


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    big = build(1024)
    big.resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, "ecl.png"))
    base = big.resize((256, 256), Image.LANCZOS)
    base.save(os.path.join(OUT, "ecl.ico"), format="ICO",
              sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)])
    print("Icon saved in", OUT)