#!/usr/bin/env python3
"""A newspaper front page summing up Wednesday 18 November 2026.

Pure Python 3.13 standard library. No network, no randomness, no
clock: the same input always renders the same PNG bytes.

Design: a classic broadsheet front page, not a TV broadcast. Big
centred nameplate, the full date (day, month, year) large directly
under it so the news is unmistakably today's, then one unmistakable
lead story with a real photo, and four more stories in a two-column
grid. New York Times style hierarchy: rank by type size, thin rules
instead of boxes, generous whitespace. Headlines use strong verbs
and numbers, factual only, no clickbait.

Photos (free licences only, decoded at runtime by a pure-stdlib PNG
decoder and blitted onto the canvas):
- Hero, Donald Trump at a podium: Gage Skidmore, CC BY-SA 2.0,
  https://commons.wikimedia.org/wiki/File:Donald_Trump_(55238711502).jpg
  (Phoenix rally, 17 April 2026; depicts the story's main figure,
  not the Manila summit itself).
- F-15E Strike Eagle over US Central Command: US Air Force photo by
  SrA Keegan Putman, public domain,
  https://commons.wikimedia.org/wiki/File:U_S_KC-135_refuels_Strike_Eagles_over_CENTCOM_(9007204).jpg
- Cyclone Akvan over the Bay of Bengal, 16 November 2026: NASA
  Worldview, NOAA-20 VIIRS true colour, public domain,
  fetched as tiles from NASA GIBS
  (https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/
  VIIRS_NOAA20_CorrectedReflectance_TrueColor).
"""

import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (250, 248, 242)
INK = (17, 17, 17)
GREYINK = (96, 94, 88)
HAIR = (168, 165, 155)
RED = (198, 32, 28)

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def read_png(path):
    """Decode a non-interlaced 8-bit PNG (grey, RGB, palette, RGBA).

    Pure stdlib: parses IHDR/PLTE/IDAT, inflates with zlib, undoes
    filters 0-4 (None, Sub, Up, Average, Paeth). Returns
    (width, height, bytearray of RGB triples, row-major).
    """
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos = 8
    width = height = bitdepth = ctype = interlace = None
    plte = None
    idat = bytearray()
    while pos < len(data):
        ln = int.from_bytes(data[pos:pos + 4], "big")
        kind = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        if kind == b"IHDR":
            width, height, bitdepth, ctype, _c, _f, interlace = \
                struct.unpack(">IIBBBBB", chunk)
        elif kind == b"PLTE":
            plte = chunk
        elif kind == b"IDAT":
            idat += chunk
        elif kind == b"IEND":
            break
        pos += 12 + ln
    assert interlace == 0, "interlaced PNG not supported"
    assert bitdepth == 8, "only 8-bit PNG supported"
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    stride = width * channels
    raw = zlib.decompress(bytes(idat))
    out = bytearray(width * height * 3)
    prev = bytearray(stride)
    p = 0
    for y in range(height):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if f == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                pa = abs(b - c)
                pb = abs(a - c)
                pc = abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        for x in range(width):
            if ctype == 0:
                g = line[x]
                r, g2, b = g, g, g
            elif ctype == 2:
                r, g2, b = line[3 * x:3 * x + 3]
            elif ctype == 3:
                idx = line[x]
                r, g2, b = plte[3 * idx:3 * idx + 3]
            elif ctype == 4:
                g = line[2 * x]
                r, g2, b = g, g, g
            else:
                r, g2, b = line[4 * x:4 * x + 3]
            o = (y * width + x) * 3
            out[o] = r
            out[o + 1] = g2
            out[o + 2] = b
        prev = line
    return width, height, out


