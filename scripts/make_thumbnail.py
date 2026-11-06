"""Thumbnail / Reel cover: the sunrise-over-Venus frame + big bold hook text.
1080 x 1920 (full Reel cover) with everything important inside the centre 1080 x 1440, so it survives
Instagram's 3:4 profile-grid crop. Also writes the 3:4 grid crop for a preview.
Run:  ~/.venvs/chatterbox/Scripts/python.exe scripts/make_thumbnail.py [frame]
"""
import sys, pathlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = pathlib.Path(__file__).resolve().parents[1]
FRAME = int(sys.argv[1]) if len(sys.argv) > 1 else 452
W, H = 1080, 1920
GRID_TOP = (H - 1440) // 2            # 240: top of the 3:4 grid crop
FONT = "C:/Windows/Fonts/Montserrat-Black.ttf"

bg = Image.open(ROOT / "blender" / "frames" / f"{FRAME:04d}.jpg").convert("RGB").resize((W, H), Image.LANCZOS)
# shift the picture down so the sunrise sits under the text, then lift contrast and warmth a little
canvas = Image.new("RGB", (W, H), (5, 6, 10)); canvas.paste(bg, (0, 260))
canvas = ImageEnhance.Contrast(canvas).enhance(1.12); canvas = ImageEnhance.Color(canvas).enhance(1.25)

# dark fade behind the text so it reads on any frame
fade = Image.new("L", (W, H), 0); fd = ImageDraw.Draw(fade)
for y in range(0, 1000):
    fd.line([(0, y), (W, y)], fill=int(235 * max(0.0, 1 - max(0, y - 560) / 440)))
canvas = Image.composite(Image.new("RGB", (W, H), (5, 6, 10)), canvas, fade)

d = ImageDraw.Draw(canvas)
def fit(text, max_w, size):
    while size > 20:
        f = ImageFont.truetype(FONT, size)
        if d.textlength(text, font=f) <= max_w: return f
        size -= 4
    return ImageFont.truetype(FONT, size)
def line(text, y, size, fill, stroke=10, max_w=960):
    f = fit(text, max_w, size); w = d.textlength(text, font=f)
    d.text(((W - w) / 2, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
    bbox = d.textbbox(((W - w) / 2, y), text, font=f, stroke_width=stroke); return bbox[3]

GOLD, WHITE = (255, 205, 64), (255, 255, 255)
y = GRID_TOP + 70
y = line("A DAY ON VENUS", y, 110, WHITE) + 10
y = line("LASTS LONGER", y, 150, GOLD, stroke=12) + 10
y = line("THAN ITS YEAR", y, 110, WHITE) + 40

# the proof, as a tag: 243 days vs 225 days
tag = "DAY: 243  ·  YEAR: 225"; tf = ImageFont.truetype(FONT, 54); tw = d.textlength(tag, font=tf)
pad_x, pad_y = 34, 18; x0 = (W - tw) / 2 - pad_x; y0 = y
d.rounded_rectangle([x0, y0, x0 + tw + 2 * pad_x, y0 + 54 + 2 * pad_y + 8], radius=44, fill=(255, 205, 64))
d.text(((W - tw) / 2, y0 + pad_y), tag, font=tf, fill=(18, 14, 6))

out = ROOT / "output"
canvas.save(out / "thumbnail.jpg", quality=94, optimize=True)
canvas.crop((0, GRID_TOP, W, GRID_TOP + 1440)).save(out / "thumbnail-grid-3x4.jpg", quality=92, optimize=True)
print("thumbnail.jpg (1080x1920) and thumbnail-grid-3x4.jpg (1080x1440) from frame", FRAME)
