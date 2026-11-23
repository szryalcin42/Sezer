#!/usr/bin/env python3
"""24 Kasım Öğretmenler Günü kampanyası — 9:16 dikey reel üretici.

Kara tahta temalı; kareleri PIL ile çizer, numpy ile müzik + efekt sesi
üretir, ffmpeg ile MP4'e çevirir.

Kullanım:  python3 make_ogretmenler_reel.py [çıktı.mp4]
           python3 make_ogretmenler_reel.py --preview <klasör>
"""
import math
import random
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
HERE = Path(__file__).resolve().parent
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = Path(ARGS[0]) if ARGS and "--preview" not in sys.argv else HERE / "ogretmenler_gunu_kampanya_reel.mp4"

FD = "/usr/share/fonts/opentype/inter/"
_fc = {}


def F(name, size):
    key = (name, size)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(FD + name + ".otf", size)
    return _fc[key]


CHALK = (244, 241, 230)
YELLOW = (255, 206, 84)
RED = (232, 72, 72)
PINK = (255, 150, 170)
BLUE = (120, 190, 255)
GREEN_L = (140, 220, 160)
WOOD = (120, 78, 42)
WOOD_D = (82, 50, 25)

# ---------------------------------------------------------------- senaryo
# (süre sn, tür)
SCENES = [(3.6, "hook"), (3.0, "today"), (5.2, "car"), (5.2, "house"),
          (4.4, "delivery"), (5.6, "draw")]

# Dış ses: voice_ogretmen/<sahne_no>.mp3 varsa sahne süresi sese göre uzatılır.
VOICE_DIR = HERE / "voice_ogretmen"
VOICE_DELAY = 0.25  # sahne başladıktan sonra sesin girişi (sn)


def clip_len(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())


VOICES = {}
for _i in range(len(SCENES)):
    _vp = VOICE_DIR / f"{_i}.mp3"
    if _vp.exists():
        VOICES[_i] = _vp
        _need = VOICE_DELAY + clip_len(_vp) + (1.5 if _i == len(SCENES) - 1 else 0.45)
        if _need > SCENES[_i][0]:
            SCENES[_i] = (round(_need, 2), SCENES[_i][1])

starts, _t = [], 0.0
for d_, _ in SCENES:
    starts.append(_t)
    _t += d_
TOTAL = _t
NFRAMES = int(TOTAL * FPS)


# ---------------------------------------------------------------- yardımcılar
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def back(x):
    """Hafif taşmalı (pop) yumuşatma."""
    x = clamp(x)
    c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def lerp(a, b, k):
    return a + (b - a) * k


def tr_num(n):
    return f"{int(round(n)):,}".replace(",", ".")


def make_bg():
    rng = np.random.default_rng(3)
    yy, xx = np.mgrid[0:H, 0:W]
    # kara tahta: koyu yeşil, ortası hafif aydınlık
    dist = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2)
    base = np.array([34, 74, 58]) * (1.15 - 0.9 * dist[..., None])
    noise = rng.normal(0, 5, (H, W, 1))
    arr = np.clip(base + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "RGB")
    # silinmiş tebeşir izleri
    smear = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(smear)
    r = random.Random(5)
    for _ in range(14):
        x, y = r.randint(-100, W), r.randint(0, H)
        sd.ellipse((x, y, x + r.randint(300, 700), y + r.randint(60, 160)), fill=r.randint(10, 24))
    smear = smear.filter(ImageFilter.GaussianBlur(40))
    img = Image.composite(Image.new("RGB", (W, H), (200, 210, 200)), img, smear)
    # ahşap çerçeve
    d = ImageDraw.Draw(img)
    fr = 34
    for i in range(fr):
        k = i / fr
        col = tuple(int(lerp(a, b, k)) for a, b in zip(WOOD_D, WOOD))
        d.rectangle((i, i, W - 1 - i, H - 1 - i), outline=col)
    d.rectangle((fr, fr, W - fr, H - fr), outline=(20, 45, 35), width=4)
    # tebeşir rafı (alt)
    d.rectangle((0, H - 110, W, H - 70), fill=WOOD)
    d.rectangle((0, H - 72, W, H - 60), fill=WOOD_D)
    for i, col in enumerate([CHALK, YELLOW, PINK, BLUE]):
        x = 140 + i * 70
        d.rounded_rectangle((x, H - 132, x + 54, H - 112), 9, fill=col)
    d.rounded_rectangle((760, H - 150, 930, H - 112), 8, fill=(60, 60, 70))  # silgi
    d.rectangle((760, H - 126, 930, H - 112), fill=(200, 190, 170))
    return img.convert("RGBA")


