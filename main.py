#!/usr/bin/env python3
"""news-image-20261118-world: one TV live-news broadcast frame that sums
up the world news of Wednesday 18 November 2026 in a single image.

Pure Python 3.13 standard library only. No randomness, no time, no
network, no external images or fonts -- every run produces the exact
same PNG bytes.

Layout (1024x1024, live TV news studio):
  masthead "THE WORLD" + red LIVE bug + date line
  red BREAKING NEWS band
  hero panel: Trump meets Quad allies in Manila
  2x2 grid: Korea missile, Canada-China trade, UK sanctions, Akvan storm
  lower-third ticker strip with the day's keywords
"""

import os
import struct
import zlib

W = 1024
H = 1024


# ---- palette -----------------------------------------------------------
BG = (11, 27, 51)
BG2 = (15, 36, 66)
PANEL = (19, 45, 80)
HERO = (22, 54, 96)
EDGE = (56, 102, 156)
RED = (212, 38, 34)
RED_DARK = (158, 24, 22)
GOLD = (233, 179, 44)
WHITE = (255, 255, 255)
LIGHT = (216, 226, 240)
GREY = (160, 174, 194)
DOT = (32, 62, 102)
SKY1 = (7, 17, 34)
SKY2 = (10, 24, 46)
WIN = (233, 179, 44)
WIN2 = (120, 170, 220)


