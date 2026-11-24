#!/usr/bin/env python3
"""'Tasarruf finansman nedir?' — 30 sn'lik 9:16 dikey reel üretici.

Kare kare PIL ile çizer, ffmpeg ile MP4'e çevirir. Dış ses tek bir dosyadır
(voice/full.mp3); cümle aralarındaki sessizlikler bulunur ve her cümle bir
sahneye eşlenir, sahne süreleri sese göre ayarlanır.

Kullanım:  python3 make_reel.py [çıktı.mp4]      (önizleme: --preview)
"""
import math
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
HERE = Path(__file__).resolve().parent
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = Path(ARGS[0]) if ARGS else HERE / "tasarruf_finansman_reel.mp4"
VOICE = HERE / "voice" / "full.mp3"

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

NAVY = (12, 27, 51)
NAVY2 = (22, 48, 86)
GREEN = (46, 204, 140)
GREEN_D = (24, 120, 84)
GOLD = (245, 190, 70)
RED = (235, 77, 75)
WHITE = (245, 247, 250)
GREY = (150, 165, 190)


def font(path, size):
    return ImageFont.truetype(path, size)


F_TITLE = font(FONT_B, 84)
F_HOOK = font(FONT_B, 96)
F_BODY = font(FONT_R, 44)
F_CHIP = font(FONT_B, 36)
F_BIG = font(FONT_B, 150)
F_MID = font(FONT_B, 56)
F_SMALL = font(FONT_B, 32)
F_TINY = font(FONT_R, 28)

# ---------------------------------------------------------------- senaryo
# (varsayılan süre, rozet, başlık, alt yazı, görsel türü)
SCENES = [
    (3.5, "", "Faiz ödemeden\nev ya da araba\nsahibi olmak?", "", "hook"),
    (3.5, "GERÇEK", "Banka faizleri\nçok yüksek", "Kredi maliyeti her ay büyür.", "bank"),
    (3.5, "TEMEL KURAL", "Borçlanmadan\nmal mülk\nalınmaz", "Önemli olan NASIL borçlandığın.", "rule"),
    (3.5, "RİSK", "Altın & döviz:\nkesin kazanç\ngarantisi yok", "Fiyatlar iner de çıkar da.", "gold"),
    (3.5, "1", "Sistem seni\nbirikime\nteşvik eder", "Her ay düzenli birikim.", "piggy"),
    (4.0, "2", "%45'ini öde,\nfinansmanın\ntamamına ulaş", "İstediğin finansmana erken erişim.", "progress"),
    (3.5, "3", "Borç bitene\nkadar sabit\nödeme", "Taksitlerin sürpriz yapmaz.", "fixed"),
    (4.0, "", "Tasarruf\nFinansman", "", "outro"),
]
OUTRO_TIPS = ["Faizsiz", "Planlı birikim", "Sabit taksit"]
VOICE_LEAD = 0.25   # ses başlamadan önceki boşluk (sn)
# voice/full.mp3 içinde 10 sessizlik bulunur; sahne sınırı olanların sırası:
SENTENCE_GAPS = range(10)
BOUNDARY = [0, 2, 4, 5, 6, 7, 8]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def voice_segments(path, n):
    """Sesteki en uzun n-1 sessizliği sahne sınırı olarak döndürür."""
    r = run(["ffmpeg", "-i", str(path), "-af", "silencedetect=noise=-35dB:d=0.25", "-f", "null", "-"])
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "csv=p=0", str(path)]).stdout)
    gaps = [(e - s, (s + e) / 2) for s, e in zip(st, en) if s > 0.3 and e < dur - 0.3]
    if len(gaps) == len(SENTENCE_GAPS) and len(BOUNDARY) == n - 1:
        # bilinen kayıt: cümle sonu olan sessizlikleri seç ("Önce gerçek:" gibi duraklamaları atla)
        mids = [g[1] for g in gaps]
        cuts = [0.0] + [mids[k] for k in BOUNDARY] + [dur]
    else:
        gaps = sorted(sorted(gaps, reverse=True)[: n - 1], key=lambda g: g[1])
        cuts = [0.0] + [g[1] for g in gaps] + [dur]
    return cuts, dur


