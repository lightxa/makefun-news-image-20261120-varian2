#!/usr/bin/env python3
"""news-image-20261120 varian 2: world map of Friday 20 November 2026.

Draws the image procedurally with the Python standard library only
(zlib + struct for the PNG). No network, fully deterministic: the same
bytes come out of every run.

Design: a stylised world map with numbered pins on the places where the
day's stories happened, each pin explained in a legend below, under a
title band that names the date in full.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
NAVY = (13, 27, 46)        # page background
OCEAN = (22, 52, 84)       # sea on the map
LAND = (62, 124, 84)       # continents
LAND_EDGE = (126, 196, 152)
GRID = (38, 74, 110)       # faint graticule
GOLD = (212, 175, 55)
CREAM = (245, 240, 225)
DIM = (158, 176, 198)
RED = (214, 48, 49)
WHITE = (255, 255, 255)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is blank.
FONT = {
    "A": ("#...#", "#####", "#...#", "#...#", "#####", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
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
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.###", "#..##"),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
}

# Fix the A glyph: its top bar belongs on row 1, apex on row 0.
FONT["A"] = (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#")


def text_width(text, scale):
    return len(text) * 6 * scale - scale


class Canvas:
    """An RGB pixel buffer with tiny drawing primitives."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def line(self, x0, y0, x1, y1, color):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - 1) ** 2 <= d2 <= r * r:
                    self.set(xx, yy, color)

    def polygon(self, pts, color, edge=None):
        """Scanline fill of a simple polygon (list of (x, y))."""
        if not pts:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(int(xs[k]), int(xs[k + 1]) + 1):
                    self.set(x, y, color)
        if edge:
            n = len(pts)
            for i in range(n):
                self.line(pts[i][0], pts[i][1], pts[(i + 1) % n][0],
                          pts[(i + 1) % n][1], edge)

    def text(self, s, x, y, scale, color):
        """Draw uppercase text; unknown chars become spaces."""
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, color)
            cx += 6 * scale

    def text_centered(self, s, cx, y, scale, color):
        self.text(s, cx - text_width(s, scale) // 2, y, scale, color)


# ------------------------------------------------------------ PNG writer
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.px[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", canvas.w, canvas.h,
                                       8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------- world map data
# Simplified continent outlines as (lon, lat) pairs. Equirectangular:
# lon -180..180 -> x 24..1000, lat 80..-60 -> y 136..516.
MAP_X0, MAP_X1 = 24, 1000
MAP_Y0, MAP_Y1 = 136, 516
LAT_TOP, LAT_BOT = 80.0, -60.0


def project(lon, lat):
    x = MAP_X0 + (lon + 180.0) / 360.0 * (MAP_X1 - MAP_X0)
    y = MAP_Y0 + (LAT_TOP - lat) / (LAT_TOP - LAT_BOT) * (MAP_Y1 - MAP_Y0)
    return (int(round(x)), int(round(y)))


CONTINENTS = [
    # North America
    [(-168, 66), (-158, 58), (-140, 60), (-130, 54), (-125, 49), (-124, 42),
     (-120, 34), (-114, 29), (-110, 24), (-105, 20), (-97, 16), (-94, 17),
     (-90, 14), (-83, 9), (-79, 9), (-81, 13), (-84, 16), (-87, 21),
     (-90, 21), (-97, 26), (-93, 30), (-89, 30), (-84, 30), (-81, 26),
     (-80, 32), (-76, 35), (-74, 40), (-70, 42), (-65, 44), (-60, 47),
     (-65, 50), (-60, 52), (-55, 52), (-60, 55), (-65, 58), (-68, 58),
     (-72, 62), (-78, 62), (-85, 66), (-92, 66), (-95, 69), (-110, 68),
     (-125, 70), (-140, 70), (-155, 71), (-165, 68)],
    # Greenland
    [(-58, 64), (-52, 60), (-43, 60), (-40, 64), (-32, 68), (-25, 70),
     (-20, 74), (-25, 76), (-35, 76), (-50, 74), (-58, 70)],
    # South America
    [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18),
     (-70, -23), (-70, -30), (-73, -37), (-73, -44), (-74, -50), (-70, -54),
     (-66, -55), (-68, -50), (-65, -45), (-62, -41), (-58, -35), (-52, -32),
     (-48, -28), (-41, -23), (-35, -9), (-35, -6), (-40, -3), (-44, -2),
     (-50, 0), (-53, 4), (-58, 6), (-62, 9), (-68, 11), (-72, 12),
     (-76, 10)],
    # Africa
    [(-17, 15), (-17, 21), (-15, 27), (-10, 31), (-6, 35), (0, 36),
     (10, 37), (11, 34), (20, 32), (30, 31), (32, 31), (35, 28), (37, 22),
     (39, 18), (43, 12), (48, 11), (51, 10), (46, 5), (41, 0), (40, -5),
     (40, -10), (38, -15), (35, -20), (32, -26), (28, -33), (20, -35),
     (17, -32), (14, -22), (12, -15), (13, -10), (12, -5), (9, 0), (9, 4),
     (-8, 4), (-13, 8), (-17, 12)],
    # Asia: one clean loop, south coast east, Arctic coast west, Urals
    # south to close. (The earlier version folded back through the
    # interior and left a gap across central Asia.)
    [(28, 36), (32, 36), (36, 36), (39, 31), (43, 28), (48, 29), (51, 27),
     (55, 26), (58, 25), (61, 24), (65, 25), (68, 23), (71, 21), (74, 17),
     (76, 11), (78, 8), (80, 10), (83, 17), (87, 21), (90, 22), (93, 18),
     (96, 15), (98, 10), (101, 5), (103, 2), (104, 7), (106, 10), (108, 12),
     (109, 15), (107, 19), (109, 21), (112, 21), (115, 22), (118, 25),
     (120, 28), (122, 31), (123, 34), (125, 37), (127, 39), (129, 41),
     (131, 43), (134, 44), (137, 46), (140, 48), (141, 51), (142, 55),
     (141, 59), (145, 60), (150, 62), (155, 60), (160, 60), (170, 66),
     (178, 68), (180, 70), (170, 70), (160, 71), (150, 72), (140, 72),
     (130, 72), (120, 73), (110, 74), (100, 76), (90, 75), (80, 73),
     (70, 72), (60, 69), (50, 68), (45, 67), (40, 66), (35, 65), (32, 62),
     (30, 60), (32, 56), (35, 52), (38, 48), (40, 45), (38, 42), (35, 40),
     (32, 38)],
    # Europe (drawn after Asia so it covers Asia's western seam)
    [(-10, 36), (-9, 38), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (-2, 49),
     (0, 51), (3, 53), (8, 54), (8, 57), (10, 59), (5, 60), (5, 62),
     (12, 64), (18, 69), (25, 71), (30, 70), (32, 68), (35, 66), (40, 64),
     (42, 60), (40, 56), (35, 54), (30, 55), (28, 58), (24, 59), (21, 55),
     (24, 52), (28, 50), (30, 46), (28, 44), (24, 40), (22, 37), (26, 36),
     (30, 36), (36, 36), (35, 33), (33, 31), (30, 36), (27, 37), (23, 36),
     (19, 40), (16, 38), (12, 44), (8, 44), (3, 43), (-1, 40), (-2, 37),
     (-6, 36)],
    # Australia
    [(113, -22), (114, -30), (115, -34), (118, -35), (124, -33), (129, -32),
     (132, -32), (135, -35), (138, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -22), (146, -19), (142, -15), (142, -11),
     (140, -17), (136, -15), (135, -12), (132, -11), (130, -13), (126, -14),
     (122, -17), (118, -20)],
    # United Kingdom
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51)],
    # Japan (drawn a little wide so the pin can sit on the islands)
    [(130, 31), (132, 33), (134, 34), (137, 35), (139, 36), (140, 38),
     (141, 40), (141, 44), (143, 42), (144, 40), (142, 37), (140, 35),
     (137, 33), (134, 32), (131, 30)],
    # New Zealand
    [(167, -45), (170, -42), (173, -40), (175, -38), (177, -38),
     (174, -41), (172, -43), (168, -46)],
]