# HEAD: bold condensed headline font, 6 wide x 10 tall, 2px stems.
# One row per string, '#' = ink, '.' = empty, left to right, top to bottom.
HEAD_GLYPHS = {
    "A": ["..##..", ".####.", "##..##", "##..##", "##..##",
          "######", "##..##", "##..##", "##..##", "##..##"],
    "B": ["#####.", "##..##", "##..##", "##..##", "#####.",
          "##..##", "##..##", "##..##", "##..##", "#####."],
    "C": [".####.", "##..##", "##....", "##....", "##....",
          "##....", "##....", "##....", "##..##", ".####."],
    "D": ["#####.", "##..##", "##..##", "##..##", "##..##",
          "##..##", "##..##", "##..##", "##..##", "#####."],
    "E": ["######", "##....", "##....", "##....", "#####.",
          "##....", "##....", "##....", "##....", "######"],
    "F": ["######", "##....", "##....", "##....", "#####.",
          "##....", "##....", "##....", "##....", "##...."],
    "G": [".####.", "##..##", "##....", "##....", "##.###",
          "##..##", "##..##", "##..##", "##..##", ".####."],
    "H": ["##..##", "##..##", "##..##", "##..##", "######",
          "##..##", "##..##", "##..##", "##..##", "##..##"],
    "I": ["######", "..##..", "..##..", "..##..", "..##..",
          "..##..", "..##..", "..##..", "..##..", "######"],
    "J": [".####.", "....##", "....##", "....##", "....##",
          "....##", "....##", "##..##", "##..##", ".####."],
    "K": ["##..##", "##.##.", "##.##.", "####..", "##.##.",
          "##.##.", "##..##", "##..##", "##..##", "##..##"],
    "L": ["##....", "##....", "##....", "##....", "##....",
          "##....", "##....", "##....", "##....", "######"],
    "M": ["##..##", "###.##", "###.##", "##.###", "##.###",
          "##.###", "##..##", "##..##", "##..##", "##..##"],
    "N": ["##..##", "###.##", "####.#", "##.###", "##.###",
          "##.###", "##.###", "##..##", "##..##", "##..##"],
    "O": [".####.", "##..##", "##..##", "##..##", "##..##",
          "##..##", "##..##", "##..##", "##..##", ".####."],
    "P": ["#####.", "##..##", "##..##", "##..##", "#####.",
          "##....", "##....", "##....", "##....", "##...."],
    "Q": [".####.", "##..##", "##..##", "##..##", "##..##",
          "##..##", "##..##", "##.###", "##..##", ".##.#."],
    "R": ["#####.", "##..##", "##..##", "##..##", "#####.",
          "##.##.", "##.##.", "##..##", "##..##", "##..##"],
    "S": [".####.", "##..##", "##....", "##....", ".####.",
          "....##", "....##", "##..##", "##..##", ".####."],
    "T": ["######", "..##..", "..##..", "..##..", "..##..",
          "..##..", "..##..", "..##..", "..##..", "..##.."],
    "U": ["##..##", "##..##", "##..##", "##..##", "##..##",
          "##..##", "##..##", "##..##", "##..##", ".####."],
    "V": ["##..##", "##..##", "##..##", "##..##", "##..##",
          "##..##", "##..##", ".####.", ".####.", "..##.."],
    "W": ["##..##", "##..##", "##..##", "##..##", "##..##",
          "##.###", "##.###", "###.##", "###.##", "##..##"],
    "X": ["##..##", "##..##", "##..##", ".####.", ".####.",
          ".####.", "##..##", "##..##", "##..##", "##..##"],
    "Y": ["##..##", "##..##", "##..##", "##..##", ".####.",
          "..##..", "..##..", "..##..", "..##..", "..##.."],
    "Z": ["######", "....##", "...##.", "...##.", "..##..",
          "..##..", ".##...", ".##...", "##....", "######"],
    "0": [".####.", "##..##", "##..##", "##.###", "##.###",
          "##.###", "##.###", "##.###", "##..##", ".####."],
    "1": ["..##..", ".###..", "..##..", "..##..", "..##..",
          "..##..", "..##..", "..##..", "..##..", ".####."],
    "2": [".####.", "##..##", "....##", "....##", "...##.",
          "..##..", ".##...", "##....", "##....", "######"],
    "3": [".####.", "....##", "....##", "....##", "..###.",
          "....##", "....##", "....##", "##..##", ".####."],
    "4": ["...##.", "..##..", "..###.", ".##.#.", "##..##",
          "##..##", "######", "....##", "....##", "....##"],
    "5": ["######", "##....", "##....", "#####.", "....##",
          "....##", "....##", "##..##", "##..##", ".####."],
    "6": [".####.", "##..##", "##....", "##....", "#####.",
          "##..##", "##..##", "##..##", "##..##", ".####."],
    "7": ["######", "....##", "....##", "...##.", "...##.",
          "..##..", "..##..", "..##..", "..##..", "..##.."],
    "8": [".####.", "##..##", "##..##", "##..##", ".####.",
          "##..##", "##..##", "##..##", "##..##", ".####."],
    "9": [".####.", "##..##", "##..##", "##..##", "##..##",
          ".#####", "....##", "....##", "##..##", ".####."],
    " ": ["......", "......", "......", "......", "......",
          "......", "......", "......", "......", "......"],
    ",": ["......", "......", "......", "......", "......",
          "......", "......", "..##..", ".##...", "##...."],
    ";": ["......", "......", "..##..", "..##..", "......",
          "......", "......", "..##..", ".##...", "##...."],
    ":": ["......", "......", "..##..", "..##..", "......",
          "......", "..##..", "..##..", "......", "......"],
    "-": ["......", "......", "......", "......", ".####.",
          ".####.", "......", "......", "......", "......"],
    "|": ["..##..", "..##..", "..##..", "..##..", "..##..",
          "..##..", "..##..", "..##..", "..##..", "..##.."],
    "/": ["....##", "....##", "...##.", "...##.", "..##..",
          "..##..", ".##...", ".##...", "##....", "##...."],
    ".": ["......", "......", "......", "......", "......",
          "......", "......", "......", "..##..", "..##.."],
    "?": [".####.", "##..##", "....##", "....##", "...##.",
          "..##..", "......", "..##..", "..##..", "......"],
}
HEAD = {"w": 6, "h": 10, "glyphs": HEAD_GLYPHS}


