#!/usr/bin/env python3
"""One TV live-news frame summing up Wednesday 18 November 2026.

Pure Python 3.13 standard library. No network, no randomness, no
clock, no outside images or fonts: the same input always renders the
same PNG bytes.

The frame is a dark-blue news studio: a dotted world map and a lit
skyline behind the panels, masthead THE WORLD with a red LIVE bug,
the date, a red BREAKING NEWS band, one hero story, four more in a
grid, and a lower-third ticker.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

NAVY = (11, 27, 51)
NAVY2 = (15, 36, 66)
CARD = (19, 45, 80)
HEROBG = (22, 54, 96)
LINE = (56, 102, 156)
RED = (212, 38, 34)
DARKRED = (158, 24, 22)
GOLD = (233, 179, 44)
WHITE = (255, 255, 255)
MIST = (216, 226, 240)
GREY = (160, 174, 194)
DOTC = (32, 62, 102)
NIGHT = (7, 17, 34)
NIGHT2 = (10, 24, 46)
LAMP = (233, 179, 44)
LAMP2 = (120, 170, 220)


# 5x7 glyphs, one row per integer, bit 4 = leftmost pixel.
GLYPHS = {
    "A": [14, 17, 17, 31, 17, 17, 17],
    "B": [30, 17, 17, 30, 17, 17, 30],
    "C": [15, 16, 16, 16, 16, 16, 15],
    "D": [30, 17, 17, 17, 17, 17, 30],
    "E": [31, 16, 16, 30, 16, 16, 31],
    "F": [31, 16, 16, 30, 16, 16, 16],
    "G": [15, 16, 16, 23, 17, 17, 14],
    "H": [17, 17, 17, 31, 17, 17, 17],
    "I": [14, 4, 4, 4, 4, 4, 14],
    "J": [7, 2, 2, 2, 2, 18, 6],
    "K": [17, 18, 20, 24, 20, 18, 17],
    "L": [16, 16, 16, 16, 16, 16, 31],
    "M": [17, 27, 21, 21, 17, 17, 17],
    "N": [17, 25, 21, 19, 17, 17, 17],
    "O": [14, 17, 17, 17, 17, 17, 14],
    "P": [30, 17, 17, 30, 16, 16, 16],
    "Q": [14, 17, 17, 17, 21, 18, 13],
    "R": [30, 17, 17, 30, 20, 18, 17],
    "S": [15, 16, 16, 14, 1, 1, 30],
    "T": [31, 4, 4, 4, 4, 4, 4],
    "U": [17, 17, 17, 17, 17, 17, 14],
    "V": [17, 17, 17, 17, 17, 10, 4],
    "W": [17, 17, 17, 21, 21, 27, 17],
    "X": [17, 17, 10, 4, 10, 17, 17],
    "Y": [17, 17, 10, 4, 4, 4, 4],
    "Z": [31, 1, 2, 4, 8, 16, 31],
    "0": [14, 17, 19, 21, 25, 17, 14],
    "1": [4, 6, 4, 4, 4, 4, 14],
    "2": [14, 17, 1, 2, 4, 8, 31],
    "3": [30, 1, 1, 14, 1, 1, 30],
    "4": [2, 6, 10, 18, 31, 2, 2],
    "5": [31, 16, 30, 1, 1, 17, 14],
    "6": [14, 16, 16, 30, 17, 17, 14],
    "7": [31, 1, 2, 2, 4, 4, 4],
    "8": [14, 17, 17, 14, 17, 17, 14],
    "9": [14, 17, 17, 15, 1, 2, 6],
    " ": [0, 0, 0, 0, 0, 0, 0],
    ".": [0, 0, 0, 0, 0, 6, 6],
    ",": [0, 0, 0, 0, 6, 2, 4],
    ";": [0, 6, 6, 0, 6, 2, 4],
    ":": [0, 6, 6, 0, 6, 6, 0],
    "!": [4, 4, 4, 4, 4, 0, 4],
    "?": [14, 17, 1, 2, 4, 0, 4],
    "'": [4, 4, 4, 0, 0, 0, 0],
    "-": [0, 0, 0, 14, 0, 0, 0],
    "/": [1, 2, 2, 4, 8, 8, 16],
    "(": [2, 4, 8, 8, 8, 4, 2],
    ")": [8, 4, 2, 2, 2, 4, 8],
    "&": [6, 18, 20, 8, 21, 18, 13],
    "%": [25, 26, 1, 2, 4, 8, 19],
    "|": [4, 4, 4, 4, 4, 4, 4],
}


def glyph_rows(ch):
    return GLYPHS.get(ch, GLYPHS["?"])


def measure(text, scale):
    return len(text) * 6 * scale - scale


def split_lines(text, width, scale):
    per_line = max(1, width // (6 * scale))
    out = []
    for chunk in text.split("\n"):
        words = chunk.split(" ")
        line = ""
        for word in words:
            trial = (line + " " + word).strip()
            if len(trial) <= per_line:
                line = trial
            else:
                if line:
                    out.append(line)
                line = word
        if line:
            out.append(line)
    return out


class Paint:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.pxbuf = bytearray(w * h * 3)
        self.fill(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.pxbuf[i] = c[0]
            self.pxbuf[i + 1] = c[1]
            self.pxbuf[i + 2] = c[2]

    def fill(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                j = base + (xx - x0) * 3
                self.pxbuf[j] = c[0]
                self.pxbuf[j + 1] = c[1]
                self.pxbuf[j + 2] = c[2]

    def row(self, x0, x1, y, c):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.set(x, y, c)

    def disc(self, cx, cy, r, c):
        for y in range(cy - r, cy + r + 1):
            dx = int((max(0, r * r - (y - cy) ** 2)) ** 0.5)
            self.row(cx - dx, cx + dx, y, c)

    def rrect(self, x, y, w, h, r, c):
        self.fill(x + r, y, w - 2 * r, h, c)
        self.fill(x, y + r, w, h - 2 * r, c)
        for cx, cy in ((x + r, y + r), (x + w - r - 1, y + r),
                       (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)):
            self.disc(cx, cy, r, c)

    def frame(self, x, y, w, h, c, t=1):
        for k in range(t):
            self.row(x + k, x + w - 1 - k, y + k, c)
            self.row(x + k, x + w - 1 - k, y + h - 1 - k, c)
            for yy in range(y + k, y + h - k):
                self.set(x + k, yy, c)
                self.set(x + w - 1 - k, yy, c)

    def draw_text(self, x, y, s, c, scale=2):
        cx = x
        for ch in s.upper():
            rows = glyph_rows(ch)
            for r in range(7):
                bits = rows[r]
                for col in range(5):
                    if (bits >> (4 - col)) & 1:
                        self.fill(cx + col * scale, y + r * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx

    def center_text(self, cx, y, s, c, scale=2):
        self.draw_text(cx - measure(s, scale) // 2, y, s, c, scale)

    def para(self, x, y, s, c, scale, width, leading=None):
        lines = split_lines(s, width, scale)
        step = leading if leading is not None else 9 * scale
        for i, ln in enumerate(lines):
            self.draw_text(x, y + i * step, ln, c, scale)
        return len(lines)


def world_dots(p):
    blobs = [
        (170, 210, 115, 55),
        (300, 430, 55, 85),
        (520, 185, 55, 38),
        (545, 335, 72, 88),
        (730, 205, 135, 72),
        (825, 480, 55, 30),
    ]
    step = 16
    for y in range(8, H, step):
        for x in range(8, W, step):
            for (cx, cy, rx, ry) in blobs:
                dx = (x - cx) / rx
                dy = (y - cy) / ry
                if dx * dx + dy * dy <= 1.0:
                    p.disc(x, y, 2, DOTC)
                    break


def city(p, base, heights, x0=0, x1=W):
    x = x0
    i = 0
    while x < x1:
        bw = 34 + (heights[i % len(heights)] % 30)
        bh = heights[i % len(heights)]
        col = NIGHT if i % 2 == 0 else NIGHT2
        p.fill(x, base - bh, bw, bh, col)
        for wy in range(base - bh + 10, base - 8, 18):
            for wx in range(x + 6, x + bw - 6, 12):
                if (wx * 7 + wy * 13) % 5 == 0:
                    p.fill(wx, wy, 4, 6, LAMP if (wx + wy) % 3 else LAMP2)
        x += bw + 6
        i += 1


def slant(p, x0, y0, x1, y1, c, t=2):
    dx = x1 - x0
    dy = y1 - y0
    steps = max(abs(dx), abs(dy), 1)
    for i in range(steps + 1):
        p.disc(x0 + dx * i // steps, y0 + dy * i // steps, t, c)


def icon_missile(p, x, y, s, c):
    cx = x + s // 2
    p.fill(cx - 3, y + 10, 6, s - 22, c)
    p.fill(cx - 2, y + 6, 4, 4, c)
    p.fill(cx - 1, y + 3, 2, 3, c)
    p.fill(cx - 8, y + s - 16, 4, 8, c)
    p.fill(cx + 4, y + s - 16, 4, 8, c)
    p.disc(cx, y + s - 5, 3, GOLD)


def icon_trade(p, x, y, s, c):
    r = s // 4
    p.disc(x + s // 2 - r // 2, y + s // 2, r, c)
    p.disc(x + s // 2 - r // 2, y + s // 2, r - 3, CARD)
    p.disc(x + s // 2 + r // 2, y + s // 2, r, c)
    p.disc(x + s // 2 + r // 2, y + s // 2, r - 3, CARD)


def icon_ban(p, x, y, s, c):
    r = s // 2 - 2
    cx, cy = x + s // 2, y + s // 2
    p.disc(cx, cy, r, c)
    p.disc(cx, cy, r - 3, CARD)
    slant(p, cx - r + 3, cy + r - 3, cx + r - 3, cy - r + 3, c)


def icon_storm(p, x, y, s, c):
    cx, cy = x + s // 2, y + s // 2
    for i in range(26):
        a = i * 0.6
        r = 2 + i * 0.6
        p.disc(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), 2, c)


ITEMS = [
    ("DIPLOMACY", "TRUMP MEETS QUAD ALLIES IN MANILA",
     "FIRST QUAD SUMMIT OF SECOND TERM; MARCOS NEXT"),
    ("ASIA", "NORTH KOREA FIRES MISSILE INTO SEA",
     "SEOUL: BALLISTIC MISSILE LAUNCHED FROM WONSAN"),
    ("TRADE", "CANADA AND CHINA EXTEND TRADE DEALS",
     "XI MEETS CARNEY AHEAD OF APEC SUMMIT"),
    ("MIDDLE EAST", "BRITAIN SANCTIONS ISRAELI SETTLEMENT FIRMS",
     "LONDON ACTS TO PROTECT TWO-STATE SOLUTION"),
    ("WEATHER", "AKVAN STORM STRENGTHENS OFF INDIA",
     "IMD WARNS ANDHRA PRADESH AND ODISHA ON ALERT"),
]


def render():
    p = Paint(W, H, NAVY)
    for i in range(8):
        p.fill(0, i * 128, W, 128, NAVY if i % 2 == 0 else NAVY2)
    world_dots(p)
    city(p, 928, [90, 150, 110, 190, 130, 220, 100, 170, 140,
                  200, 120, 160, 95, 185, 135, 210, 105, 175])

    p.center_text(470, 28, "THE WORLD", WHITE, 7)
    p.rrect(868, 30, 132, 40, 8, RED)
    p.disc(892, 50, 7, WHITE)
    p.draw_text(908, 36, "LIVE", WHITE, 3)
    p.fill(212, 96, 600, 3, GOLD)
    p.center_text(512, 108, "WEDNESDAY, 18 NOVEMBER 2026", GOLD, 2)

    p.fill(24, 140, 976, 40, RED)
    p.fill(24, 140, 976, 3, DARKRED)
    p.center_text(512, 150, "BREAKING NEWS", WHITE, 3)

    hx, hy, hw, hh = 24, 192, 976, 236
    p.fill(hx, hy, hw, hh, HEROBG)
    p.frame(hx, hy, hw, hh, LINE, 2)
    p.fill(hx, hy, hw, 8, RED)
    city(p, hy + hh - 2, [40, 62, 48, 74, 54, 68, 44, 58],
         x0=hx + 8, x1=hx + hw - 8)
    tag, head, sub = ITEMS[0]
    p.draw_text(hx + 28, hy + 24, tag, GOLD, 2)
    p.fill(hx + 28, hy + 46, 64, 3, GOLD)
    p.draw_text(hx + 28, hy + 62, head, WHITE, 4)
    p.draw_text(hx + 28, hy + 112, sub, MIST, 2)
    p.draw_text(hx + 28, hy + 148, "AGENDA: MINERALS, MARITIME SECURITY, AI",
                GOLD, 2)

    gx, gy = 24, 440
    cw, ch = 482, 232
    gap = 12
    for idx, (tag, head, sub) in enumerate(ITEMS[1:]):
        col = idx % 2
        row = idx // 2
        x = gx + col * (cw + gap)
        y = gy + row * (ch + gap)
        p.fill(x, y, cw, ch, CARD)
        p.frame(x, y, cw, ch, LINE, 2)
        p.fill(x, y, cw, 6, RED if idx % 2 == 0 else GOLD)
        p.draw_text(x + 20, y + 20, tag, GOLD if idx % 2 else RED, 2)
        icons = {"ASIA": icon_missile, "TRADE": icon_trade,
                 "MIDDLE EAST": icon_ban, "WEATHER": icon_storm}
        fn = icons.get(tag)
        if fn:
            fn(p, x + cw - 62, y + 12, 44, GOLD if idx % 2 else RED)
        p.para(x + 20, y + 56, head, WHITE, 3, cw - 40, leading=27)
        p.fill(x + 20, y + 132, cw - 40, 2, LINE)
        p.para(x + 20, y + 148, sub, GREY, 2, cw - 40, leading=19)

    ty = 928
    p.fill(0, ty, W, H - ty, NIGHT)
    p.fill(0, ty, W, 3, GOLD)
    p.rrect(24, ty + 18, 116, 48, 8, RED)
    p.disc(48, ty + 42, 7, WHITE)
    p.draw_text(64, ty + 30, "LIVE", WHITE, 3)
    ticker = "MANILA | KOREA MISSILE | CANADA-CHINA | UK SANCTIONS | AKVAN"
    tw = measure(ticker, 2)
    p.draw_text(160 + (840 - tw) // 2, ty + 36, ticker, WHITE, 2)
    return p.pxbuf


def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(rgb, w, h):
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(render(), W, H)
    path = os.path.join(out_dir, "entry.png")
    tmp_path = path + ".tmp"
    with open(tmp_path, "wb") as f:
        f.write(png)
    os.replace(tmp_path, path)
    print(f"wrote {path} ({len(png)} bytes)")


if __name__ == "__main__":
    main()
