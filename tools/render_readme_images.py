"""Render the README images into docs/images/.

  banner.png         the 32:9 wallpaper, scaled for the top of the README
  terminal.png       Konsole with astralabs-fetch (image logo), from real fastfetch output
  terminal-text.png  the same summary with the block-character logo (SSH, tmux)
  palette.png        desktop colour roles and the 16 terminal colours
  splash.gif         the boot splash, captured from the real QML off screen

Needs Pillow, CairoSVG and fontTools, plus fastfetch and ksplashqml for the live parts:
  python3 tools/render_readme_images.py
"""
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs' / 'images'
OUT.mkdir(parents=True, exist_ok=True)

MONO = ROOT / 'fonts' / 'MartianMono[wdth,wght].ttf'
FALLBACK = Path('/usr/share/fonts/google-noto/NotoSansMono-Regular.ttf')   # box drawing and blocks
UI = Path('/usr/share/fonts/google-noto/NotoSans-Regular.ttf')            # window title

VOID, PLATE, RULE, RULE_SUB = (10, 9, 9), (19, 18, 18), (44, 42, 41), (28, 27, 26)
BONE, ASH, ACID, MARK = (237, 230, 225), (142, 131, 128), (182, 255, 46), (255, 255, 255)
S = 2  # render at 2x


def mono(size, wdth=112, wght=400):
    """Martian Mono; the defaults match the instance Konsole uses (weight 400, width 112)."""
    f = ImageFont.truetype(str(MONO), size)
    f.set_variation_by_axes([wght, wdth])   # axis order in this font: weight, then width
    return f


# ---------------------------------------------------------------- banner
def banner():
    im = Image.open(ROOT / 'wallpapers/AstraLabs/contents/images/5120x1440.png')
    im.resize((1600, 450), Image.LANCZOS).save(OUT / 'banner.png', optimize=True)