# BODY: clean readable text font, 6 wide x 8 tall, 1px stems, open
# counters, for sub-lines, kickers, dates and credits at small sizes.
BODY_GLYPHS = {
    "A": [".####.", "#...#.", "#...#.", "#####.", "#...#.",
          "#...#.", "#...#.", "#...#."],
    "B": ["####..", "#...#.", "#...#.", "####..", "#...#.",
          "#...#.", "#...#.", "####.."],
    "C": [".####.", "#....#", "#.....", "#.....", "#.....",
          "#.....", "#....#", ".####."],
    "D": ["####..", "#...#.", "#...#.", "#...#.", "#...#.",
          "#...#.", "#...#.", "####.."],
    "E": ["#####.", "#.....", "#.....", "####..", "#.....",
          "#.....", "#.....", "#####."],
    "F": ["#####.", "#.....", "#.....", "####..", "#.....",
          "#.....", "#.....", "#....."],
    "G": [".####.", "#....#", "#.....", "#.....", "#..###",
          "#....#", "#....#", ".####."],
    "H": ["#...#.", "#...#.", "#...#.", "#####.", "#...#.",
          "#...#.", "#...#.", "#...#."],
    "I": [".###..", "..#...", "..#...", "..#...", "..#...",
          "..#...", "..#...", ".###.."],
    "J": ["..###.", "....#.", "....#.", "....#.", "....#.",
          "....#.", "#...#.", ".###.."],
    "K": ["#...#.", "#..#..", "#..#..", "#.#...", "##....",
          "#.#...", "#..#..", "#...#."],
    "L": ["#.....", "#.....", "#.....", "#.....", "#.....",
          "#.....", "#.....", "#####."],
    "M": ["#...#.", "##.##.", "##.##.", "#.#.#.", "#.#.#.",
          "#...#.", "#...#.", "#...#."],
    "N": ["#...#.", "##..#.", "##..#.", "#.#.#.", "#.#.#.",
          "#..##.", "#..##.", "#...#."],
    "O": [".###..", "#...#.", "#...#.", "#...#.", "#...#.",
          "#...#.", "#...#.", ".###.."],
    "P": ["####..", "#...#.", "#...#.", "####..", "#.....",
          "#.....", "#.....", "#....."],
    "Q": [".###..", "#...#.", "#...#.", "#...#.", "#...#.",
          "#.#.#.", "#..#..", ".##.#."],
    "R": ["####..", "#...#.", "#...#.", "####..", "#.#...",
          "#..#..", "#..#..", "#...#."],
    "S": [".####.", "#....#", "#.....", ".###..", "....#.",
          "#....#", "#....#", ".####."],
    "T": ["#####.", "..#...", "..#...", "..#...", "..#...",
          "..#...", "..#...", "..#..."],
    "U": ["#...#.", "#...#.", "#...#.", "#...#.", "#...#.",
          "#...#.", "#...#.", ".###.."],
    "V": ["#...#.", "#...#.", "#...#.", "#...#.", "#...#.",
          "#...#.", ".###..", "..#..."],
    "W": ["#...#.", "#...#.", "#...#.", "#...#.", "#.#.#.",
          "#.#.#.", "##.##.", "#...#."],
    "X": ["#...#.", "#...#.", ".#.#..", "..#...", "..#...",
          ".#.#..", "#...#.", "#...#."],
    "Y": ["#...#.", "#...#.", "#...#.", ".#.#..", "..#...",
          "..#...", "..#...", "..#..."],
    "Z": ["#####.", "....#.", "...#..", "..#...", "..#...",
          ".#....", "#.....", "#####."],
    "0": [".###..", "#...#.", "#..##.", "#.#.#.", "##..#.",
          "#...#.", "#...#.", ".###.."],
    "1": ["..#...", ".##...", "..#...", "..#...", "..#...",
          "..#...", "..#...", ".###.."],
    "2": [".###..", "#...#.", "....#.", "...#..", "..#...",
          ".#....", "#.....", "#####."],
    "3": ["####..", "....#.", "....#.", ".###..", "....#.",
          "....#.", "#...#.", ".###.."],
    "4": ["...#..", "..##..", ".#.#..", "#..#..", "#..#..",
          "#####.", "...#..", "...#.."],
    "5": ["#####.", "#.....", "#.....", "####..", "....#.",
          "....#.", "#...#.", ".###.."],
    "6": [".###..", "#.....", "#.....", "####..", "#...#.",
          "#...#.", "#...#.", ".###.."],
    "7": ["#####.", "....#.", "...#..", "...#..", "..#...",
          "..#...", "..#...", "..#..."],
    "8": [".###..", "#...#.", "#...#.", ".###..", "#...#.",
          "#...#.", "#...#.", ".###.."],
    "9": [".###..", "#...#.", "#...#.", "#...#.", ".####.",
          "....#.", "....#.", ".###.."],
    " ": ["......", "......", "......", "......", "......",
          "......", "......", "......"],
    ",": ["......", "......", "......", "......", "......",
          "......", "..#...", ".#...."],
    ";": ["......", "..#...", "..#...", "......", "......",
          "......", "..#...", ".#...."],
    ":": ["......", "..#...", "..#...", "......", "......",
          "..#...", "..#...", "......"],
    "-": ["......", "......", "......", ".####.", ".####.",
          "......", "......", "......"],
    "|": ["..#...", "..#...", "..#...", "..#...", "..#...",
          "..#...", "..#...", "..#..."],
    "/": ["....#.", "....#.", "...#..", "...#..", "..#...",
          "..#...", ".#....", ".#...."],
    ".": ["......", "......", "......", "......", "......",
          "......", "..#...", "..#..."],
    "?": [".###..", "#...#.", "....#.", "...#..", "..#...",
          "......", "..#...", "..#..."],
}
BODY = {"w": 6, "h": 8, "glyphs": BODY_GLYPHS}


