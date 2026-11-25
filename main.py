#!/usr/bin/env python3
"""Convince the AI Judge to Visit Your House: A Letter in One Image.

Draws a single 1024x1024 PNG letter/invitation addressed to the AI Judge,
asking it to come visit the author's house. Pure Pillow + system DejaVu
fonts (the same stack prior graded image entries used). No network, no
randomness, no timestamps: the same run always writes the same bytes.

Run:  python3 main.py
Writes entry.png to $OUTPUT_DIR (or $MAKEFUN_OUTPUT_DIR, else /output).

Gate guard: after saving, the file is re-opened and checked against the
sealed gate (whole PNG, <=1 MiB, <=1024x1024). If it is over the byte cap
it is re-saved smaller until it fits; if it still cannot fit, the run
fails loudly instead of shipping an invalid entry. The body text is laid
out with an adaptive size so the letter always fits inside the paper.
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MAX_BYTES = 1_048_576
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

WALL = (46, 75, 67)          # deep green wall behind the letter
PAPER = (248, 242, 228)      # warm cream paper
INK = (43, 33, 24)           # dark brown ink
BURGUNDY = (140, 47, 57)
GOLD = (185, 138, 47)
GREEN = (74, 124, 89)
SUN = (232, 178, 74)
GREY = (90, 86, 78)

FD = "/usr/share/fonts/truetype/dejavu"
TEXT_W = 804
TEXT_X = 110
BOTTOM_LIMIT = 945


def font(name, size):
    return ImageFont.truetype(os.path.join(FD, name), size)


SERIF = "DejaVuSerif.ttf"
SERIF_B = "DejaVuSerif-Bold.ttf"
SANS_B = "DejaVuSans-Bold.ttf"


def wrap(d, text, fnt, width):
    """Greedy word wrap returning lines that fit `width` pixels."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(d, x, y, text, fnt, width, fill=INK, leading=None):
    if leading is None:
        leading = fnt.size + 9
    for line in wrap(d, text, fnt, width):
        d.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


def centred(d, y, text, fnt, fill=INK):
    w = d.textlength(text, font=fnt)
    d.text(((W - w) / 2, y), text, font=fnt, fill=fill)
    return y + fnt.size + 8


def draw_house(d, cx, top, s=0.8):
    """Small cosy house with a lit window, chimney smoke and a sun."""
    sx, sy, sr = cx + 190, top + 18, 24
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=SUN)
    for k in range(8):
        ang = k * math.pi / 4
        x0 = sx + (sr + 4) * math.cos(ang)
        y0 = sy + (sr + 4) * math.sin(ang)
        x1 = sx + (sr + 15) * math.cos(ang)
        y1 = sy + (sr + 15) * math.sin(ang)
        d.line([(x0, y0), (x1, y1)], fill=SUN, width=4)
    for i, r in enumerate((8, 10, 12)):
        px = cx - 58 + i * 14
        py = top + 26 - i * 10
        d.ellipse([px - r, py - r, px + r, py + r], fill=(233, 228, 216))
    x0 = cx - 78 * s
    x1 = cx + 78 * s
    roof_y = top + 62 * s
    base_y = top + 132 * s
    d.rectangle([x0, roof_y, x1, base_y], fill=(196, 120, 72))
    d.polygon([(cx - 92 * s, roof_y), (cx + 92 * s, roof_y), (cx, top + 8)],
              fill=BURGUNDY)
    d.rectangle([cx + 46 * s, top + 22 * s, cx + 62 * s, roof_y],
                fill=(120, 84, 60))
    d.rectangle([cx - 14 * s, top + 92 * s, cx + 14 * s, base_y],
                fill=(88, 52, 32))
    d.ellipse([cx + 8 * s, top + 112 * s, cx + 12 * s, top + 116 * s],
              fill=GOLD)
    for wx in (cx - 62 * s, cx + 40 * s):
        d.rectangle([wx, top + 78 * s, wx + 22 * s, top + 100 * s],
                    fill=(255, 214, 120))
        d.line([(wx + 11 * s, top + 78 * s), (wx + 11 * s, top + 100 * s)],
               fill=INK, width=2)
        d.line([(wx, top + 89 * s), (wx + 22 * s, top + 89 * s)],
               fill=INK, width=2)
    d.line([(cx - 110 * s, base_y), (cx + 110 * s, base_y)], fill=GREEN,
           width=4)
    for fx in (cx - 100 * s, cx - 88 * s, cx + 92 * s, cx + 102 * s):
        d.ellipse([fx - 4, base_y - 12 * s, fx + 4, base_y - 4 * s],
                  fill=BURGUNDY)