# ---- 5x7 bitmap font ---------------------------------------------------
# Each glyph: 7 rows of 5 pixels, '#' = on, '.' = off. Uppercase only.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", "..#..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#..##"),
    "|": ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def wrap_text(s, max_width, scale):
    char_w = 6 * scale
    max_chars = max(1, max_width // char_w)
    lines = []
    for raw in s.split("\n"):
        words = raw.split(" ")
        cur = ""
        for w in words:
            trial = (cur + " " + w).strip()
            if len(trial) <= max_chars:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    return lines


# ---- canvas ------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = c[0]
                self.buf[i + 1] = c[1]
                self.buf[i + 2] = c[2]

    def hline(self, x0, x1, y, c):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.px(x, y, c)

    def disc(self, cx, cy, r, c):
        for y in range(cy - r, cy + r + 1):
            dx = int((max(0, r * r - (y - cy) ** 2)) ** 0.5)
            self.hline(cx - dx, cx + dx, y, c)

    def rounded_rect(self, x, y, w, h, r, c):
        self.fill_rect(x + r, y, w - 2 * r, h, c)
        self.fill_rect(x, y + r, w, h - 2 * r, c)
        for cx, cy in ((x + r, y + r), (x + w - r - 1, y + r),
                       (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)):
            self.disc(cx, cy, r, c)

    def rect_outline(self, x, y, w, h, c, t=1):
        for k in range(t):
            self.hline(x + k, x + w - 1 - k, y + k, c)
            self.hline(x + k, x + w - 1 - k, y + h - 1 - k, c)
            for yy in range(y + k, y + h - k):
                self.px(x + k, yy, c)
                self.px(x + w - 1 - k, yy, c)

    def text(self, x, y, s, c, scale=2):
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT["?"])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, c)
            cx += 6 * scale
        return cx

    def text_center(self, cx, y, s, c, scale=2):
        self.text(cx - text_width(s, scale) // 2, y, s, c, scale)

    def text_block(self, x, y, s, c, scale, max_width, leading=None):
        lines = wrap_text(s, max_width, scale)
        lh = leading if leading is not None else 9 * scale
        for i, ln in enumerate(lines):
            self.text(x, y + i * lh, ln, c, scale)
        return len(lines)


# ---- backdrop ----------------------------------------------------------
def draw_map_dots(cv):
    # Coarse continent dot mask: (cx, cy, rx, ry) ellipses on a grid.
    continents = [
        (170, 210, 115, 55),   # north america
        (300, 430, 55, 85),    # south america
        (520, 185, 55, 38),    # europe
        (545, 335, 72, 88),    # africa
        (730, 205, 135, 72),   # asia
        (825, 480, 55, 30),    # australia
    ]
    step = 16
    for y in range(8, H, step):
        for x in range(8, W, step):
            for (cx, cy, rx, ry) in continents:
                dx = (x - cx) / rx
                dy = (y - cy) / ry
                if dx * dx + dy * dy <= 1.0:
                    cv.disc(x, y, 2, DOT)
                    break


def draw_skyline(cv, y_base, heights, x0=0, x1=W):
    # Deterministic skyline: heights list cycles across the width.
    x = x0
    i = 0
    while x < x1:
        bw = 34 + (heights[i % len(heights)] % 30)
        bh = heights[i % len(heights)]
        col = SKY1 if i % 2 == 0 else SKY2
        cv.fill_rect(x, y_base - bh, bw, bh, col)
        # lit windows, deterministic pattern
        for wy in range(y_base - bh + 10, y_base - 8, 18):
            for wx in range(x + 6, x + bw - 6, 12):
                if (wx * 7 + wy * 13) % 5 == 0:
                    cv.fill_rect(wx, wy, 4, 6, WIN if (wx + wy) % 3 else WIN2)
        x += bw + 6
        i += 1


# ---- page --------------------------------------------------------------
STORIES = [
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
    cv = Canvas(W, H, BG)
    # subtle vertical shading on the studio backdrop
    for i in range(8):
        cv.fill_rect(0, i * 128, W, 128, BG if i % 2 == 0 else BG2)
    draw_map_dots(cv)

    # skyline silhouette along the bottom third, behind the panels
    draw_skyline(cv, 928, [90, 150, 110, 190, 130, 220, 100, 170, 140,
                            200, 120, 160, 95, 185, 135, 210, 105, 175])

    # ---- masthead ------------------------------------------------------
    cv.text_center(470, 28, "THE WORLD", WHITE, 7)
    # red LIVE bug, top right
    cv.rounded_rect(868, 30, 132, 40, 8, RED)
    cv.disc(892, 50, 7, WHITE)
    cv.text(908, 36, "LIVE", WHITE, 3)
    # date line
    cv.fill_rect(212, 96, 600, 3, GOLD)
    cv.text_center(512, 108, "WEDNESDAY, 18 NOVEMBER 2026", GOLD, 2)

    # ---- breaking band -------------------------------------------------
    cv.fill_rect(24, 140, 976, 40, RED)
    cv.fill_rect(24, 140, 976, 3, RED_DARK)
    cv.text_center(512, 150, "BREAKING NEWS", WHITE, 3)

    # ---- hero panel: story 1 ------------------------------------------
    hx, hy, hw, hh = 24, 192, 976, 236
    cv.fill_rect(hx, hy, hw, hh, HERO)
    cv.rect_outline(hx, hy, hw, hh, EDGE, 2)
    cv.fill_rect(hx, hy, hw, 8, RED)
    # skyline strip inside the hero, bottom edge
    draw_skyline(cv, hy + hh - 2, [40, 62, 48, 74, 54, 68, 44, 58],
                 x0=hx + 8, x1=hx + hw - 8)
    tag, head, sub = STORIES[0]
    cv.text(hx + 28, hy + 24, tag, GOLD, 2)
    cv.fill_rect(hx + 28, hy + 46, 64, 3, GOLD)
    cv.text(hx + 28, hy + 62, head, WHITE, 4)
    cv.text(hx + 28, hy + 112, sub, LIGHT, 2)

    # ---- 2x2 grid: stories 2-5 ----------------------------------------
    gx, gy = 24, 440
    cw, ch = 482, 232
    gap = 12
    for idx, (tag, head, sub) in enumerate(STORIES[1:]):
        col = idx % 2
        row = idx // 2
        x = gx + col * (cw + gap)
        y = gy + row * (ch + gap)
        cv.fill_rect(x, y, cw, ch, PANEL)
        cv.rect_outline(x, y, cw, ch, EDGE, 2)
        cv.fill_rect(x, y, cw, 6, RED if idx % 2 == 0 else GOLD)
        cv.text(x + 20, y + 20, tag, GOLD if idx % 2 else RED, 2)
        cv.text_block(x + 20, y + 56, head, WHITE, 3, cw - 40, leading=27)
        cv.fill_rect(x + 20, y + 132, cw - 40, 2, EDGE)
        cv.text_block(x + 20, y + 148, sub, GREY, 2, cw - 40, leading=19)

    # ---- lower-third ticker --------------------------------------------
    ty = 928
    cv.fill_rect(0, ty, W, H - ty, SKY1)
    cv.fill_rect(0, ty, W, 3, GOLD)
    cv.rounded_rect(24, ty + 18, 116, 48, 8, RED)
    cv.disc(48, ty + 42, 7, WHITE)
    cv.text(64, ty + 30, "LIVE", WHITE, 3)
    ticker = "MANILA | KOREA MISSILE | CANADA-CHINA | UK SANCTIONS | AKVAN"
    tw = text_width(ticker, 2)
    cv.text(160 + (840 - tw) // 2, ty + 36, ticker, WHITE, 2)
    return cv.buf


def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(rgb_bytes, w, h):
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)  # filter: none
        raw += rgb_bytes[y * stride:(y + 1) * stride]
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