def glyph_rows(font, ch):
    return font["glyphs"].get(ch, font["glyphs"]["?"])


def measure(text, font, scale):
    return len(text) * (font["w"] + 1) * scale - scale


def split_lines(text, width, font, scale):
    per_line = max(1, width // ((font["w"] + 1) * scale))
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
                       (x + r, y + h - r - 1),
                       (x + w - r - 1, y + h - r - 1)):
            self.disc(cx, cy, r, c)

    def frame(self, x, y, w, h, c, t=1):
        for k in range(t):
            self.row(x + k, x + w - 1 - k, y + k, c)
            self.row(x + k, x + w - 1 - k, y + h - 1 - k, c)
            for yy in range(y + k, y + h - k):
                self.set(x + k, yy, c)
                self.set(x + w - 1 - k, yy, c)

    def draw_text(self, x, y, s, c, font, scale=2):
        cx = x
        for ch in s.upper():
            rows = glyph_rows(font, ch)
            for r in range(font["h"]):
                row = rows[r]
                for col in range(font["w"]):
                    if row[col] == "#":
                        self.fill(cx + col * scale, y + r * scale,
                                  scale, scale, c)
            cx += (font["w"] + 1) * scale
        return cx

    def center_text(self, cx, y, s, c, font, scale=2):
        self.draw_text(cx - measure(s, font, scale) // 2, y, s, c,
                       font, scale)

    def para(self, x, y, s, c, font, scale, width, leading=None):
        lines = split_lines(s, width, font, scale)
        step = leading if leading is not None else (font["h"] + 1) * scale
        for i, ln in enumerate(lines):
            self.draw_text(x, y + i * step, ln, c, font, scale)
        return len(lines)

    def draw_image(self, x, y, w, h, img, src=None):
        """Blit a decoded PNG (iw, ih, rgb bytearray) scaled to (w, h).

        With src=(sx, sy, sw, sh), blit only that source rectangle,
        scaled to (w, h): a crop, never a squash.
        """
        iw, ih, data = img
        if src is None:
            sx0, sy0, sw, sh = 0, 0, iw, ih
        else:
            sx0, sy0, sw, sh = src
        for dy in range(h):
            yy = y + dy
            if yy < 0 or yy >= self.h:
                continue
            sy = sy0 + dy * sh // h
            base = (yy * self.w + x) * 3
            for dx in range(w):
                xx = x + dx
                if xx < 0 or xx >= self.w:
                    continue
                sx = sx0 + dx * sw // w
                o = (sy * iw + sx) * 3
                j = base + dx * 3
                self.pxbuf[j] = data[o]
                self.pxbuf[j + 1] = data[o + 1]
                self.pxbuf[j + 2] = data[o + 2]

    def photo(self, x, y, w, h, img, credit, src=None):
        """Blit a photo, credit line in small grey type just below it."""
        self.draw_image(x, y, w, h, img, src)
        self.draw_text(x, y + h + 4, credit, GREYINK, BODY, 1)