if VOICE.exists():
    CUTS, VDUR = voice_segments(VOICE, len(SCENES))
    if len(CUTS) == len(SCENES) + 1:
        for i in range(len(SCENES)):
            d = CUTS[i + 1] - CUTS[i] + (VOICE_LEAD if i == 0 else 0)
            if i == len(SCENES) - 1:
                d += 1.2
            SCENES[i] = (round(d, 2),) + SCENES[i][1:]

starts, t = [], 0.0
for s in SCENES:
    starts.append(t)
    t += s[0]
TOTAL = t
NFRAMES = int(TOTAL * FPS)


# ---------------------------------------------------------------- yardımcılar
def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def back(x):
    x = max(0.0, min(1.0, x))
    c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def lerp(a, b, k):
    return a + (b - a) * k


def mix(c1, c2, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(lerp(a, b, k)) for a, b in zip(c1, c2))


def make_bg():
    g = np.linspace(0, 1, H)[:, None]
    top = np.array(NAVY2)
    bot = np.array(NAVY)
    arr = (top * (1 - g) + bot * g).reshape(H, 1, 3)
    arr = np.broadcast_to(arr, (H, W, 3)).astype(np.uint8)
    img = Image.fromarray(arr.copy(), "RGB")
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((90, 950, 990, 1800), fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(170))
    img = Image.composite(Image.new("RGB", (W, H), (30, 110, 120)), img, glow)
    # ince ızgara
    d = ImageDraw.Draw(img)
    for x in range(0, W, 90):
        d.line([(x, 0), (x, H)], fill=(24, 44, 74), width=1)
    for y in range(0, H, 90):
        d.line([(0, y), (W, y)], fill=(24, 44, 74), width=1)
    return img


BG = make_bg()
VIS_C = (540, 1330)   # görsel alanın merkezi


def ctext(d, y, txt, f, col):
    tw = d.textlength(txt, font=f)
    d.text(((W - tw) / 2, y), txt, font=f, fill=col)


# ---------------------------------------------------------------- ikonlar
def draw_house(d, cx, cy, s, col, roof=None, door=NAVY):
    roof = roof or col
    d.polygon([(cx - 130 * s, cy - 20 * s), (cx, cy - 130 * s), (cx + 130 * s, cy - 20 * s)], fill=roof)
    d.rectangle((cx - 100 * s, cy - 25 * s, cx + 100 * s, cy + 110 * s), fill=col)
    d.rectangle((cx - 25 * s, cy + 30 * s, cx + 25 * s, cy + 110 * s), fill=door)
    d.rectangle((cx - 80 * s, cy + 5 * s, cx - 45 * s, cy + 40 * s), fill=door)
    d.rectangle((cx + 45 * s, cy + 5 * s, cx + 80 * s, cy + 40 * s), fill=door)


def draw_car(d, cx, cy, s, col):
    d.rounded_rectangle((cx - 150 * s, cy - 20 * s, cx + 150 * s, cy + 50 * s), int(25 * s), fill=col)
    d.polygon([(cx - 90 * s, cy - 20 * s), (cx - 55 * s, cy - 80 * s), (cx + 60 * s, cy - 80 * s),
               (cx + 100 * s, cy - 20 * s)], fill=col)
    d.polygon([(cx - 70 * s, cy - 25 * s), (cx - 45 * s, cy - 68 * s), (cx - 5 * s, cy - 68 * s),
               (cx - 5 * s, cy - 25 * s)], fill=NAVY)
    d.polygon([(cx + 5 * s, cy - 25 * s), (cx + 5 * s, cy - 68 * s), (cx + 52 * s, cy - 68 * s),
               (cx + 80 * s, cy - 25 * s)], fill=NAVY)
    for x in (-85, 85):
        d.ellipse((cx + (x - 35) * s, cy + 15 * s, cx + (x + 35) * s, cy + 85 * s), fill=(30, 30, 40))
        d.ellipse((cx + (x - 15) * s, cy + 35 * s, cx + (x + 15) * s, cy + 65 * s), fill=GREY)