# ---------------------------------------------------------------- terminal
class Term:
    """Draws ANSI text into a cell grid, the way Konsole lays it out."""

    def __init__(self, cols, rows, size=13 * S):
        self.font = mono(size)
        self.bold = mono(size, wght=700)
        self.fb = ImageFont.truetype(str(FALLBACK), size)
        self.has = set(TTFont(str(MONO)).getBestCmap())
        self.cw = round(self.font.getlength('M'))
        self.ch = round(size * 1.42) + 2 * S          # line height plus the profile's 2px spacing
        self.cols, self.rows = cols, rows
        self.pad = 6 * S
        self.img = Image.new('RGB', (cols * self.cw + 2 * self.pad, rows * self.ch + 2 * self.pad), VOID)
        self.d = ImageDraw.Draw(self.img)

    def xy(self, col, row):
        return self.pad + col * self.cw, self.pad + row * self.ch

    def put(self, col, row, text, color=BONE, bold=False):
        for i, c in enumerate(text):
            x, y = self.xy(col + i, row)
            if c in '█▀▄':                             # Konsole draws block elements itself, edge to edge
                top, bot = (y, y + self.ch) if c == '█' else (y, y + self.ch // 2) if c == '▀' else (y + self.ch // 2, y + self.ch)
                self.d.rectangle([x, top, x + self.cw - 1, bot - 1], fill=color)
                continue
            if c in '━─':                              # and box-drawing lines
                h = 2 * S if c == '━' else S
                cy = y + self.ch // 2
                self.d.rectangle([x, cy - h // 2, x + self.cw - 1, cy - h // 2 + h - 1], fill=color)
                continue
            if c in '■':
                m = self.cw // 5
                self.d.rectangle([x + m, y + self.ch * 0.3, x + self.cw - m, y + self.ch * 0.7], fill=color)
                continue
            f = (self.bold if bold else self.font) if ord(c) in self.has else self.fb
            self.d.text((x, y + (self.ch - f.size * 1.25) / 2), c, font=f, fill=color)

    def ansi(self, text, col0=0, row0=0):
        """Render fastfetch output; absolute column moves (CSI n G) are offset by col0."""
        for r, line in enumerate(text.split('\n')):
            col, color, bold = col0, BONE, False
            for tok in re.split(r'(\x1b\[[0-9;?]*[a-zA-Z])', line):
                m = re.fullmatch(r'\x1b\[([0-9;?]*)([a-zA-Z])', tok)
                if m:
                    args, cmd = m.groups()
                    if cmd == 'G':
                        col = col0 + int(args or 1) - 1
                    elif cmd == 'C':
                        col += int(args or 1)
                    elif cmd == 'm':
                        p = [int(x) for x in args.split(';') if x.isdigit()] or [0]
                        i = 0
                        while i < len(p):
                            if p[i] == 0: color, bold = BONE, False
                            elif p[i] == 1: bold = True
                            elif p[i] == 38 and i + 4 < len(p) + 1 and p[i + 1] == 2:
                                color = tuple(p[i + 2:i + 5]); i += 4
                            i += 1
                    continue
                self.put(col, row0 + r, tok, color, bold)
                col += len(tok)


def window(term, title):
    """Wrap the terminal in a Breeze titlebar with the AstraLabs colours."""
    tb = 34 * S
    W, H = term.img.width, term.img.height + tb
    im = Image.new('RGB', (W + 2 * S, H + 2 * S), RULE)
    win = Image.new('RGB', (W, H), VOID)
    d = ImageDraw.Draw(win)
    d.rectangle([0, tb - S, W, tb - 1], fill=RULE_SUB)
    f = ImageFont.truetype(str(UI), 11 * S)
    tw = d.textlength(title, font=f)
    d.text(((W - tw) / 2, (tb - 15 * S) / 2), title, font=f, fill=BONE)
    # minimise, maximise, close
    cy, r = tb // 2, 5 * S
    for i, kind in enumerate(('min', 'max', 'close')):
        cx = W - (16 + 28 * (2 - i)) * S
        if kind == 'min':
            d.line([cx - r, cy + 2 * S, cx + r, cy + 2 * S], fill=BONE, width=S)
        elif kind == 'max':
            d.rectangle([cx - r, cy - r, cx + r, cy + r], outline=BONE, width=S)
        else:
            d.line([cx - r, cy - r, cx + r, cy + r], fill=BONE, width=S)
            d.line([cx - r, cy + r, cx + r, cy - r], fill=BONE, width=S)
    win.paste(term.img, (0, tb))
    im.paste(win, (S, S))
    return im


def fastfetch(logo_args, cols):
    cfg = (ROOT / 'fastfetch/astralabs.jsonc').read_text()
    # fastfetch reports the program that launched it as the terminal and shell, which here is
    # this script; label them as they appear when it runs at login in Konsole
    bash = subprocess.run(['bash', '-c', 'echo ${BASH_VERSION%%(*}'], capture_output=True, text=True).stdout.strip()
    cfg = cfg.replace('{ "type": "terminal", "key": "terminal" }',
                      '{ "type": "terminal", "key": "terminal", "format": "Konsole 26.08.1" }')
    cfg = cfg.replace('{ "type": "shell", "key": "shell" }',
                      '{ "type": "shell", "key": "shell", "format": "bash %s" }' % bash)
    with tempfile.NamedTemporaryFile('w', suffix='.jsonc', delete=False) as t:
        t.write(cfg)
    env = dict(os.environ, COLUMNS=str(cols), COLORTERM='truecolor', TERM='xterm-256color')
    out = subprocess.run(['fastfetch', '--pipe', 'false', '-c', t.name, *logo_args], capture_output=True, text=True, env=env).stdout
    os.unlink(t.name)
    return out.rstrip('\n')


def prompt(term, row):
    term.put(0, row, '[emily@darknightpc ~]$ ', BONE)
    x, y = term.xy(23, row)
    term.d.rectangle([x, y + 2 * S, x + term.cw - 1, y + term.ch - 2 * S], fill=ACID)


def terminal_image():
    cols, logo_cols, gap = 100, 26, 4
    stats = fastfetch(['-l', 'none'], cols)
    n = len(stats.split('\n'))
    t = Term(cols, n + 3)
    # the image logo, scaled to 26 columns as astralabs-fetch asks fastfetch to
    logo = Image.open(ROOT / 'fastfetch/astralabs-terminal.png').convert('RGBA')
    lw = logo_cols * t.cw
    logo = logo.resize((lw, round(lw * logo.height / logo.width)), Image.LANCZOS)
    x, y = t.xy(2, 1)
    t.img.paste(logo, (x, y), logo)
    t.ansi(stats, col0=2 + logo_cols + gap)
    prompt(t, n + 1)
    window(t, '~ : bash — Konsole').save(OUT / 'terminal.png', optimize=True)


def terminal_text_image():
    cols = 104
    out = fastfetch(['--logo', str(ROOT / 'fastfetch/astralabs-logo.txt'), '--logo-type', 'file',
                     '--logo-color-1', '#ffffff', '--logo-color-2', '#b6ff2e'], cols)
    n = len(out.split('\n'))
    t = Term(cols, n + 2)
    t.ansi(out)
    t.put(0, n + 1, '[emily@darknightpc ~]$ ', BONE)
    window(t, 'emily@darknightpc: ~ — ssh').save(OUT / 'terminal-text.png', optimize=True)


# ---------------------------------------------------------------- palette
def palette():
    sw, gap, pad = 150 * S, 0, 28 * S
    desktop = [('void', VOID), ('plate', PLATE), ('button', RULE_SUB), ('rule', RULE), ('ash', ASH),
               ('bone', BONE), ('acid', ACID), ('ok', (77, 255, 136)), ('warn', (255, 162, 31)), ('down', (255, 46, 58))]
    kcol = {}
    cur = None
    for line in (ROOT / 'konsole/AstraLabs.colorscheme').read_text().splitlines():
        m = re.match(r'\[(Color\d(Intense)?)\]', line)
        if m: cur = m.group(1)
        elif cur and line.startswith('Color='):
            kcol[cur] = tuple(int(v) for v in line[6:].split(',')); cur = None
    names = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
    W = pad * 2 + len(desktop) * sw // 2 * 2
    W = pad * 2 + 10 * 96 * S
    lab, small = mono(10 * S, 85, 500), mono(9 * S, 85, 400)
    H = pad + 24 * S + 96 * S + 44 * S + 30 * S + 24 * S + 2 * 52 * S + 34 * S + pad
    im = Image.new('RGB', (W, H), VOID)
    d = ImageDraw.Draw(im)

    def label(x, y, text, col=ASH, f=lab):
        d.text((x, y), text.upper(), font=f, fill=col)

    y = pad
    label(pad, y, 'Desktop'); y += 24 * S
    cw = 96 * S
    for i, (n, c) in enumerate(desktop):
        x = pad + i * cw
        d.rectangle([x, y, x + cw - 1, y + 96 * S - 1], fill=c, outline=RULE)
        label(x + 8 * S, y + 96 * S + 8 * S, n, BONE, small)
        label(x + 8 * S, y + 96 * S + 24 * S, '#%02X%02X%02X' % c, ASH, small)
    y += 96 * S + 44 * S + 30 * S
    label(pad, y, 'Terminal'); y += 24 * S
    cw2 = (W - 2 * pad) // 8
    for row, suffix in enumerate(('', 'Intense')):
        for i in range(8):
            c = kcol[f'Color{i}{suffix}']
            x = pad + i * cw2
            d.rectangle([x, y, x + cw2 - 1, y + 52 * S - 1], fill=c, outline=VOID)
            if row == 0:
                tc = VOID if sum(c) > 380 else BONE
                label(x + 8 * S, y + 8 * S, names[i], tc, small)
        y += 52 * S
    im.save(OUT / 'palette.png', optimize=True)


# ---------------------------------------------------------------- splash
def splash():
    """Run the real splash QML off screen at 960×540 and grab frames into a GIF."""
    if not shutil.which('ksplashqml'):
        print('ksplashqml not found; skipping splash.gif'); return
    tmp = Path(tempfile.mkdtemp())
    pkg = tmp / 'lnf'
    shutil.copytree(ROOT / 'look-and-feel/dev.astralabs.desktop', pkg)
    qml = pkg / 'contents/splash/Splash.qml'
    s = qml.read_text()
    grab = f'''    width: 960; height: 540
    property int shot: 0
    Timer {{ interval: 40; repeat: true; running: true
        onTriggered: {{ const n = root.shot++; if (n < 100) root.grabToImage(r => r.saveToFile("{tmp}/f" + String(n).padStart(3, "0") + ".png")) }} }}
    Component.onCompleted: {{'''
    s = s.replace('    Component.onCompleted: {', grab, 1)
    qml.write_text(s)
    # a 16:9 offscreen screen, so the splash lays out as it would on a real display
    (tmp / 'screen.json').write_text(json.dumps({'screens': [{'name': 'readme', 'x': 0, 'y': 0, 'width': 1600, 'height': 900, 'logicalDpi': 96}]}))
    env = dict(os.environ, QT_QPA_PLATFORM=f'offscreen:configfile={tmp}/screen.json')
    try:
        subprocess.run(['ksplashqml', '--test', '--window', '--nofork', str(pkg)], env=env, timeout=6,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        pass
    frames = [Image.open(p).convert('RGB') for p in sorted(tmp.glob('f*.png'))]
    if not frames:
        print('no splash frames captured'); return
    def fit(f):  # the offscreen window may ignore the size; crop the centre to 16:9
        w, h = f.size
        if abs(w / h - 16 / 9) > 0.01:
            nh = round(w * 9 / 16) if w * 9 / 16 <= h else h
            nw = round(nh * 16 / 9)
            f = f.crop(((w - nw) // 2, (h - nh) // 2, (w + nw) // 2, (h + nh) // 2))
        return f.resize((960, 540), Image.LANCZOS)
    frames = [fit(f) for f in frames]
    # fixed palette built from the brand: carbon→bone and carbon→acid ramps plus white,
    # so the dark field keeps its subtle greys and acid and white stay exact
    cols = []
    for i in range(128):
        t = i / 127
        cols.append(tuple(round(VOID[k] + (BONE[k] - VOID[k]) * t) for k in range(3)))
    for i in range(1, 112):
        t = i / 111
        cols.append(tuple(round(VOID[k] + (ACID[k] - VOID[k]) * t) for k in range(3)))
    cols += [MARK] * (256 - len(cols))
    pal = Image.new('P', (1, 1))
    pal.putpalette([c for rgb in cols for c in rgb])
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(OUT / 'splash.gif', save_all=True, append_images=q[1:],
              duration=[40] * (len(q) - 1) + [2500], loop=0, optimize=True)
    shutil.rmtree(tmp)
    print('splash frames', len(frames))


if __name__ == '__main__':
    banner(); terminal_image(); terminal_text_image(); palette(); splash()
    for p in sorted(OUT.iterdir()):
        print(p.relative_to(ROOT), Image.open(p).size, p.stat().st_size // 1024, 'KB')
