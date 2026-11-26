#!/usr/bin/env python3
"""Kasım fırsatları — son 2 gün! 4 adımlı dikey reels (1080x1920, 30 fps).

Kare kare PIL ile çizer, numpy ile müzik üretir, voice/<n>.mp3 dış seslerini
miksler ve ffmpeg ile MP4'e çevirir. Sahne süreleri sese göre uzar.

Kullanım:  python3 make_firsat_reel.py [çıktı.mp4]
           python3 make_firsat_reel.py --still 3.5 12 ...   (test kareleri)
"""
import math
import random
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
HERE = Path(__file__).resolve().parent
OUT = HERE / "kasim_firsatlari_4_adim_reel.mp4"
if len(sys.argv) > 1 and sys.argv[1].endswith(".mp4"):
    OUT = Path(sys.argv[1])

# Sahnedeki telefon / marka satırı (boş bırakılırsa gösterilmez)
ILETISIM = ""

FD = "/usr/share/fonts/opentype/inter/"
def F(name, size):
    return ImageFont.truetype(FD + name, size)

F_BLACK = lambda s: F("InterDisplay-Black.otf", s)
F_BOLD = lambda s: F("InterDisplay-Bold.otf", s)
F_SEMI = lambda s: F("Inter-SemiBold.otf", s)
F_MED = lambda s: F("Inter-Medium.otf", s)

NAVY = (6, 26, 48)
DEEP = (8, 58, 86)
TURQ = (38, 208, 206)
SKY = (120, 220, 255)
SUN = (255, 158, 64)
CORAL = (255, 107, 94)
SAND = (255, 222, 160)
WHITE = (255, 255, 255)
MUTED = (170, 200, 220)
CARD = (255, 255, 255)


# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = clamp(x)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def back_out(x):
    x = clamp(x)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def prog(t, start, dur):
    return clamp((t - start) / dur)


# ------------------------------------------------------------------ çizim
_tcache = {}