def draw_coin(d, cx, cy, r, col=GOLD, label="₺"):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=mix(col, (120, 80, 10), 0.35))
    d.ellipse((cx - r * 0.86, cy - r * 0.86, cx + r * 0.86, cy + r * 0.86), fill=col)
    f = font(FONT_B, int(r * 1.05))
    tw = d.textlength(label, font=f)
    d.text((cx - tw / 2, cy - r * 0.62), label, font=f, fill=mix(col, (120, 80, 10), 0.6))


def panel(d, a):
    cx, cy = VIS_C
    w, h = 430 * a, 400 * a
    d.rounded_rectangle((cx - w, cy - h, cx + w, cy + h), 50, fill=(18, 38, 68), outline=(40, 75, 120), width=3)


# ---------------------------------------------------------------- sahne görselleri
def vis_hook(img, d, st, t):
    a = back(st / 0.6)
    cx, cy = VIS_C
    draw_house(d, cx - 190, cy - 40, 1.15 * a, WHITE, GREEN)
    k = back((st - 0.35) / 0.6)
    if k > 0:
        draw_car(d, cx + 200, cy + 120, 0.95 * k, GOLD)
    # yanıp sönen soru işareti
    q = ease((st - 0.8) / 0.4)
    if q > 0:
        f = font(FONT_B, 190)
        bob = 12 * math.sin(t * 5)
        d.text((cx + 140, cy - 330 + bob), "?", font=f, fill=mix(NAVY, GREEN, q))
    # üstü çizili yüzde
    p = ease((st - 1.2) / 0.4)
    if p > 0:
        x, y = cx - 360, cy + 220
        d.text((x, y), "%", font=F_BIG, fill=mix(NAVY, RED, p))
        d.line([(x - 10, y + 165), (x + 140, y + 20)], fill=mix(NAVY, WHITE, p), width=14)


def vis_bank(img, d, st, t):
    a = ease(st / 0.5)
    panel(d, a)
    cx, cy = VIS_C
    if a < 0.6:
        return
    # banka binası
    bx, by = cx - 220, cy + 40
    d.polygon([(bx - 150, by - 120), (bx, by - 210), (bx + 150, by - 120)], fill=GREY)
    for i in range(4):
        x = bx - 115 + i * 77
        d.rectangle((x, by - 110, x + 30, by + 90), fill=GREY)
    d.rectangle((bx - 160, by + 90, bx + 160, by + 120), fill=GREY)
    ctext_x = bx - d.textlength("BANKA", font=F_SMALL) / 2
    d.text((ctext_x, by + 140), "BANKA", font=F_SMALL, fill=GREY)
    # yükselen faiz grafiği
    k = ease((st - 0.4) / 2.0)
    pts = []
    for i in range(int(2 + 18 * k)):
        u = i / 19
        x = cx + 20 + u * 340
        y = cy + 200 - (u ** 2.2) * 420 - 10 * math.sin(i * 1.3)
        pts.append((x, y))
    if len(pts) > 1:
        d.line(pts, fill=RED, width=12, joint="curve")
        x, y = pts[-1]
        d.polygon([(x + 30, y - 25), (x - 22, y - 30), (x + 10, y + 22)], fill=RED)
    d.text((cx + 40, cy - 330), "FAİZ ↑", font=F_MID, fill=mix(NAVY, RED, k * 2))
    d.text((cx + 40, cy - 265), "toplam maliyet", font=F_TINY, fill=GREY)


