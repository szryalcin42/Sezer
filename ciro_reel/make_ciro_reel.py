#!/usr/bin/env python3
"""Akdeniz Bölgesi — kalan 4 günde 600 milyon ₺ ciro hedefi.

9:16 dikey (1080x1920, 30 fps) veri animasyonu reels üretici.
Kare kare PIL ile çizer, numpy ile müzik üretir, ffmpeg ile MP4'e çevirir.
Ayrıca hedef tablosunu hedefler.csv olarak yazar.

Kullanım:  python3 make_ciro_reel.py [çıktı.mp4]

Şube adlarını / personel dağılımını değiştirmek için aşağıdaki
SUBELER listesini düzenleyin (toplam personel 81 olmalı).
"""
import csv
import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------ veri
HEDEF = 600_000_000          # kalan ciro hedefi (₺)
GUN = 4                      # kalan gün
# (şube adı, personel sayısı) — gerçek dağılım bilinmediği için örnek.
SUBELER = [
    ("Şube 1", 9), ("Şube 2", 9), ("Şube 3", 9),
    ("Şube 4", 8), ("Şube 5", 8), ("Şube 6", 8), ("Şube 7", 8), ("Şube 8", 8),
    ("Şube 9", 7), ("Şube 10", 7),
]
PERSONEL = sum(p for _, p in SUBELER)
assert PERSONEL == 81, PERSONEL

GUNLUK = HEDEF / GUN                         # 150 Mn
KISI_TOPLAM = HEDEF / PERSONEL               # 7,41 Mn
KISI_GUNLUK = KISI_TOPLAM / GUN              # 1,85 Mn
SUBE_HEDEF = [(ad, p, KISI_TOPLAM * p) for ad, p in SUBELER]  # personel oranlı

# ------------------------------------------------------------------ görsel
W, H, FPS = 1080, 1920, 30
HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "akdeniz_600m_hedef_reel.mp4"

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


def tr(n, d=0):
    s = f"{n:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def mn(n, d=1):
    return f"{tr(n / 1e6, d)} Mn ₺"


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


