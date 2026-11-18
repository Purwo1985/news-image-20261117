#!/usr/bin/env python3
"""news-image-20261117: render a one-page newspaper infographic that sums up
the world news of Tuesday 17 November 2026 as a 1024x1024 PNG.

Pure standard library. The PNG encoder is hand-rolled (zlib + struct), the
type is a 5x7 bitmap font defined below, and every story is embedded in this
file as data. No network, no clock, no randomness: two runs write byte
identical output.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   (writes out/entry.png)
Grader: python3 main.py                        (writes /output/entry.png)
"""

import math
import os
import struct
import sys
import zlib

# ---------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is 7 rows of 5 cells; '#' is ink, '.' is blank.
# Only the characters the infographic uses are defined (upper case, digits
# and a small set of punctuation); everything is rendered in capitals.
# ---------------------------------------------------------------------------

FONT = {
    "A": ("..#..", ".#.#.", "#...#", "#####", "#...#", "#...#", "#...#"),
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
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "*": (".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "....."),
}

CHAR_W = 5
CHAR_H = 7
CHAR_ADV = 6  # advance per character, in font cells


def text_width(text, scale):
    """Pixel width of `text` rendered at `scale`."""
    return len(text) * CHAR_ADV * scale - scale


def wrap_text(text, scale, max_width):
    """Greedy word wrap. Returns a list of lines that fit max_width px."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# Canvas: an RGB pixel buffer with simple drawing primitives.
# ---------------------------------------------------------------------------

class Canvas:
    def __init__(self, width, height, color):
        self.w = width
        self.h = height
        self.px = bytearray(color * (width * height))

    def _set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = color

    def fill(self, color):
        self.px = bytearray(color * (self.w * self.h))

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:(yy * self.w + x1) * 3] = color * (x1 - x0)

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        """Bresenham line with square brush of side `thick`."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = thick // 2
        while True:
            self.rect(x0 - r, y0 - r, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, radius, color, filled=True):
        """Midpoint circle; filled disc or 1px ring."""
        r = radius
        x = 0
        y = r
        d = 1 - r
        while x <= y:
            if filled:
                for xx in range(cx - x, cx + x + 1):
                    self._set(xx, cy + y, color)
                    self._set(xx, cy - y, color)
                for xx in range(cx - y, cx + y + 1):
                    self._set(xx, cy + x, color)
                    self._set(xx, cy - x, color)
            else:
                for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                               (cx + x, cy - y), (cx - x, cy - y),
                               (cx + y, cy + x), (cx - y, cy + x),
                               (cx + y, cy - x), (cx - y, cy - x)):
                    self._set(px, py, color)
            x += 1
            if d < 0:
                d += 2 * x + 1
            else:
                y -= 1
                d += 2 * (x - y) + 1

    def ring(self, cx, cy, radius, color, thick=3):
        for rr in range(radius - thick + 1, radius + 1):
            self.circle(cx, cy, rr, color, filled=False)

    def polygon(self, points, color):
        """Scanline fill of a simple polygon given as [(x, y), ...]."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.rect(int(xs[k]), y, max(1, int(xs[k + 1]) - int(xs[k])), 1, color)

    def text(self, x, y, s, scale, color):
        """Draw text at top-left (x, y); returns pixel width drawn."""
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(CHAR_H):
                bits = glyph[row]
                for col in range(CHAR_W):
                    if bits[col] == "#":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += CHAR_ADV * scale
        return cx - x - scale

# ---------------------------------------------------------------------------
# Palette (RGB byte triples).
# ---------------------------------------------------------------------------

PAPER = bytes((247, 243, 234))   # warm newsprint off-white
INK = bytes((20, 33, 61))        # dark navy, header/footer bands
INK_SOFT = bytes((38, 54, 88))
WHITE = bytes((255, 255, 255))
GOLD = bytes((212, 175, 55))     # header rules and date underline
CARD = bytes((255, 255, 255))
CARD_EDGE = bytes((203, 196, 180))
BODY = bytes((48, 48, 48))       # body copy grey-black
MUTED = bytes((110, 108, 100))   # small print

# One accent colour per story, used for its kicker, top bar and icon.
NAVY = bytes((20, 33, 61))
RED = bytes((178, 34, 34))
TEAL = bytes((13, 110, 110))
ORANGE = bytes((196, 94, 12))
GREEN = bytes((34, 110, 58))
PURPLE = bytes((96, 58, 140))

# ---------------------------------------------------------------------------
# The news of Tuesday 17 November 2026, as reported that day.
# Each story: region/field tag, headline, one-sentence summary.
# ---------------------------------------------------------------------------

STORIES = [
    {
        "tag": "ASIA  /  DIPLOMACY",
        "color": NAVY,
        "headline": "QUAD LEADERS MEET IN MANILA",
        "body": ("TRUMP, MODI, TAKAICHI AND ALBANESE HOLD TALKS ON THE "
                 "SIDELINES OF THE ASEAN SUMMIT. TRUMP SAYS THE US WILL "
                 "CATCH CHINA ON RARE EARTHS WITHIN 10 MONTHS."),
        "icon": "summit",
    },
    {
        "tag": "HEALTH  /  AMERICAS",
        "color": RED,
        "headline": "US LOSES MEASLES-FREE STATUS",
        "body": ("PAHO SAYS MEASLES HAS SPREAD WITHOUT A BREAK FOR OVER A "
                 "YEAR. THE US HELD ELIMINATION STATUS SINCE 2000. "
                 "MEXICO AND BOLIVIA LOSE IT TOO."),
        "icon": "cross",
    },
    {
        "tag": "WAR IN UKRAINE",
        "color": TEAL,
        "headline": "CRIMEAN BRIDGE HIT AS KYIV BRIDGES ARE DAMAGED",
        "body": ("UKRAINE STRIKES THE CRIMEA LINK, HALTING TRAFFIC. AN "
                 "OVERNIGHT RUSSIAN MISSILE ATTACK DAMAGES TWO BRIDGES "
                 "IN KYIV AND DISRUPTS TRANSPORT."),
        "icon": "bridge",
    },
    {
        "tag": "MIDDLE EAST",
        "color": ORANGE,
        "headline": "BAHRAIN INTERCEPTS IRANIAN ATTACKS",
        "body": ("BAHRAIN SAYS ITS AIR DEFENCES STOPPED IRANIAN STRIKES "
                 "NEAR A US BASE, THE THIRD SUCH ATTEMPT IN FIVE DAYS. "
                 "A THIRD US AIRCRAFT CARRIER ARRIVES IN THE REGION."),
        "icon": "bolt",
    },
    {
        "tag": "DIPLOMACY",
        "color": GREEN,
        "headline": "FIRST US-CHINA-RUSSIA SUMMIT SET FOR 19 NOV",
        "body": ("CHINA CONFIRMS XI, TRUMP AND PUTIN WILL MEET IN "
                 "SHENZHEN ON 19 NOVEMBER, THE FIRST SUCH THREE-WAY "
                 "SUMMIT BETWEEN THE THREE LEADERS."),
        "icon": "triangle",
    },
    {
        "tag": "WEATHER  /  INDIA",
        "color": PURPLE,
        "headline": "CYCLONE AKVAN NEARS INDIA'S EAST COAST",
        "body": ("THE STORM IS SET TO MAKE LANDFALL ON 20 NOVEMBER. "
                 "ODISHA BEGINS EVACUATING PEOPLE FROM VULNERABLE "
                 "AREAS AS HEAVY RAIN IS FORECAST."),
        "icon": "cyclone",
    },
]

FOOTER_LINES = [
    "ALSO ON 17 NOVEMBER: ULA SAYS VULCAN'S FIRST STAGE UNDERPERFORMED IN",
    "SUNDAY'S FAILED LAUNCH, LOSING 40 AMAZON SATELLITES / COP31 DRAFT SETS",
    "OUT CLASHING CLIMATE PRIORITIES / JPMORGAN SAYS BANKING IS BACK TO NORMAL",
]

# ---------------------------------------------------------------------------
# Icons: small pictograms drawn with the canvas primitives, centred at
# (cx, cy) inside a ring of radius R.
# ---------------------------------------------------------------------------

R = 24  # icon radius


def draw_icon(cv, kind, cx, cy, color):
    if kind == "summit":
        # Four leaders around a table: four dots joined in a ring.
        pts = [(cx - 13, cy - 13), (cx + 13, cy - 13),
               (cx + 13, cy + 13), (cx - 13, cy + 13)]
        for i in range(4):
            cv.line(pts[i][0], pts[i][1], pts[(i + 1) % 4][0],
                    pts[(i + 1) % 4][1], color, 3)
        for px, py in pts:
            cv.circle(px, py, 6, color)
        cv.circle(cx, cy, 5, color)
    elif kind == "cross":
        # Medical cross.
        cv.rect(cx - 6, cy - 16, 12, 32, color)
        cv.rect(cx - 16, cy - 6, 32, 12, color)
    elif kind == "bridge":
        # A suspension bridge: deck, two towers, two arcs.
        cv.line(cx - 20, cy + 10, cx + 20, cy + 10, color, 3)
        cv.line(cx - 14, cy - 12, cx - 14, cy + 10, color, 3)
        cv.line(cx + 14, cy - 12, cx + 14, cy + 10, color, 3)
        for t in range(0, 21):
            u = t / 20.0
            x = int(cx - 14 + 28 * u)
            y = int(cy - 12 + 14 * (1 - (2 * u - 1) ** 2) * -1 + 14)
            cv.rect(x, y, 2, 2, color)
        cv.circle(cx - 14, cy - 14, 3, color)
        cv.circle(cx + 14, cy - 14, 3, color)
    elif kind == "bolt":
        # Lightning bolt.
        cv.polygon([(cx + 4, cy - 18), (cx - 10, cy + 2), (cx - 1, cy + 2),
                    (cx - 4, cy + 18), (cx + 10, cy - 2), (cx + 1, cy - 2)],
                   color)
    elif kind == "triangle":
        # Three leaders: three dots at the corners of a triangle.
        pts = [(cx, cy - 15), (cx + 16, cy + 11), (cx - 16, cy + 11)]
        for i in range(3):
            cv.line(pts[i][0], pts[i][1], pts[(i + 1) % 3][0],
                    pts[(i + 1) % 3][1], color, 3)
        for px, py in pts:
            cv.circle(px, py, 6, color)
    elif kind == "cyclone":
        # Spiral storm: concentric arcs of growing radius.
        for r in (5, 10, 15, 20):
            steps = 26
            for s in range(steps + 1):
                a = 3.141592653589793 * 2 * s / steps * 0.8
                x = int(cx + r * math.cos(a))
                y = int(cy + r * math.sin(a))
                cv.rect(x, y, 3, 3, color)
    else:
        cv.circle(cx, cy, 6, color)


# ---------------------------------------------------------------------------
# Layout: 1024 x 1024 newspaper front page.
# ---------------------------------------------------------------------------

W, H = 1024, 1024


def render():
    cv = Canvas(W, H, PAPER)

    # --- Header band -------------------------------------------------------
    cv.rect(0, 0, W, 168, INK)
    cv.hline(0, 168, W, GOLD, 4)
    label = "THE WORLD IN ONE DAY"
    cv.text((W - text_width(label, 2)) // 2, 22, label, 2, GOLD)
    date = "17 NOVEMBER 2026"
    cv.text((W - text_width(date, 7)) // 2, 50, date, 7, WHITE)
    cv.hline((W - 420) // 2, 112, 420, GOLD, 2)
    sub = "TUESDAY  -  SIX STORIES FROM AROUND THE GLOBE"
    cv.text((W - text_width(sub, 2)) // 2, 126, sub, 2, WHITE)

    # --- Story cards: 2 columns x 3 rows ----------------------------------
    card_w, card_h = 492, 238
    gap = 16
    x0, y0 = 16, 184
    for idx, story in enumerate(STORIES):
        col = idx % 2
        row = idx // 2
        cx = x0 + col * (card_w + gap)
        cy = y0 + row * (card_h + gap)
        color = story["color"]

        cv.rect(cx, cy, card_w, card_h, CARD)
        cv.rect(cx, cy, card_w, 6, color)              # accent bar
        # thin border
        cv.hline(cx, cy + card_h - 1, card_w, CARD_EDGE, 1)
        cv.vline(cx, cy, card_h, CARD_EDGE, 1)
        cv.vline(cx + card_w - 1, cy, card_h, CARD_EDGE, 1)

        # Kicker tag, left; icon ring, right.
        cv.text(cx + 18, cy + 22, story["tag"], 2, color)
        icx, icy = cx + card_w - 46, cy + 48
        cv.ring(icx, icy, R + 4, color, 3)
        draw_icon(cv, story["icon"], icx, icy, color)

        # Headline, up to 2 lines, scale 3.
        head_lines = wrap_text(story["headline"], 3, card_w - 36)[:2]
        hy = cy + 58
        for line in head_lines:
            cv.text(cx + 18, hy, line, 3, INK)
            hy += 27

        # Body copy, scale 2.
        body_lines = wrap_text(story["body"], 2, card_w - 36)
        by = hy + 10
        for line in body_lines:
            cv.text(cx + 18, by, line, 2, BODY)
            by += 19

    # --- Footer band -------------------------------------------------------
    cv.rect(0, 946, W, H - 946, INK)
    cv.hline(0, 946, W, GOLD, 3)
    fy = 958
    for line in FOOTER_LINES:
        cv.text(16, fy, line, 2, WHITE)
        fy += 17

    return cv


# ---------------------------------------------------------------------------
# Minimal PNG encoder: 8-bit RGB, no ancillary chunks, zlib level 9.
# Deterministic: no timestamps, no random data anywhere.
# ---------------------------------------------------------------------------

def png_bytes(cv):
    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(render())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, %dx%d)" % (path, len(data), W, H))
    return 0


if __name__ == "__main__":
    sys.exit(main())