HERO = {
    "tag": "DIPLOMACY",
    "head": "TRUMP MEETS QUAD ALLIES IN MANILA",
    "sub": "FIRST QUAD SUMMIT IN 2 YEARS; "
           "XI-PUTIN TALKS NEXT IN SHENZHEN",
    "agenda": "AGENDA: MINERALS, MARITIME SECURITY, AI",
    "photo": "hero.png",
    "credit": "PHOTO: GAGE SKIDMORE / CC BY-SA 2.0",
}

# Row 1: photo cards. Row 2: text-only cards. One-line subs, so each
# card fits its row; wording trimmed, facts unchanged.
CARDS = [
    {"tag": "MIDDLE EAST",
     "head": "US JETS STRIKE IRAN AFTER DRONE ATTACK",
     "sub": "3RD ATTACK ON BAHRAIN IN 5 DAYS",
     "photo": "jet.png",
     "credit": "PHOTO: US AIR FORCE / PUBLIC DOMAIN"},
    {"tag": "WEATHER",
     "head": "AKVAN STORM STRENGTHENS OFF INDIA",
     "sub": "LANDFALL FRIDAY; WINDS 145 KM/H",
     "photo": "akvan.png",
     "credit": "IMAGE: NASA WORLDVIEW / PUBLIC DOMAIN"},
    {"tag": "ASIA",
     "head": "NORTH KOREA FIRES MISSILE INTO SEA",
     "sub": "SEOUL: MISSILE FIRED FROM WONSAN"},
    {"tag": "MIDDLE EAST",
     "head": "UK SANCTIONS ISRAELI SETTLEMENT FIRMS",
     "sub": "LONDON ACTS FOR TWO-STATE SOLUTION"},
]