def vis_rule(img, d, st, t):
    a = ease(st / 0.5)
    panel(d, a)
    cx, cy = VIS_C
    if a < 0.6:
        return
    # terazi: bir kefede ev, diğerinde para yığını
    tilt = 0.18 * math.sin(min(st, 2.0) * 2.4) * math.exp(-st * 0.6)
    d.rectangle((cx - 10, cy - 200, cx + 10, cy + 230), fill=GREY)
    d.rounded_rectangle((cx - 120, cy + 220, cx + 120, cy + 250), 12, fill=GREY)
    L = 300
    x1, y1 = cx - L * math.cos(tilt), cy - 200 - L * math.sin(tilt)
    x2, y2 = cx + L * math.cos(tilt), cy - 200 + L * math.sin(tilt)
    d.line([(x1, y1), (x2, y2)], fill=WHITE, width=10)
    d.ellipse((cx - 22, cy - 222, cx + 22, cy - 178), fill=GOLD)
    for (x, y), side in (((x1, y1), 0), ((x2, y2), 1)):
        d.line([(x, y), (x - 90, y + 170)], fill=GREY, width=4)
        d.line([(x, y), (x + 90, y + 170)], fill=GREY, width=4)
        d.chord((x - 120, y + 120, x + 120, y + 220), 0, 180, fill=WHITE)
        if side == 0:
            draw_house(d, x, y + 95, 0.5, GREEN, GREEN_D)
        else:
            for j in range(5):
                draw_coin(d, x - 40 + (j % 3) * 40, y + 140 - (j // 3) * 40 - 10, 28)
    k = ease((st - 1.2) / 0.4)
    if k > 0:
        ctext(d, cy + 290, "BİRİKİM  =  MÜLK", F_SMALL, mix(NAVY, GOLD, k))


def vis_gold(img, d, st, t):
    a = ease(st / 0.5)
    panel(d, a)
    cx, cy = VIS_C
    if a < 0.6:
        return
    # zigzag fiyat grafiği
    k = ease((st - 0.3) / 2.2)
    pts = []
    n = int(2 + 26 * k)
    for i in range(n):
        u = i / 27
        x = cx - 360 + u * 720
        y = cy + 60 - 170 * math.sin(u * 9.5) * (0.5 + 0.5 * math.cos(u * 3.1)) - 60 * math.sin(u * 23)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        col = GREEN if pts[i + 1][1] < pts[i][1] else RED
        d.line([pts[i], pts[i + 1]], fill=col, width=10)
    d.line([(cx - 370, cy + 260), (cx + 370, cy + 260)], fill=GREY, width=3)
    # altın külçe + dolar
    gx, gy = cx - 250, cy - 300
    d.polygon([(gx - 90, gy + 40), (gx - 60, gy - 30), (gx + 60, gy - 30), (gx + 90, gy + 40)], fill=GOLD)
    d.polygon([(gx - 60, gy - 30), (gx - 40, gy - 50), (gx + 40, gy - 50), (gx + 60, gy - 30)],
              fill=(255, 220, 130))
    draw_coin(d, cx + 250, cy - 300, 60, (120, 200, 120), "$")
    q = ease((st - 1.0) / 0.4)
    if q > 0:
        f = font(FONT_B, 130)
        ctext(d, cy - 370 + 8 * math.sin(t * 6), "?", f, mix(NAVY, WHITE, q))


def vis_piggy(img, d, st, t):
    a = back(st / 0.6)
    cx, cy = VIS_C
    cy += 80
    s = a
    # kumbara
    d.ellipse((cx - 230 * s, cy - 160 * s, cx + 230 * s, cy + 160 * s), fill=(244, 143, 177))
    d.ellipse((cx + 170 * s, cy - 50 * s, cx + 290 * s, cy + 50 * s), fill=(236, 120, 160))
    d.ellipse((cx + 215 * s, cy - 15 * s, cx + 235 * s, cy + 5 * s), fill=(150, 60, 90))
    d.ellipse((cx + 245 * s, cy - 15 * s, cx + 265 * s, cy + 5 * s), fill=(150, 60, 90))
    d.polygon([(cx + 60 * s, cy - 140 * s), (cx + 110 * s, cy - 220 * s), (cx + 140 * s, cy - 120 * s)],
              fill=(236, 120, 160))
    d.ellipse((cx + 90 * s, cy - 70 * s, cx + 115 * s, cy - 45 * s), fill=NAVY)
    for x in (-140, -40, 60, 150):
        d.rounded_rectangle((cx + (x - 25) * s, cy + 120 * s, cx + (x + 25) * s, cy + 200 * s), 10,
                            fill=(236, 120, 160))
    d.rounded_rectangle((cx - 60 * s, cy - 165 * s, cx + 60 * s, cy - 145 * s), 8, fill=(150, 60, 90))
    # düşen paralar
    if st > 0.5:
        for i in range(6):
            ph = (st - 0.5 - i * 0.35)
            if ph < 0:
                continue
            ph = ph % 2.1
            if ph > 0.7:
                continue
            y = cy - 520 + ph / 0.7 * 360
            draw_coin(d, cx, y, 44)
    # ay sayacı
    months = min(12, int(max(0, st - 0.5) * 4) + 1)
    d.text((cx - 360, cy - 430), f"{months}. ay", font=F_MID, fill=GREEN)
    bar_w = 720 * months / 12
    d.rounded_rectangle((cx - 360, cy + 260, cx + 360, cy + 290), 15, fill=(30, 55, 90))
    d.rounded_rectangle((cx - 360, cy + 260, cx - 360 + bar_w, cy + 290), 15, fill=GREEN)


def vis_progress(img, d, st, t):
    cx, cy = VIS_C
    a = ease(st / 0.4)
    # yüzde çemberi
    r = 260
    box = (cx - r, cy - r - 60, cx + r, cy + r - 60)
    d.arc(box, 0, 360, fill=(30, 55, 90), width=44)
    p = 0.45 * ease((st - 0.3) / 1.6)
    if p > 0:
        d.arc(box, -90, -90 + 360 * p, fill=GOLD, width=44)
    full = ease((st - 2.2) / 0.9)
    if full > 0:
        d.arc(box, -90 + 360 * 0.45, -90 + 360 * (0.45 + 0.55 * full), fill=GREEN, width=44)
    pct = f"%{int(round(p * 100))}" if full <= 0 else "%100"
    col = GOLD if full <= 0 else GREEN
    ctext(d, cy - 140, pct, font(FONT_B, 120), mix(NAVY, col, a))
    lbl = "biriktir" if full <= 0 else "finansman hazır!"
    ctext(d, cy + 20, lbl, F_SMALL, mix(NAVY, WHITE, a))
    # anahtar
    if full > 0.5:
        k = back((full - 0.5) / 0.5)
        kx, ky = cx, cy + 330
        d.ellipse((kx - 150 * k, ky - 45 * k, kx - 60 * k, ky + 45 * k), outline=GOLD, width=int(18 * k) + 1)
        d.rectangle((kx - 62 * k, ky - 10 * k, kx + 150 * k, ky + 10 * k), fill=GOLD)
        d.rectangle((kx + 90 * k, ky, kx + 108 * k, ky + 45 * k), fill=GOLD)
        d.rectangle((kx + 125 * k, ky, kx + 143 * k, ky + 35 * k), fill=GOLD)


def vis_fixed(img, d, st, t):
    a = ease(st / 0.5)
    panel(d, a)
    cx, cy = VIS_C
    if a < 0.6:
        return
    base = cy + 240
    n = 8
    bw = 62
    for i in range(n):
        k = back((st - 0.3 - i * 0.12) / 0.4)
        if k <= 0:
            continue
        x = cx - 330 + i * 86
        h = 280 * k
        d.rounded_rectangle((x, base - h, x + bw, base), 12, fill=GREEN)
        d.text((x + 8, base + 14), f"{i + 1}.", font=F_TINY, fill=GREY)
    k = ease((st - 1.4) / 0.5)
    if k > 0:
        y = base - 280 - 30
        x1 = cx - 340 + 700 * k
        for x in range(int(cx - 340), int(x1), 40):
            d.line([(x, y), (x + 22, y)], fill=WHITE, width=6)
        ctext(d, cy - 330, "Taksit = SABİT", F_MID, mix(NAVY, WHITE, k))
    # kilit simgesi
    q = back((st - 1.8) / 0.5)
    if q > 0:
        lx, ly = cx + 300, cy - 175
        d.arc((lx - 40 * q, ly - 80 * q, lx + 40 * q, ly), 180, 360, fill=GOLD, width=int(14 * q) + 1)
        d.rounded_rectangle((lx - 55 * q, ly - 30 * q, lx + 55 * q, ly + 60 * q), 12, fill=GOLD)


def vis_outro(img, d, st, t):
    cx, cy = VIS_C
    y = 860
    for i, tip in enumerate(OUTRO_TIPS):
        a = ease((st - 0.6 - i * 0.45) / 0.4)
        if a <= 0:
            continue
        x = 220 + (1 - a) * 80
        d.ellipse((x, y + 6, x + 64, y + 70), fill=mix(NAVY, GREEN, a))
        d.line([(x + 15, y + 40), (x + 29, y + 54), (x + 50, y + 22)], fill=NAVY, width=8)
        d.text((x + 100, y + 2), tip, font=F_MID, fill=mix(NAVY, WHITE, a))
        y += 120
    k = back((st - 1.6) / 0.6)
    if k > 0:
        draw_house(d, cx, 1450, 1.0 * k, WHITE, GREEN)
    a = ease((st - 2.4) / 0.5)
    if a > 0:
        ctext(d, 1640, "Hayaline bugün başla", F_MID, mix(NAVY, GOLD, a))
        ctext(d, 1720, "Kaydet  •  Paylaş  •  Takip et", F_SMALL, mix(NAVY, WHITE, a))


VIS = {"hook": vis_hook, "bank": vis_bank, "rule": vis_rule, "gold": vis_gold,
       "piggy": vis_piggy, "progress": vis_progress, "fixed": vis_fixed, "outro": vis_outro}


def draw_text_block(d, st, badge, title, sub, kind):
    y = 220
    if badge:
        a = ease(st / 0.35)
        tw = d.textlength(badge, font=F_CHIP)
        x0 = 90 - (1 - a) * 60
        col = RED if badge in ("GERÇEK", "RİSK") else (GOLD if badge == "TEMEL KURAL" else GREEN)
        if len(badge) == 1:
            badge = f"AVANTAJ {badge}"
            tw = d.textlength(badge, font=F_CHIP)
        d.rounded_rectangle((x0, y, x0 + tw + 56, y + 66), 33, fill=mix(NAVY, col, a))
        d.text((x0 + 28, y + 13), badge, font=F_CHIP, fill=NAVY)
        y += 100
    f = F_HOOK if kind in ("hook", "outro") else F_TITLE
    for i, line in enumerate(title.split("\n")):
        a = ease((st - 0.1 - i * 0.14) / 0.45)
        lh = f.size + 20
        if a > 0:
            col = WHITE
            if kind == "outro" and i == 1:
                col = GREEN
            if kind == "hook":
                ctext(d, y + (1 - a) * 50, line, f, mix(NAVY, col, a))
            else:
                d.text((90 + (1 - a) * 80, y), line, font=f, fill=mix(NAVY, col, a))
        y += lh
    if sub:
        a = ease((st - 0.6) / 0.45)
        if a > 0:
            d.text((90, y + 20 + (1 - a) * 25), sub, font=F_BODY, fill=mix(NAVY, GREY, a))


def scene_at(t):
    for i in range(len(SCENES)):
        if t < starts[i] + SCENES[i][0] or i == len(SCENES) - 1:
            return i, t - starts[i]


def render_frame(n):
    t = n / FPS
    i, st = scene_at(t)
    dur, badge, title, sub, kind = SCENES[i]
    img = BG.copy()
    d = ImageDraw.Draw(img)
    VIS[kind](img, d, st, t)
    draw_text_block(d, st, badge, title, sub, kind)
    # ilerleme çubuğu
    d.rounded_rectangle((90, 120, W - 90, 132), 6, fill=(35, 60, 95))
    d.rounded_rectangle((90, 120, 90 + (W - 180) * (t / TOTAL), 132), 6, fill=GREEN)
    # yasal not
    note = "Bilgilendirme amaçlıdır, yatırım tavsiyesi değildir."
    ctext(d, H - 70, note, F_TINY, (95, 115, 145))
    # sahne geçişi (beyaz flaş yerine hızlı kararma)
    out_a = 1 - ease((st - (dur - 0.25)) / 0.25) if i < len(SCENES) - 1 else 1.0
    if out_a < 1:
        img = Image.blend(Image.new("RGB", (W, H), NAVY), img, 0.3 + 0.7 * out_a)
    if t < 0.25:
        img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, t / 0.25)
    if i == len(SCENES) - 1 and st > dur - 0.5:
        img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, max(0, (dur - st) / 0.5))
    return img