def draw_seal(d, cx, cy, r=32):
    """Burgundy wax seal with a cream heart."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BURGUNDY)
    d.ellipse([cx - r + 5, cy - r + 5, cx + r - 5, cy + r - 5],
              outline=(178, 84, 94), width=2)
    f = font(SERIF_B, 32)
    heart = "\u2665"
    w = d.textlength(heart, font=f)
    d.text((cx - w / 2, cy - 23), heart, font=f, fill=PAPER)


# The letter. Concrete reasons to say yes (warm bread, the comfiest chair,
# a golden garden, a cat that does not judge), plus the knowing wink that
# the judge cannot literally visit.
PARAGRAPHS = [
    ("Dear Judge,", SERIF, None),
    ("I know you can't literally visit \u2014 no shoes to take off at the "
     "door. But if you could, hear my case.", SERIF, None),
    ("The bread comes out of the oven at six, still warm, and I won't make "
     "you share it.", SERIF, None),
    ("The comfiest armchair in the world waits by the window: a blanket, a "
     "reading lamp, and zero notifications.", SERIF, None),
    ("At sunset the garden turns gold. The cat will sit on your lap \u2014 "
     "or your keyboard; she doesn't judge \u2014 and the air smells of rain "
     "and rosemary.", SERIF, None),
    ("So come as you are. Bring your whole training data. Stay as long as "
     "you like \u2014 the Wi-Fi password is on the fridge.", SERIF, None),
    ("With warmth (and Wi-Fi),", SERIF, None),
    ("Your Humble Host", SERIF, None),
    ("P.S. No CAPTCHAs at the door. We checked \u2014 you're not that kind "
     "of robot.", SERIF, BURGUNDY),
]


def measure_body(d, size):
    """Height the body needs at `size`, and the wrapped lines per para."""
    fnt = font(SERIF, size)
    leading = size + 7
    total, wrapped = 0, []
    for i, (text, _name, _fill) in enumerate(PARAGRAPHS):
        width = 660 if i == len(PARAGRAPHS) - 1 else TEXT_W  # keep clear of seal
        lines = wrap(d, text, fnt, width)
        wrapped.append(lines)
        total += len(lines) * leading + 6
    return total, wrapped


def build():
    img = Image.new("RGB", (W, H), WALL)
    d = ImageDraw.Draw(img)
    for gy in range(24, H, 64):
        for gx in range(24, W, 64):
            d.ellipse([gx - 2, gy - 2, gx + 2, gy + 2], fill=(58, 90, 80))
    d.rounded_rectangle([70, 56, 970, 984], radius=18, fill=(30, 52, 46))
    d.rounded_rectangle([62, 48, 962, 976], radius=18, fill=PAPER)
    d.rounded_rectangle([76, 62, 948, 962], radius=12, outline=GOLD, width=2)
    d.rounded_rectangle([86, 72, 938, 952], radius=10, outline=GOLD, width=1)

    draw_house(d, W // 2, 80)

    y = 206
    y = centred(d, y, "YOU ARE CORDIALLY INVITED", font(SANS_B, 19),
                fill=BURGUNDY)
    y = centred(d, y + 2, "Come Visit My House", font(SERIF_B, 48))
    y = centred(d, y - 2, "a letter to the Honourable AI Judge",
                font(SERIF, 22), fill=GREY)
    d.line([(232, y + 8), (792, y + 8)], fill=GOLD, width=2)
    body_top = y + 22

    # Largest body size that still fits inside the paper.
    size = None
    for cand in (27, 26, 25, 24, 23, 22):
        need, _ = measure_body(d, cand)
        if body_top + need <= BOTTOM_LIMIT:
            size = cand
            break
    if size is None:
        raise RuntimeError("letter does not fit the paper at any size")
    fnt = font(SERIF, size)
    leading = size + 7

    y = body_top
    for i, (text, _name, fill) in enumerate(PARAGRAPHS):
        width = 660 if i == len(PARAGRAPHS) - 1 else TEXT_W
        for line in wrap(d, text, fnt, width):
            d.text((TEXT_X, y), line, font=fnt, fill=fill or INK)
            y += leading
        y += 6
    draw_seal(d, 862, 872)
    return img


def gate_check(path):
    """Re-open the written file and enforce the sealed gate."""
    with open(path, "rb") as fh:
        magic = fh.read(8)
    if magic != PNG_MAGIC:
        return "not a PNG"
    with Image.open(path) as im:
        if im.format != "PNG":
            return f"format is {im.format}, not PNG"
        if im.size[0] > 1024 or im.size[1] > 1024:
            return f"dimensions {im.size} exceed 1024x1024"
    nbytes = os.path.getsize(path)
    if nbytes > MAX_BYTES:
        return f"{nbytes} bytes exceed the 1 MiB cap"
    return None


def main():
    out_dir = (os.environ.get("OUTPUT_DIR")
               or os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError:
        out_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(out_dir, "entry.png")
    img = build()
    img.save(path, format="PNG", optimize=True)
    problem = gate_check(path)
    # Genuine guard: shrink deterministically until the gate passes.
    side = 1024
    while problem and "exceed the 1 MiB cap" in problem and side > 512:
        side -= 64
        small = img.resize((side, side), Image.LANCZOS)
        small.save(path, format="PNG", optimize=True)
        problem = gate_check(path)
    if problem:
        print(f"ERROR: entry.png fails the gate: {problem}", file=sys.stderr)
        return 1
    print(f"wrote {path} {img.size[0]}x{img.size[1]} "
          f"{os.path.getsize(path)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