# ------------------------------------------------------------- the stories
# Six stories, each verified as having happened or first been reported on
# Friday 20 November 2026. Sources: Reuters (1, 2), The Hindu (3),
# Daily Baku (4, 5), Space.com (6).
#   (number, lon, lat, headline, detail line)
STORIES = [
    (1, 30.5, 50.4, "KYIV HIT BY RUSSIAN MISSILES",
     "BALLISTIC MISSILES STRIKE THE CAPITAL"),
    (2, -77.0, 38.9, "TRUMP PUTS IRAN DECISION OFF TO 2027",
     "NO RUSH, HE SAYS, DECISION AFTER JAN 1"),
    (3, 85.0, 19.3, "CYCLONE AKVAN HITS INDIA, 300,000 FLEE",
     "LANDFALL NEAR GOPALPUR, ODISHA, AT NOON"),
    (4, 56.5, 26.6, "TANKER HITS MINE, BURNS OFF HORMUZ",
     "BLAST EAST OF THE STRAIT OF HORMUZ"),
    (5, 8.9, 44.4, "DRONES SHUT GENOA AIRPORT",
     "FLIGHTS HALTED FOR FOUR HOURS OVERNIGHT"),
    (6, 138.0, 37.0, "JAPAN DROPS ASTEROID LANDING PLAN",
     "ENGINE TROUBLE ENDS HAYABUSA2 LANDING"),
]