# ---------------------------------------------------------------- ses
def make_audio(path, sr=44100):
    n = int(TOTAL * sr)
    tt = np.arange(n) / sr
    out = np.zeros(n)
    # umut veren pad: C - G - Am - F, 120 BPM'lik hafif vuruş
    chords = [[261.6, 329.6, 392.0], [196.0, 246.9, 293.7], [220.0, 261.6, 329.6], [174.6, 220.0, 261.6]]
    seg = 2.0
    for k in range(int(TOTAL / seg) + 1):
        a, b = int(k * seg * sr), min(n, int((k + 1) * seg * sr))
        if a >= n:
            break
        loc = tt[a:b] - k * seg
        env = np.minimum(1, loc / 0.3) * np.minimum(1, (seg - loc) / 0.3)
        for f in chords[k % 4]:
            out[a:b] += 0.045 * env * (np.sin(2 * np.pi * f * loc) + 0.25 * np.sin(2 * np.pi * f * 2 * loc))
    beat = 0.5
    L = int(0.12 * sr)
    lt = np.arange(L) / sr
    kick = np.sin(2 * np.pi * (55 + 90 * np.exp(-lt * 40)) * lt) * np.exp(-lt * 25)
    for k in range(int(TOTAL / beat)):
        i0 = int(k * beat * sr)
        if i0 + L < n:
            out[i0:i0 + L] += 0.12 * kick
    fade = np.minimum(1, tt / 0.5) * np.minimum(1, (TOTAL - tt) / 1.0)
    out = out * fade / max(1e-6, np.abs(out).max()) * 0.8
    if VOICE.exists():
        raw = run_bytes(["ffmpeg", "-v", "error", "-i", str(VOICE), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"])
        v = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
        voice = np.zeros(n)
        i0 = int(VOICE_LEAD * sr)
        v = v[: max(0, n - i0)]
        voice[i0:i0 + len(v)] = v
        voice /= max(1e-6, np.abs(voice).max())
        env = np.convolve(np.abs(voice), np.ones(int(0.3 * sr)) / int(0.3 * sr), mode="same")
        duck = 1 - 0.7 * np.clip(env * 12, 0, 1)
        out = out * 0.4 * duck + voice * 0.95
    out = np.clip(out, -1, 1)
    pcm = (out * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(np.stack([pcm, pcm], axis=1).tobytes())


def run_bytes(cmd):
    return subprocess.run(cmd, capture_output=True, check=True).stdout


def main():
    wav = OUT.with_suffix(".wav")
    make_audio(wav)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
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
        outdir = Path(sys.argv[sys.argv.index("--preview") + 1]) if len(sys.argv) > sys.argv.index("--preview") + 1 else HERE
        for i in range(len(SCENES)):
            render_frame(int((starts[i] + SCENES[i][0] * 0.8) * FPS)).resize((540, 960)).save(outdir / f"prev_{i}.png")
        print("sahneler:", [s[0] for s in SCENES], "toplam", round(TOTAL, 2))
    else:
        main()