# ------------------------------------------------------------------ çizim yardımcıları
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
        a = layer.getchannel("A").point(lambda v: int(v * alpha))
        layer.putalpha(a)
    w, h = layer.size
    ax, ay = anchor
    px = x - (w // 2 if ax == "m" else w if ax == "r" else 0)
    py = y - (h // 2 if ay == "m" else h if ay == "b" else 0)
    px, py = int(px), int(py)
    # ekran dışına taşmayı kırp
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


# ------------------------------------------------------------------ arka plan
def make_bg():
    y = np.linspace(0, 1, H)[:, None]
    x = np.linspace(0, 1, W)[None, :]
    top = np.array(NAVY, float)
    bot = np.array(DEEP, float)
    g = top + (bot - top) * (y ** 1.3)[..., None]
    # sağ üstte güneş parıltısı
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
        col = (TURQ if i % 2 == 0 else SKY)
        d.polygon(pts, fill=col + (int(18 + i * 9),))
    base.alpha_composite(layer, dest=(0, H - 360))


def header(base, t, alpha=1.0):
    text(base, "AKDENİZ BÖLGESİ", W // 2, 250, F_BOLD(40), TURQ, alpha=alpha)
    text(base, "CİRO HEDEF PLANI", W // 2, 300, F_SEMI(30), MUTED, alpha=alpha)


def title(base, s, sub, t, t0):
    p = ease_out(prog(t, t0, 0.5))
    text(base, s, W // 2, 420 - 30 * (1 - p), F_BLACK(92), WHITE, alpha=p)
    if sub:
        text(base, sub, W // 2, 500 - 20 * (1 - p), F_MED(36), SAND, alpha=p)


# ------------------------------------------------------------------ sahneler
# (başlangıç, bitiş)
S = {
    "hook": (0.0, 5.0),
    "ozet": (5.0, 10.0),
    "gun": (10.0, 16.5),
    "sube": (16.5, 24.5),
    "kisi": (24.5, 30.5),
    "outro": (30.5, 36.0),
}
DUR = 36.0
CUTS = [v[0] for v in S.values()][1:]


def scene_alpha(t, name, fade=0.35):
    a, b = S[name]
    if t < a or t > b:
        return 0.0
    fin = 1.0 if a == 0 else clamp((t - a) / fade)
    fout = 1.0 if b >= DUR else clamp((b - t) / fade)
    return min(fin, fout)


def sc_hook(img, t, A):
    t0 = S["hook"][0]
    p1 = back_out(prog(t, t0 + 0.2, 0.6))
    text(img, "KALAN", W // 2, 640, F_BOLD(52), SAND, alpha=A * clamp(p1))
    text(img, "4 GÜN", W // 2, 790, F_BLACK(230), WHITE, alpha=A, scale=max(0.01, p1))
    # sayaç
    pc = ease_io(prog(t, t0 + 1.0, 2.6))
    val = HEDEF * pc
    text(img, f"{tr(val)} ₺", W // 2, 1060, F_BLACK(112), SUN, alpha=A * clamp(pc * 4))
    text(img, "ciro hedefi", W // 2, 1160, F_SEMI(48), MUTED, alpha=A * clamp(pc * 4))
    # ilerleme çubuğu
    bw = 760
    rrect(img, (W / 2 - bw / 2, 1240, W / 2 + bw / 2, 1262), 11, (255, 255, 255), A * 0.15)
    rrect(img, (W / 2 - bw / 2, 1240, W / 2 - bw / 2 + bw * pc, 1262), 11, SUN, A)
    p3 = ease_out(prog(t, t0 + 3.7, 0.6))
    text(img, "Nasıl yetişir? Bölelim ↓", W // 2, 1380 + 20 * (1 - p3), F_BOLD(52), TURQ, alpha=A * p3)


def sc_ozet(img, t, A):
    t0 = S["ozet"][0]
    title(img, "ELİMİZDEKİLER", None, t, t0)
    tiles = [("10", "ŞUBE", TURQ), ("81", "PERSONEL", SUN), ("4", "GÜN", CORAL)]
    for i, (n, lab, col) in enumerate(tiles):
        p = back_out(prog(t, t0 + 0.4 + i * 0.35, 0.55))
        y = 640 + i * 230
        x0 = 140 + (1 - clamp(p)) * -300
        rrect(img, (x0, y - 95, x0 + 800, y + 95), 36, (255, 255, 255), A * 0.08 * clamp(p))
        rrect(img, (x0, y - 95, x0 + 16, y + 95), 8, col, A * clamp(p))
        text(img, n, x0 + 70, y, F_BLACK(140), col, "lm", A * clamp(p))
        text(img, lab, x0 + 330, y, F_BOLD(64), WHITE, "lm", A * clamp(p))
    p = ease_out(prog(t, t0 + 1.9, 0.6))
    text(img, "600 Mn ₺ ÷ 4 gün", W // 2, 1370, F_BOLD(60), WHITE, alpha=A * p)
    p2 = back_out(prog(t, t0 + 2.5, 0.6))
    text(img, "= 150 Mn ₺ / gün", W // 2, 1470, F_BLACK(78), SUN, alpha=A * clamp(p2),
         scale=max(0.01, 0.6 + 0.4 * p2))


def sc_gun(img, t, A):
    t0 = S["gun"][0]
    title(img, "GÜNLERE GÖRE", "her gün eşit pay: 150 Mn ₺", t, t0)
    base_y, maxh, bw, gap = 1270, 560, 170, 50
    x_start = (W - (4 * bw + 3 * gap)) / 2
    cum_max = HEDEF
    for i in range(GUN):
        p = ease_out(prog(t, t0 + 0.6 + i * 0.45, 0.7))
        x = x_start + i * (bw + gap)
        # basamaklı (şelale) sütun: önceki günlerin toplamı + bu günün payı
        prev = maxh * (i * GUNLUK / cum_max)
        if i > 0:
            rrect(img, (x, base_y - prev, x + bw, base_y), 22, (255, 255, 255), A * 0.08)
        h = maxh * (GUNLUK / cum_max) * p
        col = [TURQ, SKY, SUN, CORAL][i]
        rrect(img, (x, base_y - prev - h, x + bw, base_y - prev), 22, col, A * clamp(p * 3))
        text(img, f"{i + 1}. GÜN", x + bw / 2, base_y + 50, F_BOLD(40), WHITE, alpha=A)
        text(img, "+150", x + bw / 2, base_y - prev - h / 2, F_BLACK(44), NAVY,
             alpha=A * clamp(p * 2 - 1))
        text(img, f"Σ {tr((i + 1) * GUNLUK / 1e6)} Mn", x + bw / 2, base_y - prev - h - 34,
             F_BOLD(34), WHITE, alpha=A * clamp(p * 2 - 1))
    # toplam şerit
    pc = ease_io(prog(t, t0 + 2.6, 2.4))
    bw2 = 820
    rrect(img, (W / 2 - bw2 / 2, 1420, W / 2 + bw2 / 2, 1450), 15, (255, 255, 255), A * 0.15)
    rrect(img, (W / 2 - bw2 / 2, 1420, W / 2 - bw2 / 2 + bw2 * pc, 1450), 15, SUN, A)
    text(img, f"{tr(HEDEF * pc / 1e6)} / 600 Mn ₺", W // 2, 1510, F_BOLD(48), WHITE,
         alpha=A * clamp(pc * 5))


def sc_sube(img, t, A):
    t0 = S["sube"][0]
    title(img, "ŞUBEYE GÖRE", "personel sayısına oranlı dağılım", t, t0)
    y0, rh = 600, 92
    maxv = max(v for _, _, v in SUBE_HEDEF)
    x_bar, bar_w = 310, 450
    for i, (ad, p_, v) in enumerate(SUBE_HEDEF):
        p = ease_out(prog(t, t0 + 0.5 + i * 0.16, 0.8))
        y = y0 + i * rh
        a = A * clamp(p * 2)
        text(img, ad, 90, y, F_BOLD(38), WHITE, "lm", a)
        text(img, f"{p_} kişi", 90, y + 34, F_MED(26), MUTED, "lm", a)
        rrect(img, (x_bar, y - 22, x_bar + bar_w, y + 22), 22, (255, 255, 255), a * 0.08)
        w = bar_w * (v / maxv) * p
        col = TURQ if p_ == 9 else SKY if p_ == 8 else SUN
        rrect(img, (x_bar, y - 22, x_bar + w, y + 22), 22, col, A)
        text(img, f"{tr(v / 1e6 * p, 1)} Mn", 1010, y - 8, F_BLACK(36), WHITE, "rm", a)
        text(img, f"{tr(v / GUN / 1e6, 1)} Mn/gün", 1010, y + 28, F_SEMI(26), SAND, "rm", a)
    p = ease_out(prog(t, t0 + 3.2, 0.6))
    text(img, "ortalama şube: 60 Mn ₺  ·  15 Mn ₺ / gün", W // 2, 1560, F_BOLD(40), SUN,
         alpha=A * p)


def sc_kisi(img, t, A):
    t0 = S["kisi"][0]
    title(img, "KİŞİ BAŞI", "81 kişinin her biri", t, t0)
    cols, sp, r = 9, 74, 25
    gx = (W - (cols - 1) * sp) / 2
    gy = 620
    lit = ease_io(prog(t, t0 + 0.5, 1.8)) * PERSONEL
    d = ImageDraw.Draw(img)
    for k in range(PERSONEL):
        cx = gx + (k % cols) * sp
        cy = gy + (k // cols) * sp
        on = clamp(lit - k)
        col = tuple(int(a + (b - a) * on) for a, b in zip((40, 70, 95), SUN if k % 9 == 4 else TURQ))
        rr = r * (0.75 + 0.25 * on)
        # baş + gövde (kişi ikonu)
        d.ellipse((cx - rr * 0.45, cy - rr, cx + rr * 0.45, cy - rr * 0.1), fill=col + (int(255 * A),))
        d.pieslice((cx - rr * 0.8, cy - rr * 0.05, cx + rr * 0.8, cy + rr * 1.4), 180, 360,
                   fill=col + (int(255 * A),))
    p1 = back_out(prog(t, t0 + 2.4, 0.6))
    text(img, f"{tr(KISI_TOPLAM / 1e6, 2)} Mn ₺", W // 2, 1340, F_BLACK(110), SUN,
         alpha=A * clamp(p1), scale=max(0.01, 0.6 + 0.4 * p1))
    text(img, "4 günlük kişisel hedef", W // 2, 1430, F_SEMI(40), MUTED, alpha=A * clamp(p1))
    p2 = back_out(prog(t, t0 + 3.3, 0.6))
    rrect(img, (170, 1490, 910, 1600), 55, CORAL, A * clamp(p2))
    text(img, f"{tr(KISI_GUNLUK / 1e6, 2)} Mn ₺ / gün", W // 2, 1545, F_BLACK(60), WHITE,
         alpha=A * clamp(p2))


def sc_outro(img, t, A):
    t0 = S["outro"][0]
    p0 = ease_out(prog(t, t0, 0.5))
    text(img, "4 GÜNDE", W // 2, 470, F_BOLD(60), SAND, alpha=A * p0)
    text(img, "600 Mn ₺", W // 2, 590, F_BLACK(170), WHITE, alpha=A * p0)
    rows = [("HER GÜN", "150 Mn ₺", TURQ),
            ("HER ŞUBE", "~15 Mn ₺ / gün", SKY),
            ("HER KİŞİ", "1,85 Mn ₺ / gün", SUN)]
    for i, (k, v, col) in enumerate(rows):
        p = back_out(prog(t, t0 + 0.6 + i * 0.4, 0.55))
        y = 820 + i * 170
        x0 = 120 + (1 - clamp(p)) * 200
        a = A * clamp(p)
        rrect(img, (x0, y - 70, x0 + 840, y + 70), 34, (255, 255, 255), a * 0.08)
        text(img, k, x0 + 40, y, F_BOLD(44), col, "lm", a)
        text(img, v, x0 + 800, y, F_BLACK(54), WHITE, "rm", a)
    p = back_out(prog(t, t0 + 2.3, 0.7))
    pulse = 1 + 0.03 * math.sin((t - t0) * 7) * clamp(p)
    text(img, "HADİ AKDENİZ!", W // 2, 1400, F_BLACK(104), SUN, alpha=A * clamp(p),
         scale=max(0.01, p * pulse))
    text(img, "Hedef bizim, başarı bizim.", W // 2, 1510, F_SEMI(44), WHITE,
         alpha=A * clamp(p))


SCENES = [("hook", sc_hook), ("ozet", sc_ozet), ("gun", sc_gun),
          ("sube", sc_sube), ("kisi", sc_kisi), ("outro", sc_outro)]


def frame(t):
    img = BG.copy()
    waves(img, t)
    header(img, t)
    for name, fn in SCENES:
        A = scene_alpha(t, name)
        if A > 0:
            fn(img, t, A)
    # alt ilerleme göstergesi (sahneler)
    for i, (name, _) in enumerate(SCENES):
        a, b = S[name]
        x = W / 2 - 3 * 70 + i * 84
        rrect(img, (x, 1690, x + 70, 1698), 4, (255, 255, 255), 0.18)
        f = clamp((t - a) / (b - a))
        if f > 0:
            rrect(img, (x, 1690, x + 70 * f, 1698), 4, TURQ, 0.9)
    return img.convert("RGB")


# ------------------------------------------------------------------ ses
SR = 44100


def make_audio(path):
    n = int(DUR * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    bpm = 118
    beat = 60 / bpm
    # akorlar: Am - F - C - G  (her biri 2 ölçü = 8 vuruş)
    chords = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63],
              [261.63, 329.63, 392.0], [196.0, 246.94, 293.66]]
    bars = int(DUR / (beat * 4)) + 1
    for b in range(bars):
        ch = chords[(b // 2) % 4]
        s0 = b * 4 * beat
        i0, i1 = int(s0 * SR), min(n, int((s0 + 4 * beat) * SR))
        seg = tt[i0:i1] - s0
        env = np.minimum(1, seg / 0.3) * np.exp(-seg * 0.35)
        pad = sum(np.sin(2 * np.pi * f * seg) + 0.3 * np.sin(4 * np.pi * f * seg) for f in ch)
        out[i0:i1] += 0.035 * pad * env
        # bas: kök nota, sekizlik
        for k in range(8):
            bs = s0 + k * beat / 2
            j0, j1 = int(bs * SR), min(n, int((bs + beat / 2) * SR))
            sg = tt[j0:j1] - bs
            out[j0:j1] += 0.10 * np.sign(np.sin(2 * np.pi * ch[0] / 2 * sg)) * np.exp(-sg * 9) * 0.6
    nb = int(DUR / beat) + 1
    rng = np.random.default_rng(7)
    for k in range(nb):
        s = k * beat
        i0, i1 = int(s * SR), min(n, int((s + 0.35) * SR))
        sg = tt[i0:i1] - s
        if s > 0.9:  # açılışta yumuşak giriş
            out[i0:i1] += 0.45 * np.sin(2 * np.pi * (50 + 90 * np.exp(-sg * 30)) * sg) * np.exp(-sg * 9)
        hs = s + beat / 2
        h0, h1 = int(hs * SR), min(n, int((hs + 0.06) * SR))
        if h1 > h0:
            out[h0:h1] += 0.06 * rng.standard_normal(h1 - h0) * np.exp(-np.arange(h1 - h0) / SR * 60)
    # sahne geçişlerinde "whoosh"
    for c in CUTS:
        s = c - 0.35
        i0, i1 = int(s * SR), min(n, int((s + 0.7) * SR))
        sg = np.arange(i1 - i0) / SR
        noise = rng.standard_normal(i1 - i0)
        noise = np.convolve(noise, np.ones(12) / 12, mode="same")
        out[i0:i1] += 0.5 * noise * np.sin(np.pi * sg / 0.7) ** 2
    # sayaç tıkları (hook)
    for k in range(26):
        s = 1.0 + k * 0.1
        i0, i1 = int(s * SR), int((s + 0.03) * SR)
        sg = tt[i0:i1] - s
        out[i0:i1] += 0.18 * np.sin(2 * np.pi * 1800 * sg) * np.exp(-sg * 150)
    # bitiş: fade-out
    fo = int(1.5 * SR)
    out[-fo:] *= np.linspace(1, 0, fo)
    out /= np.max(np.abs(out)) + 1e-9
    out *= 0.85
    pcm = (out * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ------------------------------------------------------------------ çıktı
def write_csv():
    with open(HERE / "hedefler.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Kırılım", "Personel", "4 Günlük Hedef (₺)", "Günlük Hedef (₺)"])
        w.writerow(["Akdeniz Bölgesi", PERSONEL, tr(HEDEF), tr(GUNLUK)])
        for i in range(GUN):
            w.writerow([f"{i + 1}. Gün", PERSONEL, tr(GUNLUK), tr(GUNLUK)])
        for ad, p, v in SUBE_HEDEF:
            w.writerow([ad, p, tr(v), tr(v / GUN)])
        w.writerow(["Kişi başı", 1, tr(KISI_TOPLAM), tr(KISI_GUNLUK)])


def main():
    write_csv()
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
        if i % 150 == 0:
            print(f"kare {i}/{nframes}", flush=True)
    ff.stdin.close()
    ff.wait()
    wav.unlink()
    print("yazıldı:", OUT)


if __name__ == "__main__":
    main()
