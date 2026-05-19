"""Genera los iconos PWA on-brand de Racing Cars (fintech-dark + acento racing).

Uso: py -3 tools/make_icons.py
Salida: static/icon-512.png, static/icon-192.png, static/apple-touch-icon.png
Regenerar solo si cambia la identidad visual.
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

BG = (10, 10, 10)          # #0a0a0a
ACCENT = (0, 255, 136)     # #00ff88
LIGHT = (224, 224, 224)    # #e0e0e0
S = 512                    # se genera a 512 y se reescala

OUT = os.path.join(os.path.dirname(__file__), "..", "static")

_FONTS = [
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\Arial Bold.ttf",
]


def _font(size: int) -> ImageFont.FreeTypeFont:
    for p in _FONTS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def build() -> Image.Image:
    img = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(img)

    # "RC" centrado, verde acento, ligeramente arriba del centro
    fnt = _font(260)
    txt = "RC"
    bb = d.textbbox((0, 0), txt, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx = (S - tw) / 2 - bb[0]
    ty = (S - th) / 2 - bb[1] - 28
    d.text((tx, ty), txt, font=fnt, fill=ACCENT)

    # Banda de bandera a cuadros (acento racing) debajo del texto
    cell = 26
    cols = 8
    band_w = cell * cols
    x0 = (S - band_w) // 2
    y0 = 360
    for row in range(2):
        for col in range(cols):
            on = (row + col) % 2 == 0
            c = LIGHT if on else (40, 40, 40)
            xa = x0 + col * cell
            ya = y0 + row * cell
            d.rectangle([xa, ya, xa + cell - 1, ya + cell - 1], fill=c)

    return img


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    base = build()
    targets = {
        "icon-512.png": 512,
        "icon-192.png": 192,
        "apple-touch-icon.png": 180,
    }
    for name, size in targets.items():
        im = base.resize((size, size), Image.LANCZOS)
        path = os.path.join(OUT, name)
        im.save(path, "PNG")
        print("escrito", os.path.normpath(path))


if __name__ == "__main__":
    main()