def render():
    p = Paint(W, H, PAPER)

    # Nameplate: double rule, big centred masthead, thick-thin rule.
    p.fill(24, 12, 976, 3, INK)
    p.fill(24, 18, 976, 1, INK)
    p.center_text(512, 28, "THE WORLD", INK, HEAD, 10)
    p.fill(24, 136, 976, 3, INK)
    p.fill(24, 142, 976, 1, INK)

    # Dateline, large and impossible to miss: full day, month, year.
    p.center_text(512, 152, "WEDNESDAY, 18 NOVEMBER 2026", INK, HEAD, 4)
    p.fill(24, 200, 976, 1, HAIR)
    p.draw_text(24, 208, "WORLD NEWS", INK, BODY, 2)
    right = measure("LATE EDITION", BODY, 2)
    p.draw_text(1000 - right, 208, "LATE EDITION", INK, BODY, 2)
    p.fill(24, 232, 976, 3, INK)

    # Lead story: kicker, one-line headline, photo left, deck right.
    p.draw_text(24, 248, HERO["tag"], RED, BODY, 2)
    p.draw_text(24, 274, HERO["head"], INK, HEAD, 4)
    hero_img = read_png(os.path.join(ASSETS, HERO["photo"]))
    p.photo(24, 328, 440, 248, hero_img, HERO["credit"])
    tx = 488
    p.para(tx, 328, HERO["sub"], INK, BODY, 2, 512, leading=20)
    p.para(tx, 388, HERO["agenda"], GREYINK, BODY, 2, 512, leading=20)
    p.fill(24, 600, 976, 1, HAIR)

    # Grid hairlines.
    p.fill(511, 612, 1, 350, HAIR)
    p.fill(24, 838, 976, 1, HAIR)

    # Row 1: photo cards (centre-cropped strips, never squashed).
    for i, card in enumerate(CARDS[:2]):
        x = 24 + i * 494
        img = read_png(os.path.join(ASSETS, card["photo"]))
        src = (0, (img[1] - 84) // 2, 482, 84)
        p.photo(x, 612, 482, 84, img, card["credit"], src)
        p.draw_text(x, 714, card["tag"], RED, BODY, 2)
        n = p.para(x, 736, card["head"], INK, HEAD, 3, 482, leading=34)
        p.para(x, 736 + n * 34 + 6, card["sub"], GREYINK, BODY, 2, 482,
               leading=20)

    # Row 2: text-only cards.
    for i, card in enumerate(CARDS[2:]):
        x = 24 + i * 494
        p.draw_text(x, 850, card["tag"], RED, BODY, 2)
        n = p.para(x, 872, card["head"], INK, HEAD, 3, 482, leading=34)
        p.para(x, 872 + n * 34 + 6, card["sub"], GREYINK, BODY, 2, 482,
               leading=20)

    # Footer: the date again, under a rule.
    p.fill(24, 974, 976, 2, INK)
    p.center_text(512, 984, "THE WORLD | WEDNESDAY, 18 NOVEMBER 2026",
                  INK, BODY, 2)
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