def text_layer(s, font, fill):
    key = (s, font.path, font.size, fill)
    if key not in _tcache:
        l, t, r, b = font.getbbox(s)
        img = Image.new("RGBA", (r - l + 4, b - t + 4), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((2 - l, 2 - t), s, font=font, fill=fill + (255,))
        _tcache[key] = img
    return _tcache[key]


def put(base, layer, x, y, anchor="mm", alpha=1.0, scale=1.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    if scale != 1.0:
        layer = layer.resize((max(1, int(layer.width * scale)),
                              max(1, int(layer.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        layer = layer.copy()
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    w, h = layer.size
    ax, ay = anchor
    px = x - (w // 2 if ax == "m" else w if ax == "r" else 0)
    py = y - (h // 2 if ay == "m" else h if ay == "b" else 0)
    px, py = int(px), int(py)
    cx0, cy0 = max(0, -px), max(0, -py)
    cx1, cy1 = min(w, W - px), min(h, H - py)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    if (cx0, cy0, cx1, cy1) != (0, 0, w, h):
        layer = layer.crop((cx0, cy0, cx1, cy1))
    base.alpha_composite(layer, dest=(px + cx0, py + cy0))


def text(base, s, x, y, font, fill=WHITE, anchor="mm", alpha=1.0, scale=1.0):
    put(base, text_layer(s, font, fill), x, y, anchor, alpha, scale)


def rrect(base, box, r, fill, alpha=1.0, outline=None, width=0):
    x0, y0, x1, y1 = [int(v) for v in box]
    if x1 - x0 < 1 or y1 - y0 < 1 or alpha <= 0.01:
        return
    layer = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    a = int(255 * alpha)
    ImageDraw.Draw(layer).rounded_rectangle(
        (0, 0, x1 - x0 - 1, y1 - y0 - 1), radius=min(r, (y1 - y0) // 2, (x1 - x0) // 2),
        fill=fill + (a,) if fill else None,
        outline=outline + (a,) if outline else None, width=width)
    put(base, layer, x0, y0, "lt")


def card(base, cx, cy, w, h, r, fill, alpha, scale=1.0, outline=None, width=0):
    w, h = w * scale, h * scale
    rrect(base, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), r, fill, alpha, outline, width)


# ------------------------------------------------------------------ ikonlar
def icon_layer(kind, size=220, col=WHITE, acc=SUN):
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c, a = col + (255,), acc + (255,)
    n = NAVY + (255,)
    if kind == "ev":
        d.polygon([(s * .12, s * .48), (s * .5, s * .14), (s * .88, s * .48)], fill=a)
        d.rectangle((s * .22, s * .46, s * .78, s * .86), fill=c)
        d.rectangle((s * .44, s * .62, s * .56, s * .86), fill=a)
        d.rectangle((s * .29, s * .55, s * .39, s * .65), fill=n)
        d.rectangle((s * .61, s * .55, s * .71, s * .65), fill=n)
        d.rectangle((s * .66, s * .2, s * .74, s * .36), fill=c)
    elif kind == "araba":
        d.polygon([(s * .27, s * .52), (s * .36, s * .32), (s * .66, s * .32), (s * .77, s * .52)], fill=c)
        d.polygon([(s * .34, s * .5), (s * .4, s * .37), (s * .49, s * .37), (s * .49, s * .5)], fill=n)
        d.polygon([(s * .53, s * .5), (s * .53, s * .37), (s * .63, s * .37), (s * .70, s * .5)], fill=n)
        d.rounded_rectangle((s * .1, s * .5, s * .9, s * .72), radius=int(s * .07), fill=a)
        for wx in (.28, .72):
            d.ellipse((s * (wx - .1), s * .62, s * (wx + .1), s * .82), fill=c)
            d.ellipse((s * (wx - .045), s * .675, s * (wx + .045), s * .765), fill=n)
        d.rectangle((s * .82, s * .55, s * .88, s * .6), fill=SAND + (255,))
    elif kind == "dukkan":
        d.rectangle((s * .16, s * .46, s * .84, s * .86), fill=c)
        stripes = 6
        sw = s * .76 / stripes
        for i in range(stripes):
            x0 = s * .12 + i * sw
            colr = a if i % 2 == 0 else c
            d.rectangle((x0, s * .22, x0 + sw, s * .4), fill=colr)
            d.ellipse((x0, s * .32, x0 + sw, s * .32 + sw), fill=colr)
        d.rectangle((s * .12, s * .16, s * .88, s * .24), fill=a)
        d.rectangle((s * .24, s * .56, s * .5, s * .74), fill=SKY + (255,))
        d.rectangle((s * .58, s * .56, s * .74, s * .86), fill=a)
    return img


ICONS = {k: icon_layer(k) for k in ("ev", "araba", "dukkan")}


# ------------------------------------------------------------------ arka plan
def make_bg():
    y = np.linspace(0, 1, H)[:, None]
    x = np.linspace(0, 1, W)[None, :]
    top, bot = np.array(NAVY, float), np.array(DEEP, float)
    g = top + (bot - top) * (y ** 1.3)[..., None]
    d = np.sqrt((x - 0.85) ** 2 + ((y - 0.08) * 1.6) ** 2)
    glow = np.clip(1 - d / 0.55, 0, 1) ** 2.2
    g = g + glow[..., None] * np.array([90, 50, 10], float) * 0.55
    g = np.broadcast_to(g, (H, W, 3))
    return Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert("RGBA")


BG = make_bg()


def waves(base, t):
    layer = Image.new("RGBA", (W, 360), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(5):
        amp = 18 + i * 6
        yb = 90 + i * 55
        ph = t * (0.9 + i * 0.25) + i * 1.3
        pts = [(x, yb + amp * math.sin(x / (150 + i * 30) + ph)) for x in range(0, W + 20, 20)]
        pts += [(W, 360), (0, 360)]
        d.polygon(pts, fill=(TURQ if i % 2 == 0 else SKY) + (int(18 + i * 9),))
    base.alpha_composite(layer, dest=(0, H - 360))


# ------------------------------------------------------------------ zamanlama
# (ad, asgari süre). voice/<sıra>.mp3 varsa süre sese göre uzar.
BASE = [("hook", 5.0), ("adim1", 7.0), ("adim2", 7.0), ("adim3", 8.0),
        ("adim4", 8.0), ("bonus", 7.0), ("cta", 6.0)]
VOICE_DIR = HERE / "voice"
VOICE_DELAY = 0.4
VOICE_TAIL = 0.8


def clip_len(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())


VOICES = {}
for _i in range(len(BASE)):
    _f = VOICE_DIR / f"{_i}.mp3"
    if _f.exists():
        VOICES[_i] = (_f, clip_len(_f))

S, _t = {}, 0.0
for _i, (_name, _d) in enumerate(BASE):
    if _i in VOICES:
        _d = max(_d, VOICE_DELAY + VOICES[_i][1] + VOICE_TAIL)
    if _i == len(BASE) - 1:
        _d += 1.5
    S[_name] = (round(_t, 3), round(_t + _d, 3))
    _t += _d
DUR = round(_t, 3)
CUTS = [v[0] for v in S.values()][1:]

# Dış ses içindeki vurgu anları (sahne başından itibaren sn, ses gecikmesi dahil).
# silencedetect ile bulunan duraklamalara göre ayarlandı.
CUE = {
    "adim1": [4.1, 5.0, 6.2],        # on bin / otuz bin / elli bin
    "adim2": [4.9, 5.6, 6.7],        # ev / araba / dükkan
    "adim3": [3.1, 4.1, 5.35, 6.6],   # peşinatlı / peşinatsız / çekiliş / kurasız
    "adim4": [3.6, 5.7, 7.0],        # %50 peşin / %50 taksit / taksit kutuları
}


def scene_alpha(t, name, fade=0.35):
    a, b = S[name]
    if t < a or t > b:
        return 0.0
    fin = 1.0 if a == 0 else clamp((t - a) / fade)
    fout = 1.0 if b >= DUR else clamp((b - t) / fade)
    return min(fin, fout)


# ------------------------------------------------------------------ ortak öğeler
def header(img, A):
    text(img, "KASIM FIRSATLARI", W // 2, 240, F_BOLD(40), SUN, alpha=A)
    text(img, "son 2 gün", W // 2, 290, F_SEMI(30), MUTED, alpha=A)


def stepper(img, cur, t, t0, A):
    """Üstte 1-2-3-4 adım göstergesi. cur: aktif adım (1..4), 5 = hepsi tamam."""
    xs = [W / 2 - 270 + i * 180 for i in range(4)]
    y = 375
    for i in range(3):
        done = (i + 1) < cur
        rrect(img, (xs[i] + 34, y - 4, xs[i + 1] - 34, y + 4), 4,
              TURQ if done else (255, 255, 255), A * (0.9 if done else 0.18))
    for i, x in enumerate(xs):
        n = i + 1
        if n < cur:
            card(img, x, y, 64, 64, 32, TURQ, A)
            text(img, "✓", x, y, F_BLACK(34), NAVY, alpha=A)
        elif n == cur:
            p = back_out(prog(t, t0 + 0.1, 0.5))
            pulse = 1 + 0.06 * math.sin((t - t0) * 6)
            card(img, x, y, 84, 84, 42, SUN, A * 0.25, scale=max(0.01, p * pulse))
            card(img, x, y, 64, 64, 32, SUN, A, scale=max(0.01, p))
            text(img, str(n), x, y, F_BLACK(34), NAVY, alpha=A * clamp(p))
        else:
            card(img, x, y, 64, 64, 32, None, A * 0.5, outline=MUTED, width=3)
            text(img, str(n), x, y, F_BOLD(32), MUTED, alpha=A * 0.6)


def step_title(img, n, l1, l2, t, t0, A):
    p = ease_out(prog(t, t0 + 0.15, 0.5))
    text(img, f"{n}. ADIM", W // 2, 500 - 20 * (1 - p), F_BOLD(46), TURQ, alpha=A * p)
    p2 = ease_out(prog(t, t0 + 0.4, 0.5))
    text(img, l1, W // 2, 590 - 25 * (1 - p2), F_BLACK(80), WHITE, alpha=A * p2)
    text(img, l2, W // 2, 685 - 25 * (1 - p2), F_BLACK(80), WHITE, alpha=A * p2)


# ------------------------------------------------------------------ sahneler
def sc_hook(img, t, A):
    t0 = S["hook"][0]
    p = back_out(prog(t, t0 + 0.1, 0.6))
    text(img, "KASIM", W // 2, 520, F_BLACK(170), WHITE, alpha=A * clamp(p),
         scale=max(0.01, 0.7 + 0.3 * p))
    p2 = back_out(prog(t, t0 + 0.45, 0.6))
    text(img, "FIRSATLARI", W // 2, 690, F_BLACK(140), SUN, alpha=A * clamp(p2),
         scale=max(0.01, 0.7 + 0.3 * p2))
    p3 = back_out(prog(t, t0 + 1.1, 0.6))
    pulse = 1 + 0.04 * math.sin((t - t0) * 8) * clamp(p3)
    sc = max(0.01, p3 * pulse)
    card(img, W / 2, 905, 760, 170, 85, CORAL, A * clamp(p3), scale=sc)
    text(img, "SON 2 GÜN!", W // 2, 905, F_BLACK(104), WHITE, alpha=A * clamp(p3), scale=sc)
    # takvim yaprakları
    p4 = ease_out(prog(t, t0 + 1.6, 0.6))
    text(img, "bitmesine", W // 2, 1040, F_SEMI(44), MUTED, alpha=A * p4)
    p5 = ease_out(prog(t, t0 + 2.6, 0.5))
    text(img, "4 ADIMDA PLANINI YAP", W // 2, 1200, F_BLACK(64), WHITE, alpha=A * p5)
    for i in range(4):
        q = back_out(prog(t, t0 + 2.9 + i * 0.18, 0.45))
        x = W / 2 - 270 + i * 180
        card(img, x, 1340, 100, 100, 50, [TURQ, SKY, SUN, CORAL][i], A * clamp(q), scale=max(0.01, q))
        text(img, str(i + 1), x, 1340, F_BLACK(54), NAVY, alpha=A * clamp(q), scale=max(0.01, q))
        if i < 3:
            text(img, "›", x + 90, 1336, F_BLACK(60), MUTED, alpha=A * clamp(q))


def sc_adim1(img, t, A):
    t0 = S["adim1"][0]
    header(img, A)
    stepper(img, 1, t, t0, A)
    step_title(img, 1, "Aylık ödeme", "gücünü belirle", t, t0, A)
    opts = [("10.000 ₺", 10), ("30.000 ₺", 30), ("50.000 ₺", 50)]
    cues = CUE["adim1"]
    for i, (lab, v) in enumerate(opts):
        y = 880 + i * 200
        p = back_out(prog(t, t0 + 1.0 + i * 0.2, 0.5))
        hl = ease_out(prog(t, t0 + cues[i], 0.3))
        # vurgu sonraki seçeneğe geçince hafifçe sön
        if i < 2:
            hl *= 1 - 0.6 * ease_out(prog(t, t0 + cues[i + 1], 0.3))
        sc = max(0.01, clamp(p) * (1 + 0.05 * hl))
        a = A * clamp(p)
        card(img, W / 2, y, 800, 160, 40, CARD, a * (0.08 + 0.12 * hl), scale=sc)
        card(img, W / 2, y, 800, 160, 40, None, a * hl, scale=sc, outline=SUN, width=5)
        text(img, lab, 170, y - 18, F_BLACK(68), SUN if hl > 0.3 else WHITE, "lm", a)
        text(img, "/ ay", 510, y - 10, F_SEMI(36), MUTED, "lm", a)
        bw = 330 * (v / 50) * ease_out(prog(t, t0 + 1.4 + i * 0.2, 0.8))
        rrect(img, (170, y + 38, 500, y + 52), 7, (255, 255, 255), a * 0.12)
        rrect(img, (170, y + 38, 170 + bw, y + 52), 7, [TURQ, SKY, SUN][i], a)
        q = back_out(prog(t, t0 + cues[i], 0.4))
        text(img, "mi?", 910, y, F_BLACK(60), WHITE, "rm", a * clamp(q),
             scale=max(0.01, 0.6 + 0.4 * q))
    p = ease_out(prog(t, t0 + cues[2] + 1.2, 0.5))
    text(img, "Bütçene uygun planla başla", W // 2, 1520, F_BOLD(44), SAND, alpha=A * p)


def sc_adim2(img, t, A):
    t0 = S["adim2"][0]
    header(img, A)
    stepper(img, 2, t, t0, A)
    step_title(img, 2, "Kısa ve uzun vadede", "ihtiyacını belirle", t, t0, A)
    # vade anahtarı
    p = ease_out(prog(t, t0 + 1.0, 0.5))
    tw = 700
    card(img, W / 2, 850, tw, 110, 55, CARD, A * 0.1 * p)
    ph = (max(0.0, t - t0 - 1.6) % 3.0)
    k = ease_io((ph - 1.2) / 0.3) if ph < 2.7 else 1 - ease_io((ph - 2.7) / 0.3)
    kx = W / 2 - tw / 4 + k * tw / 2
    card(img, kx, 850, tw / 2 - 14, 86, 43, TURQ, A * p)
    text(img, "KISA VADE", W / 2 - tw / 4, 850, F_BOLD(38), NAVY if k < 0.5 else WHITE, alpha=A * p)
    text(img, "UZUN VADE", W / 2 + tw / 4, 850, F_BOLD(38), NAVY if k >= 0.5 else WHITE, alpha=A * p)
    items = [("ev", "EV"), ("araba", "ARABA"), ("dukkan", "DÜKKAN")]
    cues = CUE["adim2"]
    for i, (ic, lab) in enumerate(items):
        x = W / 2 - 320 + i * 320
        q = back_out(prog(t, t0 + cues[i] - 0.15, 0.55))
        a = A * clamp(q)
        sc = max(0.01, q)
        bob = 8 * math.sin((t - t0) * 3 + i) * clamp(q)
        card(img, x, 1160 + bob, 280, 360, 44, CARD, a * 0.1, scale=sc)
        put(img, ICONS[ic], x, 1120 + bob, "mm", a, scale=sc)
        text(img, lab, x, 1290 + bob, F_BLACK(46), WHITE, alpha=a, scale=sc)
        if i < 2:
            text(img, "mi?", x, 1365 + bob, F_SEMI(32), SAND, alpha=a)
        else:
            text(img, "mı?", x, 1365 + bob, F_SEMI(32), SAND, alpha=a)
    p = ease_out(prog(t, t0 + cues[2] + 1.0, 0.5))
    text(img, "Hayalindeki hedefi seç", W // 2, 1520, F_BOLD(44), SAND, alpha=A * p)


def choice_row(img, t, t0, A, y, label, left, right, c_left, c_right):
    p = ease_out(prog(t, t0 + c_left - 0.4, 0.4))
    text(img, label, W // 2, y - 120, F_SEMI(36), MUTED, alpha=A * p)
    for j, (lines, cue, col) in enumerate([(left, c_left, TURQ), (right, c_right, SUN)]):
        x = W / 2 - 235 + j * 470
        q = back_out(prog(t, t0 + cue - 0.1, 0.5))
        a = A * clamp(q)
        sc = max(0.01, q)
        card(img, x, y, 360, 170, 40, col, a, scale=sc)
        if len(lines) == 1:
            text(img, lines[0], x, y, F_BLACK(46), NAVY, alpha=a, scale=sc)
        else:
            text(img, lines[0], x, y - 28 * sc, F_BLACK(40), NAVY, alpha=a, scale=sc)
            text(img, lines[1], x, y + 26 * sc, F_BLACK(40), NAVY, alpha=a, scale=sc)
    q = ease_out(prog(t, t0 + c_right - 0.1, 0.4))
    text(img, "ya da", W // 2, y, F_BOLD(30), MUTED, alpha=A * q)


def sc_adim3(img, t, A):
    t0 = S["adim3"][0]
    header(img, A)
    stepper(img, 3, t, t0, A)
    step_title(img, 3, "Ödeme planını", "seç", t, t0, A)
    c = CUE["adim3"]
    choice_row(img, t, t0, A, 970, "PEŞİNAT", ["PEŞİNATLI"], ["PEŞİNATSIZ"], c[0], c[1])
    choice_row(img, t, t0, A, 1310, "TESLİMAT", ["ÇEKİLİŞLİ"], ["KURASIZ KESİN", "TESLİMAT"], c[2], c[3])
    p = ease_out(prog(t, t0 + c[3] + 1.2, 0.5))
    text(img, "Sana uygun planı birlikte seçelim", W // 2, 1530, F_BOLD(42), SAND, alpha=A * p)


def sc_adim4(img, t, A):
    t0 = S["adim4"][0]
    header(img, A)
    stepper(img, 4, t, t0, A)
    step_title(img, 4, "Ödemeni", "ayarla", t, t0, A)
    c = CUE["adim4"]
    cx, cy, R, ring = W / 2, 1010, 190, 64
    p0 = ease_out(prog(t, t0 + 1.0, 0.4))
    text(img, "KATILIM BEDELİ", cx, 775, F_BOLD(40), MUTED, alpha=A * p0)
    layer = Image.new("RGBA", (2 * R + 4, 2 * R + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    box = (2, 2, 2 * R + 2, 2 * R + 2)
    d.ellipse(box, outline=(255, 255, 255, int(40 * p0)), width=ring)
    pa = ease_io(prog(t, t0 + c[0] - 0.3, 0.9))
    pb = ease_io(prog(t, t0 + c[1] - 0.3, 0.9))
    if pa > 0:
        d.arc(box, 90, 90 + 180 * pa, fill=SUN + (255,), width=ring)
    if pb > 0:
        d.arc(box, 270, 270 + 180 * pb, fill=TURQ + (255,), width=ring)
    put(img, layer, cx, cy, "mm", A)
    text(img, "%50", cx, cy - 30, F_BLACK(90), SUN if pb < 0.5 else WHITE, alpha=A * clamp(pa * 2))
    text(img, "+ %50", cx, cy + 50, F_BLACK(56), TURQ, alpha=A * clamp(pb * 2))
    qa = back_out(prog(t, t0 + c[0], 0.5))
    card(img, 215, 1300, 350, 110, 30, SUN, A * clamp(qa), scale=max(0.01, qa))
    text(img, "%50 PEŞİN", 215, 1300, F_BLACK(44), NAVY, alpha=A * clamp(qa), scale=max(0.01, qa))
    qb = back_out(prog(t, t0 + c[1], 0.5))
    card(img, 770, 1300, 520, 110, 30, TURQ, A * clamp(qb), scale=max(0.01, qb))
    text(img, "%50 TAKSİTLERLE", 770, 1300, F_BLACK(44), NAVY, alpha=A * clamp(qb),
         scale=max(0.01, qb))
    # taksit kutuları: her taksitin üstüne katılım payı biner
    for i in range(8):
        x = 150 + i * 111
        q = ease_out(prog(t, t0 + c[2] - 0.6 + i * 0.12, 0.4))
        rrect(img, (x - 44, 1420, x + 44, 1520), 14, (255, 255, 255), A * 0.12 * q)
        h = 34 * q
        rrect(img, (x - 44, 1420, x + 44, 1420 + h), 10, TURQ, A * q)
        text(img, f"{i + 1}", x, 1485, F_BOLD(30), WHITE, alpha=A * q)
    p = ease_out(prog(t, t0 + c[2] + 0.4, 0.5))
    text(img, "kalan yarısı taksitlerine eklenir", W // 2, 1580, F_SEMI(36), SAND, alpha=A * p)


_rng = random.Random(3)
CONFETTI = [(_rng.uniform(0, W), _rng.uniform(-400, 0), _rng.uniform(140, 320),
             _rng.uniform(0, 6.28), _rng.choice([TURQ, SKY, SUN, CORAL, SAND]),
             _rng.uniform(10, 20)) for _ in range(90)]


def sc_bonus(img, t, A):
    t0 = S["bonus"][0]
    lt = t - t0
    # dönen ışınlar
    layer = Image.new("RGBA", (1400, 1400), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for k in range(16):
        a0 = k * (2 * math.pi / 16) + lt * 0.3
        pts = [(700, 700), (700 + 900 * math.cos(a0), 700 + 900 * math.sin(a0)),
               (700 + 900 * math.cos(a0 + 0.12), 700 + 900 * math.sin(a0 + 0.12))]
        d.polygon(pts, fill=SUN + (22,))
    put(img, layer, W / 2, 900, "mm", A * ease_out(prog(t, t0, 0.6)))
    # konfeti (yazıların arkasında)
    if lt > 5.8:
        ct = lt - 5.8
        d2 = ImageDraw.Draw(img)
        for (x, y, v, ph, col, sz) in CONFETTI:
            yy = y + v * ct * 2.2 + 300
            xx = x + 30 * math.sin(ct * 3 + ph)
            if 0 < yy < H - 200:
                w = sz * abs(math.cos(ct * 5 + ph))
                d2.rectangle((xx - w / 2, yy - sz / 3, xx + w / 2, yy + sz / 3),
                             fill=col + (int(230 * A),))
    header(img, A)
    stepper(img, 5, t, t0, A)
    p = back_out(prog(t, t0 + 0.2, 0.6))
    card(img, W / 2, 560, 440, 140, 70, SUN, A * clamp(p), scale=max(0.01, p))
    text(img, "BONUS", W // 2, 560, F_BLACK(84), NAVY, alpha=A * clamp(p), scale=max(0.01, p))
    p2 = ease_out(prog(t, t0 + 1.7, 0.5))
    text(img, "Cumartesi gününe kadar", W // 2, 730, F_BOLD(52), WHITE, alpha=A * p2)
    text(img, "gelen tüm müşterilerimize", W // 2, 800, F_BOLD(52), WHITE, alpha=A * p2)
    p3 = back_out(prog(t, t0 + 4.5, 0.6))
    sc = max(0.01, 0.6 + 0.4 * p3)
    card(img, W / 2, 1010, 900, 300, 50, CARD, A * 0.1 * clamp(p3), scale=sc)
    text(img, "REHİN / İPOTEK", W // 2, 950, F_BLACK(92), SUN, alpha=A * clamp(p3), scale=sc)
    text(img, "MASRAFLARI", W // 2, 1060, F_BLACK(92), WHITE, alpha=A * clamp(p3), scale=sc)
    p4 = back_out(prog(t, t0 + 5.8, 0.6))
    pulse = 1 + 0.05 * math.sin(lt * 7) * clamp(p4)
    sc4 = max(0.01, p4 * pulse)
    card(img, W / 2, 1290, 620, 170, 85, CORAL, A * clamp(p4), scale=sc4)
    text(img, "BİZDEN!", W // 2, 1290, F_BLACK(110), WHITE, alpha=A * clamp(p4), scale=sc4)



def sc_cta(img, t, A):
    t0 = S["cta"][0]
    lt = t - t0
    header(img, A)
    p = ease_out(prog(t, t0 + 0.1, 0.5))
    text(img, "Fırsatlar için", W // 2, 560, F_BOLD(60), SAND, alpha=A * p)
    p2 = back_out(prog(t, t0 + 0.5, 0.6))
    text(img, "İLETİŞİME", W // 2, 700, F_BLACK(140), WHITE, alpha=A * clamp(p2),
         scale=max(0.01, 0.7 + 0.3 * p2))
    text(img, "GEÇ!", W // 2, 850, F_BLACK(140), SUN, alpha=A * clamp(p2),
         scale=max(0.01, 0.7 + 0.3 * p2))
    p3 = ease_out(prog(t, t0 + 1.6, 0.5))
    text(img, "Ödeme planını", W // 2, 1010, F_BOLD(54), WHITE, alpha=A * p3)
    text(img, "beraber belirleyelim", W // 2, 1080, F_BOLD(54), WHITE, alpha=A * p3)
    p4 = back_out(prog(t, t0 + 2.6, 0.6))
    pulse = 1 + 0.04 * math.sin(lt * 6) * clamp(p4)
    sc = max(0.01, p4 * pulse)
    # buton halkası
    ring = (lt * 0.8) % 1.0
    card(img, W / 2, 1260, 700 + 120 * ring, 150 + 60 * ring, 105, None,
         A * clamp(p4) * (1 - ring) * 0.8, outline=TURQ, width=4)
    card(img, W / 2, 1260, 700, 150, 75, TURQ, A * clamp(p4), scale=sc)
    text(img, "HEMEN BİZE ULAŞ", W // 2, 1260, F_BLACK(58), NAVY, alpha=A * clamp(p4), scale=sc)
    if ILETISIM:
        text(img, ILETISIM, W // 2, 1400, F_BOLD(50), WHITE, alpha=A * clamp(p4))
    p5 = ease_out(prog(t, t0 + 3.2, 0.5))
    card(img, W / 2, 1520, 560, 90, 45, CORAL, A * p5)
    text(img, "KASIM FIRSATLARINA SON 2 GÜN", W // 2, 1520, F_BOLD(34), WHITE, alpha=A * p5)


SCENES = [("hook", sc_hook), ("adim1", sc_adim1), ("adim2", sc_adim2), ("adim3", sc_adim3),
          ("adim4", sc_adim4), ("bonus", sc_bonus), ("cta", sc_cta)]


def frame(t):
    img = BG.copy()
    waves(img, t)
    for name, fn in SCENES:
        A = scene_alpha(t, name)
        if A > 0:
            fn(img, t, A)
    for i, (name, _) in enumerate(SCENES):
        a, b = S[name]
        x = W / 2 - 3.5 * 80 + i * 80
        rrect(img, (x, 1690, x + 68, 1698), 4, (255, 255, 255), 0.18)
        f = clamp((t - a) / (b - a))
        if f > 0:
            rrect(img, (x, 1690, x + 68 * f, 1698), 4, TURQ, 0.9)
    return img.convert("RGB")


# ------------------------------------------------------------------ ses
SR = 44100


def make_audio(path):
    n = int(DUR * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    beat = 60 / 120
    # C - G - Am - F (pozitif, kampanya havası)
    chords = [[261.63, 329.63, 392.0], [196.0, 246.94, 293.66],
              [220.0, 261.63, 329.63], [174.61, 220.0, 261.63]]
    bars = int(DUR / (beat * 4)) + 1
    for b in range(bars):
        ch = chords[b % 4]
        s0 = b * 4 * beat
        i0, i1 = int(s0 * SR), min(n, int((s0 + 4 * beat) * SR))
        if i0 >= n:
            break
        seg = tt[i0:i1] - s0
        env = np.minimum(1, seg / 0.2) * np.exp(-seg * 0.4)
        pad = sum(np.sin(2 * np.pi * f * seg) + 0.3 * np.sin(4 * np.pi * f * seg) for f in ch)
        out[i0:i1] += 0.035 * pad * env
        for k in range(8):
            bs = s0 + k * beat / 2
            j0, j1 = int(bs * SR), min(n, int((bs + beat / 2) * SR))
            if j0 >= n:
                break
            sg = tt[j0:j1] - bs
            out[j0:j1] += 0.06 * np.sign(np.sin(2 * np.pi * ch[0] / 2 * sg)) * np.exp(-sg * 9)
            # arpej
            f = ch[k % 3] * 2
            out[j0:j1] += 0.03 * np.sin(2 * np.pi * f * sg) * np.exp(-sg * 12)
    rng = np.random.default_rng(11)
    nb = int(DUR / beat) + 1
    for k in range(nb):
        s = k * beat
        i0, i1 = int(s * SR), min(n, int((s + 0.35) * SR))
        if i0 >= n:
            break
        sg = tt[i0:i1] - s
        out[i0:i1] += 0.45 * np.sin(2 * np.pi * (50 + 90 * np.exp(-sg * 30)) * sg) * np.exp(-sg * 9)
        if k % 2 == 1:
            i0b, i1b = int((s) * SR), min(n, int((s + 0.12) * SR))
            out[i0b:i1b] += 0.12 * rng.standard_normal(i1b - i0b) * np.exp(-np.arange(i1b - i0b) / SR * 30)
        hs = s + beat / 2
        h0, h1 = int(hs * SR), min(n, int((hs + 0.05) * SR))
        if h1 > h0:
            out[h0:h1] += 0.05 * rng.standard_normal(h1 - h0) * np.exp(-np.arange(h1 - h0) / SR * 60)
    for c in CUTS:
        s = c - 0.35
        i0, i1 = int(s * SR), min(n, int((s + 0.7) * SR))
        sg = np.arange(i1 - i0) / SR
        noise = np.convolve(rng.standard_normal(i1 - i0), np.ones(12) / 12, mode="same")
        out[i0:i1] += 0.5 * noise * np.sin(np.pi * sg / 0.7) ** 2
        # adım çanı
        j0, j1 = int(c * SR), min(n, int((c + 0.6) * SR))
        sg = np.arange(j1 - j0) / SR
        out[j0:j1] += 0.12 * (np.sin(2 * np.pi * 1318.5 * sg) + 0.5 * np.sin(2 * np.pi * 1975.5 * sg)) * np.exp(-sg * 6)
    voice = np.zeros(n)
    for i, (f, ln) in VOICES.items():
        st = S[BASE[i][0]][0] + VOICE_DELAY
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-f", "s16le", "-ac", "1",
                              "-ar", str(SR), "-"], capture_output=True).stdout
        v = np.frombuffer(raw, np.int16).astype(float) / 32768
        i0 = int(st * SR)
        v = v[:max(0, n - i0)]
        voice[i0:i0 + len(v)] += v
    out /= np.max(np.abs(out)) + 1e-9
    if VOICES:
        env = (np.abs(voice) > 0.02).astype(float)
        k = int(0.25 * SR)
        env = np.clip(np.convolve(env, np.ones(k) / k, mode="same") * 4, 0, 1)
        out = out * (1 - 0.6 * env) * 0.55 + voice / (np.max(np.abs(voice)) + 1e-9) * 0.9
    fo = int(1.5 * SR)
    out[-fo:] *= np.linspace(1, 0, fo)
    out = out / (np.max(np.abs(out)) + 1e-9) * 0.85
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


def main():
    if "--still" in sys.argv:
        for s in sys.argv[sys.argv.index("--still") + 1:]:
            frame(float(s)).save(HERE / f"still_{s}.png")
        return
    wav = HERE / "_muzik.wav"
    make_audio(wav)
    nframes = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(OUT)],
        stdin=subprocess.PIPE)
    for i in range(nframes):
        ff.stdin.write(frame(i / FPS).tobytes())
        if i % 300 == 0:
            print(f"kare {i}/{nframes}", flush=True)
    ff.stdin.close()
    ff.wait()
    wav.unlink()
    print("yazıldı:", OUT, f"({DUR:.1f} sn)")


if __name__ == "__main__":
    main()