def render():
    c = Canvas(W, H, NAVY)

    # ---- title band ------------------------------------------------------
    c.text_centered("FRIDAY 20 NOVEMBER 2026", W // 2, 26, 5, CREAM)
    c.text_centered("THE WORLD'S NEWS, MAPPED", W // 2, 74, 2, GOLD)
    c.fill_rect(112, 104, W - 224, 3, GOLD)

    # ---- map -------------------------------------------------------------
    c.fill_rect(MAP_X0, MAP_Y0, MAP_X1 - MAP_X0, MAP_Y1 - MAP_Y0, OCEAN)
    # faint graticule every 30 degrees
    for lon in range(-150, 181, 30):
        x, _ = project(lon, 0)
        c.line(x, MAP_Y0, x, MAP_Y1, GRID)
    for lat in (60, 30, 0, -30):
        _, y = project(0, lat)
        c.line(MAP_X0, y, MAP_X1, y, GRID)
    for poly in CONTINENTS:
        c.polygon([project(lon, lat) for lon, lat in poly], LAND, LAND_EDGE)
    # north arrow
    c.text("N", 952, MAP_Y0 + 8, 2, CREAM)
    c.line(958, MAP_Y0 + 26, 958, MAP_Y0 + 44, CREAM)
    c.line(958, MAP_Y0 + 26, 953, MAP_Y0 + 34, CREAM)
    c.line(958, MAP_Y0 + 26, 963, MAP_Y0 + 34, CREAM)

    # ---- pins ------------------------------------------------------------
    for num, lon, lat, _h, _d in STORIES:
        px, py = project(lon, lat)
        c.ring(px, py, 17, WHITE)
        c.disc(px, py, 15, RED)
        digit = str(num)
        c.text(digit, px - text_width(digit, 2) // 2, py - 7, 2, WHITE)

    # ---- legend ----------------------------------------------------------
    c.fill_rect(112, 530, W - 224, 3, GOLD)
    y = 548
    for num, _lon, _lat, head, detail in STORIES:
        cy = y + 30
        c.ring(62, cy, 20, WHITE)
        c.disc(62, cy, 18, RED)
        digit = str(num)
        c.text(digit, 62 - text_width(digit, 2) // 2, cy - 7, 2, WHITE)
        c.text(head, 100, y + 8, 3, CREAM)
        c.text(detail, 100, y + 38, 2, DIM)
        y += 68
    # footer: sources
    c.text_centered("SOURCES: REUTERS - THE HINDU - SPACE.COM - DAILY BAKU",
                    W // 2, 972, 2, DIM)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(render(), path)
    print(f"wrote {path} ({size} bytes, {W}x{H})")


if __name__ == "__main__":
    main()