BG = make_bg()

# tebeşir dokusu maskesi (yazıya pürüz katmak için)
_g = np.random.default_rng(11).random((H, W))
CHALK_MASK = Image.fromarray((np.where(_g > 0.18, 255, 120)).astype(np.uint8), "L")


def text_sprite(text, font, color, stroke=0, stroke_col=None, chalky=True):
    bbox = font.getbbox(text, stroke_width=stroke)
    w, h = bbox[2] - bbox[0] + 8, bbox[3] - bbox[1] + 8
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((4 - bbox[0], 4 - bbox[1]), text, font=font, fill=color,
           stroke_width=stroke, stroke_fill=stroke_col)
    if chalky:
        a = im.getchannel("A")
        m = CHALK_MASK.crop((0, 0, w, h))
        a = Image.fromarray((np.array(a, dtype=np.uint16) * np.array(m) // 255).astype(np.uint8))
        im.putalpha(a)
    return im


_sc = {}


def sprite(text, font_name, size, color, **kw):
    key = (text, font_name, size, color, tuple(sorted(kw.items())))
    if key not in _sc:
        _sc[key] = text_sprite(text, F(font_name, size), color, **kw)
    return _sc[key]


def put(img, spr, cx, cy, alpha=1.0, scale=1.0, rot=0.0):
    """Sprite'ı (cx, cy) merkezli, alfa/ölçek/dönüş ile bas."""
    if alpha <= 0.01 or scale <= 0.01:
        return
    s = spr
    if abs(scale - 1) > 0.01:
        s = s.resize((max(1, int(s.width * scale)), max(1, int(s.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.1:
        s = s.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.99:
        a = s.getchannel("A").point(lambda v: int(v * alpha))
        s = s.copy()
        s.putalpha(a)
    img.alpha_composite(s, (int(cx - s.width / 2), int(cy - s.height / 2)))


def text(img, t, font_name, size, color, cx, cy, alpha=1.0, scale=1.0, rot=0.0, **kw):
    put(img, sprite(t, font_name, size, color, **kw), cx, cy, alpha, scale, rot)


def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def with_alpha(lay, alpha):
    if alpha >= 0.99:
        return lay
    a = lay.getchannel("A").point(lambda v: int(v * alpha))
    lay.putalpha(a)
    return lay


def chalk_line(d, pts, col, width, k=1.0):
    """Çoklu noktalı çizgiyi k oranında (0..1) çiz — 'tebeşirle çiziliyor' etkisi."""
    segs = list(zip(pts[:-1], pts[1:]))
    lens = [math.dist(a, b) for a, b in segs]
    total = sum(lens) * clamp(k)
    for (a, b), L in zip(segs, lens):
        if total <= 0:
            break
        f = min(1.0, total / L) if L else 1
        e = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        d.line([a, e], fill=col, width=width, joint="curve")
        total -= L


# ---------------------------------------------------------------- süslemeler
rng = random.Random(42)
CONFETTI = [(rng.uniform(60, W - 60), rng.uniform(-1.2, 0), rng.uniform(0.25, 0.5),
             rng.uniform(0, 6.28), rng.choice([YELLOW, RED, PINK, BLUE, GREEN_L, CHALK]),
             rng.uniform(14, 26)) for _ in range(90)]
DUST = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1.5, 4), rng.uniform(0.2, 1)) for _ in range(60)]


def draw_confetti(img, t0, strength=1.0):
    d = ImageDraw.Draw(img)
    for x, y0, sp, ph, col, s in CONFETTI:
        y = (y0 + t0 * sp) * H
        if y < -40 or y > H - 120:
            continue
        xx = x + 30 * math.sin(t0 * 3 + ph)
        ang = t0 * 5 + ph
        w_ = s * abs(math.cos(ang))
        a = int(255 * strength)
        d.polygon([(xx - w_, y - s * 0.4), (xx + w_, y - s * 0.4),
                   (xx + w_, y + s * 0.4), (xx - w_, y + s * 0.4)], fill=col + (a,))


def draw_dust(img, t):
    d = ImageDraw.Draw(img)
    for x, y, r, sp in DUST:
        yy = (y - t * 25 * sp) % H
        a = int(60 + 50 * math.sin(t * 2 + x))
        d.ellipse((x - r, yy - r, x + r, yy + r), fill=(255, 255, 255, a))


def draw_apple(img, cx, cy, s, a=1.0):
    lay = layer()
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - s, cy - s * 0.85, cx + s * 0.1, cy + s * 0.95), fill=RED)
    d.ellipse((cx - s * 0.1, cy - s * 0.85, cx + s, cy + s * 0.95), fill=RED)
    d.ellipse((cx - s * 0.55, cy - s * 0.5, cx - s * 0.25, cy - s * 0.1), fill=(255, 150, 140))
    d.line([(cx, cy - s * 0.7), (cx + s * 0.12, cy - s * 1.25)], fill=WOOD_D, width=max(3, int(s * 0.14)))
    d.ellipse((cx + s * 0.1, cy - s * 1.35, cx + s * 0.75, cy - s * 0.95), fill=(90, 190, 90))
    img.alpha_composite(with_alpha(lay, a))


def draw_pencil(img, cx, cy, L, ang, a=1.0):
    lay = Image.new("RGBA", (int(L) + 40, 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    h = 46
    y0 = 12
    d.rectangle((0, y0, 30, y0 + h), fill=(240, 150, 160))            # silgi
    d.rectangle((30, y0, 50, y0 + h), fill=(190, 190, 195))           # metal
    d.rectangle((50, y0, L - 70, y0 + h), fill=YELLOW)                # gövde
    d.rectangle((50, y0 + 15, L - 70, y0 + 31), fill=(240, 180, 50))
    d.polygon([(L - 70, y0), (L, y0 + h / 2), (L - 70, y0 + h)], fill=(240, 205, 160))
    d.polygon([(L - 22, y0 + h / 2 - 7), (L, y0 + h / 2), (L - 22, y0 + h / 2 + 7)], fill=(50, 50, 50))
    lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    put(img, lay, cx, cy, a)


# ---------------------------------------------------------------- çizimler
def draw_car(img, cx, cy, k, t, a=1.0):
    """Tebeşir stili araba. k: çizim ilerlemesi 0..1"""
    lay = layer()
    d = ImageDraw.Draw(lay)
    col = CHALK + (255,)
    s = 1.0
    body = [(cx - 300, cy + 40), (cx - 300, cy - 30), (cx - 250, cy - 50), (cx - 150, cy - 60),
            (cx - 80, cy - 140), (cx + 110, cy - 140), (cx + 190, cy - 60), (cx + 280, cy - 45),
            (cx + 310, cy - 10), (cx + 310, cy + 40), (cx + 250, cy + 40)]
    body2 = [(cx + 130, cy + 40), (cx - 130, cy + 40)]
    tail = [(cx - 250, cy + 40), (cx - 300, cy + 40)]
    chalk_line(d, body, col, 12, k * 1.4)
    chalk_line(d, body2, col, 12, k * 2 - 0.6)
    chalk_line(d, tail, col, 12, k * 2 - 0.8)
    # camlar
    if k > 0.45:
        kk = ease((k - 0.45) / 0.3)
        win = [(cx - 135, cy - 62), (cx - 70, cy - 122), (cx + 10, cy - 122), (cx + 10, cy - 62), (cx - 135, cy - 62)]
        win2 = [(cx + 40, cy - 62), (cx + 40, cy - 122), (cx + 100, cy - 122), (cx + 160, cy - 62), (cx + 40, cy - 62)]
        chalk_line(d, win, BLUE + (255,), 8, kk)
        chalk_line(d, win2, BLUE + (255,), 8, kk)
    # tekerlekler (dönüyor)
    if k > 0.3:
        kk = ease((k - 0.3) / 0.3)
        for wx in (cx - 190, cx + 190):
            r = 62 * kk
            d.ellipse((wx - r, cy + 40 - r, wx + r, cy + 40 + r), fill=(34, 74, 58, 255), outline=col, width=12)
            r2 = 22 * kk
            d.ellipse((wx - r2, cy + 40 - r2, wx + r2, cy + 40 + r2), outline=YELLOW + (255,), width=6)
            for j in range(4):
                an = t * 9 + j * math.pi / 2
                d.line([(wx + r2 * math.cos(an), cy + 40 + r2 * math.sin(an)),
                        (wx + (r - 10) * math.cos(an), cy + 40 + (r - 10) * math.sin(an))],
                       fill=col, width=4)
    # far
    if k > 0.8:
        d.ellipse((cx + 270, cy - 28, cx + 296, cy - 6), fill=YELLOW + (255,))
    img.alpha_composite(with_alpha(lay, a))


def draw_house(img, cx, cy, k, a=1.0):
    lay = layer()
    d = ImageDraw.Draw(lay)
    col = CHALK + (255,)
    walls = [(cx - 230, cy - 60), (cx - 230, cy + 170), (cx + 230, cy + 170), (cx + 230, cy - 60)]
    roof = [(cx - 290, cy - 40), (cx, cy - 260), (cx + 290, cy - 40)]
    chim = [(cx + 120, cy - 170), (cx + 120, cy - 250), (cx + 180, cy - 250), (cx + 180, cy - 125)]
    chalk_line(d, walls, col, 12, k * 1.5)
    chalk_line(d, roof, RED + (255,), 14, k * 1.6 - 0.25)
    chalk_line(d, chim, col, 10, k * 2 - 0.9)
    if k > 0.5:
        kk = ease((k - 0.5) / 0.35)
        door = [(cx - 50, cy + 170), (cx - 50, cy + 40), (cx + 50, cy + 40), (cx + 50, cy + 170)]
        chalk_line(d, door, YELLOW + (255,), 10, kk)
        for wx in (cx - 160, cx + 100):
            win = [(wx, cy - 10), (wx + 70, cy - 10), (wx + 70, cy + 60), (wx, cy + 60), (wx, cy - 10)]
            chalk_line(d, win, BLUE + (255,), 8, kk)
            if kk > 0.9:
                d.line([(wx + 35, cy - 10), (wx + 35, cy + 60)], fill=BLUE + (255,), width=5)
                d.line([(wx, cy + 25), (wx + 70, cy + 25)], fill=BLUE + (255,), width=5)
                d.rectangle((wx + 4, cy - 6, wx + 66, cy + 56), fill=YELLOW + (60,))
    if k > 0.85:
        d.ellipse((cx + 25, cy + 100, cx + 37, cy + 112), fill=YELLOW + (255,))
        # kalp
        hk = ease((k - 0.85) / 0.15)
        hs = 26 * hk
        hx, hy = cx, cy - 115
        d.ellipse((hx - hs, hy - hs * 0.6, hx, hy + hs * 0.3), fill=PINK + (255,))
        d.ellipse((hx, hy - hs * 0.6, hx + hs, hy + hs * 0.3), fill=PINK + (255,))
        d.polygon([(hx - hs * 0.98, hy), (hx + hs * 0.98, hy), (hx, hy + hs * 1.05)], fill=PINK + (255,))
    img.alpha_composite(with_alpha(lay, a))


def draw_calendar(img, cx, cy, s, sc_t, a=1.0):
    if s < 0.05:
        return
    lay = layer()
    d = ImageDraw.Draw(lay)
    w2, h2 = 190 * s, 210 * s
    d.rounded_rectangle((cx - w2, cy - h2, cx + w2, cy + h2), int(30 * s), fill=CHALK + (255,))
    d.rounded_rectangle((cx - w2, cy - h2, cx + w2, cy - h2 + 110 * s), int(30 * s), fill=RED + (255,))
    d.rectangle((cx - w2, cy - h2 + 70 * s, cx + w2, cy - h2 + 110 * s), fill=RED + (255,))
    for rx in (cx - 100 * s, cx + 100 * s):
        d.rounded_rectangle((rx - 14 * s, cy - h2 - 34 * s, rx + 14 * s, cy - h2 + 34 * s), int(12 * s), fill=(60, 60, 70, 255))
    img.alpha_composite(with_alpha(lay, a))
    text(img, "AY", "Inter-Black", int(56 * s), CHALK, cx, cy - h2 + 56 * s, a, chalky=False)
    # sayaç: 12 → 6
    n = int(round(lerp(12, 6, ease((sc_t - 0.5) / 1.1))))
    text(img, str(n), "InterDisplay-Black", int(250 * s), (34, 74, 58), cx, cy + 55 * s, a,
         scale=1 + 0.12 * math.sin(clamp((sc_t - 1.6) / 0.35) * math.pi), chalky=False)


def draw_ball(img, cx, cy, r, col, label, a=1.0):
    lay = layer()
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col + (255,))
    d.ellipse((cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55), fill=(255, 255, 255, 255))
    d.ellipse((cx - r * 0.75, cy - r * 0.8, cx - r * 0.35, cy - r * 0.45), fill=(255, 255, 255, 120))
    img.alpha_composite(with_alpha(lay, a))
    text(img, label, "Inter-Black", int(r * 0.6), (30, 30, 30), cx, cy + 2, a, chalky=False)


def underline(img, x0, x1, y, k, col=YELLOW, width=12):
    d = ImageDraw.Draw(img)
    pts = [(lerp(x0, x1, i / 20), y + 6 * math.sin(i * 0.9)) for i in range(21)]
    chalk_line(d, pts, col + (255,), width, k)


def badge(img, label, cx, cy, sc_t, col=RED, fg=CHALK, size=44, delay=0.0):
    k = back((sc_t - delay) / 0.45)
    if k <= 0:
        return
    spr = sprite(label, "Inter-Black", size, fg, chalky=False)
    w_, h_ = spr.width + 70, spr.height + 36
    bl = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    ImageDraw.Draw(bl).rounded_rectangle((0, 0, w_ - 1, h_ - 1), h_ // 2, fill=col + (255,))
    bl.alpha_composite(spr, (35, 18))
    put(img, bl, cx, cy, clamp(k), scale=k, rot=-3)


# ---------------------------------------------------------------- sahneler
def sc_hook(img, t, st):
    draw_dust(img, t)
    k1 = back((st - 0.1) / 0.5)
    text(img, "24", "InterDisplay-Black", 330, YELLOW, W / 2, 620, clamp(k1), scale=k1)
    text(img, "KASIM", "InterDisplay-Black", 150, CHALK, W / 2, 860, ease((st - 0.35) / 0.4),
         scale=lerp(1.25, 1, ease((st - 0.35) / 0.4)))
    underline(img, 270, 810, 960, ease((st - 0.7) / 0.6))
    a = ease((st - 1.0) / 0.45)
    text(img, "ÖĞRETMENLER", "Inter-Black", 100, CHALK, W / 2 + (1 - a) * -120, 1100, a)
    a = ease((st - 1.2) / 0.45)
    text(img, "GÜNÜ'NE ÖZEL", "Inter-Black", 100, CHALK, W / 2 + (1 - a) * 120, 1215, a)
    badge(img, "KAMPANYA", W / 2, 1380, st, delay=1.6, size=62)
    ak = ease((st - 0.6) / 0.5)
    draw_apple(img, 190, 400 + 8 * math.sin(t * 3), 60, ak)
    draw_pencil(img, 860, 1560, 360, 25 + 3 * math.sin(t * 2), ease((st - 1.4) / 0.5))
    if st > 1.6:
        draw_confetti(img, (st - 1.6) * 1.2, 0.9)


def sc_today(img, t, st):
    draw_dust(img, t)
    badge(img, "BUGÜN", W / 2, 620, st, col=YELLOW, fg=(34, 60, 45), size=90)
    a = ease((st - 0.4) / 0.4)
    text(img, "gelen tüm", "Inter-Bold", 96, CHALK, W / 2, 820 + (1 - a) * 40, a)
    a = ease((st - 0.6) / 0.4)
    text(img, "müşterilerimize", "Inter-Black", 106, CHALK, W / 2, 950 + (1 - a) * 40, a)
    k = back((st - 0.95) / 0.45)
    text(img, "ÖZEL", "InterDisplay-Black", 230, YELLOW, W / 2, 1160, clamp(k), scale=k, rot=-4 * clamp(k))
    underline(img, 330, 760, 1290, ease((st - 1.4) / 0.5), col=RED)
    # yıldızlar
    for i, (x, y) in enumerate([(170, 1120), (910, 1080), (220, 1340), (880, 1330)]):
        s = 26 * back((st - 1.2 - i * 0.1) / 0.4) * (0.85 + 0.15 * math.sin(t * 6 + i))
        if s > 0:
            d = ImageDraw.Draw(img)
            pts = []
            for j in range(10):
                r = s if j % 2 == 0 else s * 0.42
                an = -math.pi / 2 + j * math.pi / 5
                pts.append((x + r * math.cos(an), y + r * math.sin(an)))
            d.polygon(pts, fill=YELLOW + (255,))


def price_block(img, st, price_lbl, item_lbl, inst, icon_y, item_col):
    """Ortak fiyat düzeni: üstte '2 MİLYON TL araba için', altta taksit tutarı."""
    a = ease((st - 0.2) / 0.4)
    text(img, price_lbl, "InterDisplay-Black", 128, CHALK, W / 2 + (1 - a) * -100, 380, a)
    a = ease((st - 0.45) / 0.4)
    text(img, item_lbl, "Inter-Bold", 80, item_col, W / 2 + (1 - a) * 100, 500, a)
    # taksit kutusu
    k = back((st - 1.9) / 0.5)
    if k > 0:
        bw, bh = 860, 330
        box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        bd = ImageDraw.Draw(box)
        bd.rounded_rectangle((0, 0, bw - 1, bh - 1), 46, fill=(20, 45, 35, 235), outline=YELLOW + (255,), width=8)
        put(img, box, W / 2, 1270, clamp(k), scale=k)
        cnt = lerp(0, inst, ease((st - 2.2) / 1.0))
        bump = 1 + 0.1 * math.sin(clamp((st - 3.2) / 0.3) * math.pi)
        text(img, f"{tr_num(cnt)} TL", "InterDisplay-Black", 150, YELLOW, W / 2, 1235, clamp(k), scale=k * bump)
        text(img, "taksitle", "Inter-Bold", 64, CHALK, W / 2, 1365, ease((st - 2.6) / 0.4))


def sc_car(img, t, st):
    draw_dust(img, t)
    price_block(img, st, "2 MİLYON TL", "araba için", 20000, 850, BLUE)
    x = lerp(-450, W / 2, ease((st - 0.3) / 1.1))
    bob = 4 * math.sin(t * 18) if st < 1.4 else 0
    draw_car(img, x, 830 + bob, ease((st - 0.1) / 1.2), t)
    if st < 1.5:  # hız çizgileri
        d = ImageDraw.Draw(img)
        a = int(200 * (1 - ease((st - 0.9) / 0.6)))
        for i in range(4):
            y = 760 + i * 40
            d.line([(x - 340 - i * 30, y), (x - 520 - i * 30, y)], fill=CHALK + (a,), width=6)


def sc_house(img, t, st):
    draw_dust(img, t)
    price_block(img, st, "5 MİLYON TL", "ev için", 20833, 870, PINK)
    draw_house(img, W / 2, 900, ease((st - 0.15) / 1.5))
    # bacadan duman
    if st > 1.2:
        lay = layer()
        d = ImageDraw.Draw(lay)
        for i in range(4):
            p = ((st - 1.2) * 0.6 + i * 0.25) % 1
            y = 630 - p * 70
            x = W / 2 + 150 + 25 * math.sin(p * 6 + i)
            r = 12 + 18 * p
            d.ellipse((x - r, y - r, x + r, y + r), fill=(240, 240, 235, int(170 * (1 - p))))
        img.alpha_composite(lay)


def sc_delivery(img, t, st):
    draw_dust(img, t)
    a = ease((st - 0.1) / 0.4)
    text(img, "EN ERKEN", "Inter-Black", 96, CHALK, W / 2, 340 + (1 - a) * 40, a)
    k = back((st - 0.2) / 0.55)
    draw_calendar(img, W / 2, 750, clamp(k) * 1.0 + 0.0001, st, clamp(k))
    a = ease((st - 1.3) / 0.4)
    text(img, "6 AYDA", "InterDisplay-Black", 170, YELLOW, W / 2, 1110, a, scale=lerp(1.3, 1, a))
    a = ease((st - 1.6) / 0.4)
    text(img, "teslimat alma", "Inter-Bold", 86, CHALK, W / 2, 1250 + (1 - a) * 30, a)
    a = ease((st - 1.8) / 0.4)
    text(img, "şansını yakala!", "Inter-Black", 96, CHALK, W / 2, 1360 + (1 - a) * 30, a)
    underline(img, 270, 810, 1430, ease((st - 2.3) / 0.5), col=RED)
    # anahtar ikonu çevresinde parıltı
    for i in range(8):
        an = i * math.pi / 4 + t * 0.8
        r0, r1 = 255, 255 + 30 * (0.5 + 0.5 * math.sin(t * 5 + i))
        al = int(220 * ease((st - 1.0) / 0.4))
        if al > 0:
            ImageDraw.Draw(img).line([(W / 2 + r0 * math.cos(an), 750 + r0 * math.sin(an)),
                                      (W / 2 + r1 * math.cos(an), 750 + r1 * math.sin(an))],
                                     fill=YELLOW + (al,), width=8)


BALLS = [(RED, "24"), (YELLOW, "11"), (BLUE, "12"), (GREEN_L, "7"), (PINK, "3")]


def sc_draw(img, t, st):
    draw_dust(img, t)
    # kura küresi
    cx, cy, R = W / 2 - 60, 560, 210
    lay = layer()
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(255, 255, 255, 40), outline=CHALK + (255,), width=10)
    d.rectangle((cx - 40, cy + R - 5, cx + 40, cy + R + 60), fill=WOOD)
    d.rounded_rectangle((cx - 160, cy + R + 55, cx + 160, cy + R + 95), 16, fill=WOOD_D)
    gk = ease(st / 0.5)
    img.alpha_composite(with_alpha(lay, gk))
    spin = st * 3.2
    for i, (col, lb) in enumerate(BALLS):
        an = spin * (1 + 0.15 * i) + i * 1.3
        rr = 120 + 40 * math.sin(i * 2.1 + st)
        bx, by = cx + rr * math.cos(an), cy + rr * math.sin(an) * 0.85
        if i == 0 and st > 1.6:  # ilk top dışarı çıkıyor
            k = ease((st - 1.6) / 0.7)
            bx, by = lerp(bx, cx + R + 170, k), lerp(by, cy + 60, k)
            draw_ball(img, bx, by, lerp(62, 95, k), col, "24" if k < 0.9 else "★", gk)
        else:
            draw_ball(img, bx, by, 62, col, lb, gk)
    a = ease((st - 1.0) / 0.4)
    text(img, "İLK KURA", "InterDisplay-Black", 150, CHALK, W / 2, 1040 + (1 - a) * 40, a)
    k = back((st - 1.5) / 0.5)
    text(img, "ARALIK", "InterDisplay-Black", 190, YELLOW, W / 2, 1205, clamp(k), scale=k, rot=-3 * clamp(k))
    a = ease((st - 1.9) / 0.4)
    text(img, "ayında!", "Inter-Black", 100, CHALK, W / 2, 1345, a)
    badge(img, "HEMEN GEL, FIRSATI KAÇIRMA!", W / 2, 1490, st, col=RED, size=48, delay=2.6)
    if st > 1.8:
        draw_confetti(img, (st - 1.8) * 1.1)


SCENE_FN = {"hook": sc_hook, "today": sc_today, "car": sc_car, "house": sc_house,
            "delivery": sc_delivery, "draw": sc_draw}


def scene_at(t):
    for i in range(len(SCENES)):
        if t < starts[i] + SCENES[i][0] or i == len(SCENES) - 1:
            return i, t - starts[i]


def render_frame(n):
    t = n / FPS
    i, st = scene_at(t)
    dur, kind = SCENES[i]
    img = BG.copy()
    content = layer()
    SCENE_FN[kind](content, t, st)
    # sahne geçişi: içerik yukarı kayarak solar (son sahne hariç)
    if i < len(SCENES) - 1:
        k = ease((st - (dur - 0.3)) / 0.3)
        if k > 0:
            content = with_alpha(content, 1 - k)
            content = content.transform(content.size, Image.AFFINE, (1, 0, 0, 0, 1, 80 * k))
    img.alpha_composite(content)
    # ilerleme çubuğu
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((90, 110, W - 90, 120), 5, fill=(20, 45, 35, 255))
    d.rounded_rectangle((90, 110, 90 + (W - 180) * (t / TOTAL), 120), 5, fill=YELLOW + (255,))
    img = img.convert("RGB")
    if t < 0.25:
        img = Image.blend(Image.new("RGB", (W, H)), img, t / 0.25)
    if t > TOTAL - 0.5:
        img = Image.blend(Image.new("RGB", (W, H)), img, clamp((TOTAL - t) / 0.5))
    return img


# ---------------------------------------------------------------- ses
def make_audio(path, sr=44100):
    n = int(TOTAL * sr)
    tt = np.arange(n) / sr
    out = np.zeros(n)
    bpm = 118
    beat = 60 / bpm
    # akor döngüsü: C - G - Am - F (neşeli pop)
    chords = [[261.6, 329.6, 392.0], [196.0, 246.9, 293.7], [220.0, 261.6, 329.6], [174.6, 220.0, 261.6]]
    bass = [130.8, 98.0, 110.0, 87.3]
    bar = beat * 4
    r = np.random.default_rng(1)

    def add(t0, sig, gain):
        i0 = int(t0 * sr)
        if i0 >= n:
            return
        sig = sig[: n - i0]
        out[i0:i0 + len(sig)] += gain * sig

    nb = int(TOTAL / beat) + 1
    for b in range(nb):
        t0 = b * beat
        ch = chords[(b // 4) % 4]
        # kick
        L = int(0.25 * sr)
        lt = np.arange(L) / sr
        add(t0, np.sin(2 * np.pi * np.cumsum(55 + 110 * np.exp(-lt * 30)) / sr) * np.exp(-lt * 14), 0.5)
        # clap 2 ve 4
        if b % 2 == 1:
            L = int(0.15 * sr)
            lt = np.arange(L) / sr
            add(t0, r.normal(0, 1, L) * np.exp(-lt * 30), 0.12)
        # hi-hat sekizlik
        for h in (0, 0.5):
            L = int(0.04 * sr)
            lt = np.arange(L) / sr
            nz = r.normal(0, 1, L)
            nz = np.diff(np.concatenate([[0], nz]))
            add(t0 + h * beat, nz * np.exp(-lt * 90), 0.05)
        # bas
        L = int(beat * 0.9 * sr)
        lt = np.arange(L) / sr
        f = bass[(b // 4) % 4]
        add(t0, (np.sin(2 * np.pi * f * lt) + 0.3 * np.sin(4 * np.pi * f * lt)) * np.exp(-lt * 3), 0.22)
        # pluck arpej (onaltılık)
        for s in range(4):
            note = ch[(b * 4 + s) % 3] * (2 if s % 2 else 1)
            L = int(0.3 * sr)
            lt = np.arange(L) / sr
            sig = (np.sin(2 * np.pi * note * lt) + 0.4 * np.sin(4 * np.pi * note * lt)) * np.exp(-lt * 12)
            add(t0 + s * beat / 4, sig, 0.07)
    # pad
    for k in range(int(TOTAL / bar) + 1):
        a, b_ = int(k * bar * sr), min(n, int((k + 1) * bar * sr))
        if a >= n:
            break
        loc = tt[a:b_] - k * bar
        env = np.minimum(1, loc / 0.3) * np.minimum(1, (bar - loc) / 0.3)
        for f in chords[k % 4]:
            out[a:b_] += 0.025 * env * np.sin(2 * np.pi * f * loc)

    # efektler: geçişlerde whoosh, fiyat/rakam belirişinde 'ding'
    def whoosh(t0):
        L = int(0.4 * sr)
        lt = np.arange(L) / sr
        nz = r.normal(0, 1, L)
        env = np.sin(np.pi * lt / 0.4) ** 2
        lp = np.convolve(nz, np.ones(12) / 12, mode="same")
        add(t0, lp * env, 0.5)

    def ding(t0, f=1318.5):
        L = int(0.8 * sr)
        lt = np.arange(L) / sr
        sig = (np.sin(2 * np.pi * f * lt) + 0.5 * np.sin(2 * np.pi * f * 2.01 * lt)) * np.exp(-lt * 5)
        add(t0, sig, 0.18)

    for i in range(1, len(SCENES)):
        whoosh(starts[i] - 0.25)
    ding(starts[0] + 0.2)
    ding(starts[0] + 1.7, 1568)
    ding(starts[1] + 1.0, 1568)
    for i in (2, 3):
        ding(starts[i] + 3.2, 1760)  # taksit tutarı netleşince
    ding(starts[4] + 1.6, 1568)
    ding(starts[5] + 1.5, 1760)
    ding(starts[5] + 1.65, 2093)

    fade = np.minimum(1, tt / 0.3) * np.minimum(1, (TOTAL - tt) / 1.0)
    out = out * fade
    out = np.tanh(out * 1.4) / np.tanh(1.4)
    out = out / max(1e-6, np.abs(out).max()) * 0.85
    if VOICES:
        voice = np.zeros(n)
        for i, vp in VOICES.items():
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(vp), "-ac", "1", "-ar", str(sr),
                                  "-f", "f32le", "-"], capture_output=True, check=True).stdout
            v = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
            i0 = int((starts[i] + VOICE_DELAY) * sr)
            v = v[: max(0, n - i0)]
            voice[i0:i0 + len(v)] += v
        voice /= max(1e-6, np.abs(voice).max())
        # müziği konuşma sırasında kıs (ducking)
        win = int(0.3 * sr)
        env = np.convolve(np.abs(voice), np.ones(win) / win, mode="same")
        duck = 1 - 0.65 * np.clip(env * 12, 0, 1)
        out = out * 0.5 * duck + voice * 0.95
        out = np.clip(out, -1, 1)
    pcm = (out * 32767).astype(np.int16)
    st = np.stack([pcm, pcm], axis=1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(st.tobytes())


def main():
    wav = OUT.with_suffix(".wav")
    make_audio(wav)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(OUT)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(NFRAMES):
        p.stdin.write(render_frame(n).tobytes())
        if n % 150 == 0:
            print(f"kare {n}/{NFRAMES}", flush=True)
    p.stdin.close()
    p.wait()
    wav.unlink(missing_ok=True)
    print("hazır:", OUT, f"({TOTAL:.1f} sn)")


if __name__ == "__main__":
    if "--preview" in sys.argv:
        outdir = Path(ARGS[0]) if ARGS else Path(".")
        outdir.mkdir(parents=True, exist_ok=True)
        for i, (dur, kind) in enumerate(SCENES):
            sec = starts[i] + dur - 0.45
            render_frame(int(sec * FPS)).resize((540, 960)).save(outdir / f"prev_{i}_{kind}.png")
        print("önizleme:", outdir)
    else:
        main()
