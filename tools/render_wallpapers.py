"""Render the AstraLabs wallpapers.

Two packages:
  AstraLabs        dot field, lockup centred, two acid registration marks
  AstraLabs-Field  dot field and registration marks only

Run with a Python that has Pillow and CairoSVG:
  python3 tools/render_wallpapers.py /path/to/astralabs-lockup.svg
"""
import io, json, math, sys
from pathlib import Path
from PIL import Image, ImageDraw
import cairosvg

ROOT = Path(__file__).resolve().parent.parent
LOCKUP = Path(sys.argv[1])
SIZES = [(5120, 1440), (3840, 1080), (3440, 1440), (2560, 1080), (3840, 2160), (2560, 1440), (1920, 1080), (1920, 1200), (2560, 1600)]
VOID = (10, 9, 9)
BONE = (237, 230, 225)
ACID = (182, 255, 46)
SS = 2  # supersample


def field(W, H, ss):
    """Dot grid, 16px pitch, a little brighter toward the centre (same falloff as the login field)."""
    im = Image.new('RGB', (W * ss, H * ss), VOID)
    d = ImageDraw.Draw(im)
    cx, cy = W / 2, H / 2
    reach = math.hypot(cx, cy)
    pitch, r = 16, 1.0
    for gx in range(8, W, pitch):
        for gy in range(8, H, pitch):
            edge = max(0.0, 1 - math.hypot(gx - cx, gy - cy) / reach)
            a = 0.07 + edge * 0.11
            c = tuple(round(VOID[i] + (BONE[i] - VOID[i]) * a) for i in range(3))
            d.rectangle([(gx - r) * ss, (gy - r) * ss, (gx + r) * ss - 1, (gy + r) * ss - 1], fill=c)
    return im


def reg_marks(im, W, H, ss):
    """Acid plus marks, top-left and bottom-right, on grid intersections."""
    d = ImageDraw.Draw(im)
    arm = max(12, round(min(W, H) * 0.014))
    inset = 8 + 16 * max(2, round(min(W, H) / 360))
    for x, y in ((inset, inset), (W - 1 - inset, H - 1 - inset)):
        # 1px lines on whole pixels so they stay crisp after downsampling
        d.rectangle([(x - arm) * ss, y * ss, (x + arm + 1) * ss - 1, (y + 1) * ss - 1], fill=ACID)
        d.rectangle([x * ss, (y - arm) * ss, (x + 1) * ss - 1, (y + arm + 1) * ss - 1], fill=ACID)


def lockup(im, W, H, ss):
    w = round(min(W * 0.3, H * 0.42))
    png = cairosvg.svg2png(url=str(LOCKUP), output_width=w * ss)
    lk = Image.open(io.BytesIO(png)).convert('RGBA')
    im.paste(lk, ((W * ss - lk.width) // 2, (H * ss - lk.height) // 2), lk)


def package(pid, name, desc, with_lockup):
    base = ROOT / 'wallpapers' / pid
    (base / 'contents' / 'images').mkdir(parents=True, exist_ok=True)
    for W, H in SIZES:
        im = field(W, H, SS)
        reg_marks(im, W, H, SS)
        if with_lockup:
            lockup(im, W, H, SS)
        im = im.resize((W, H), Image.BOX)  # exact 2x2 average keeps 1px lines crisp
        im.save(base / 'contents' / 'images' / f'{W}x{H}.png', optimize=True)
        if (W, H) == (3840, 2160):
            im.resize((400, 225), Image.LANCZOS).save(base / 'contents' / 'screenshot.png')
        print(pid, W, H)
    (base / 'metadata.json').write_text(json.dumps({
        'KPlugin': {
            'Authors': [{'Name': 'Emily Astranova', 'Email': 'emily@astralabs.dev'}],
            'Id': pid, 'Name': name, 'Description': desc, 'License': 'AGPL-3.0',
        }
    }, indent=4) + '\n')


package('AstraLabs', 'AstraLabs', 'Dot field with the AstraLabs lockup', True)
package('AstraLabs-Field', 'AstraLabs Field', 'Dot field and registration marks', False)
