#!/usr/bin/env python3
"""'Türk kahvesi neden köpürür?' — 9:16 dikey reel üretici.

Kare kare PIL ile çizer, ffmpeg ile MP4'e çevirir, numpy ile basit
arka plan müziği + kabarcık sesleri üretir.

Kullanım:  python3 make_reel.py [çıktı.mp4]
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
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "turk_kahvesi_kopuk_reel.mp4"

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_S = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

CREAM = (243, 227, 200)
GOLD = (217, 160, 91)
COPPER = (181, 101, 46)
COPPER_D = (120, 60, 25)
FOAM = (196, 150, 105)
FOAM_L = (226, 190, 145)
DARK = (28, 16, 10)


def font(path, size):
    return ImageFont.truetype(path, size)


F_TITLE = font(FONT_S, 92)
F_HOOK = font(FONT_S, 118)
F_BODY = font(FONT_R, 46)
F_CHIP = font(FONT_B, 38)
F_SMALL = font(FONT_B, 34)
F_LABEL = font(FONT_B, 44)

# ---------------------------------------------------------------- senaryo
# (süre sn, rozet, başlık, gövde, köpük hedefi 0..1, alev 0..1, inset türü)
SCENES = [
    (4.0, "", "Türk kahvesi\nNEDEN\nköpürür?", "", 0.55, 0.6, "hook"),
    (5.0, "1 / 5", "Pudra gibi\nöğütme",
     "Çok ince kahve taneleri kabarcıkların\netrafını sarar ve onları zırh gibi korur.",
     0.35, 0.5, "particles"),
    (5.0, "2 / 5", "Gizli gaz: CO₂",
     "Taze kavrulmuş kahve içinde karbondioksit\nsaklar. Isınınca gaz çıkar, kabarcık olur.",
     0.5, 0.6, "co2"),
    (5.0, "3 / 5", "Soğuk su,\nkısık ateş",
     "Yavaş ısınmada gaz acele etmeden çıkar;\nkabarcıklar patlamadan üst üste birikir.",
     0.65, 0.35, "thermo"),
    (5.0, "4 / 5", "Doğal köpük\nyapıcılar",
     "Kahve yağları, proteinler ve melanoidinler\nkabarcık zarını güçlendirir.",
     0.8, 0.5, "film"),
    (5.0, "5 / 5", "Cezvenin\ndar boğazı",
     "Dar ağız köpüğü bir araya toplar;\nköpük yükselir ve kalınlaşır.",
     1.0, 0.5, "neck"),
    (5.0, "DİKKAT", "Sakın\nkaynatma!",
     "Kaynarsa kabarcıklar patlar, köpük söner.\nKabarınca hemen ocaktan al.",
     -1.0, 1.0, "boil"),
    (6.0, "", "Bol köpüğün\nsırrı", "", 1.0, 0.4, "outro"),
]
OUTRO_TIPS = ["Taze çekilmiş kahve", "Soğuk su", "Kısık ateş",
              "Karıştırmayı erken bitir", "Kaynatmadan ocaktan al"]

# Dış ses: voice/<sahne_no>.mp3 varsa sahne süresi sese göre uzatılır.
VOICE_DIR = HERE / "voice"
VOICE_DELAY = 0.35  # sahne başladıktan sonra sesin girişi (sn)


def clip_len(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())


VOICES = {}
for i in range(len(SCENES)):
    vp = VOICE_DIR / f"{i}.mp3"
    if vp.exists():
        VOICES[i] = vp
        need = VOICE_DELAY + clip_len(vp) + (1.4 if i == len(SCENES) - 1 else 0.55)
        if need > SCENES[i][0]:
            SCENES[i] = (round(need, 2),) + SCENES[i][1:]

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


def lerp(a, b, k):
    return a + (b - a) * k


def mix(c1, c2, k):
    return tuple(int(lerp(a, b, k)) for a, b in zip(c1, c2))


def make_bg():
    g = np.linspace(0, 1, H)[:, None]
    top = np.array([58, 34, 22])
    bot = np.array([14, 8, 5])
    arr = (top * (1 - g) + bot * g)[:, :, None].repeat(1, 2)
    arr = np.broadcast_to(arr.reshape(H, 1, 3), (H, W, 3)).astype(np.uint8)
    img = Image.fromarray(arr.copy(), "RGB")
    # sıcak ışık halesi
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((140, 1050, 940, 1900), fill=90)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    warm = Image.new("RGB", (W, H), (150, 75, 30))
    img = Image.composite(warm, img, glow)
    return img


BG = make_bg()

# Köpük kabarcıkları: sabit tohumlu rastgele dağılım
rng = random.Random(42)
FOAM_BUBBLES = [(rng.uniform(-1, 1), rng.uniform(0, 1), rng.uniform(9, 26), rng.uniform(0, 6.28))
                for _ in range(170)]
CO2_BUBBLES = [(rng.uniform(-1, 1), rng.uniform(0, 1), rng.uniform(10, 26), rng.uniform(0.6, 1.2))
               for _ in range(26)]

# Cezve geometrisi
CX = 540
RIM_Y = 1430          # ağız (rim) yüksekliği
NECK_HW = 150         # ağız yarı genişliği
BASE_Y = 1760
BASE_HW = 215


def cezve_poly():
    # ağız → hafif boğaz → şişkin gövde → taban
    pts_r = [(NECK_HW + 18, RIM_Y), (NECK_HW, RIM_Y + 45), (NECK_HW - 8, RIM_Y + 90),
             (BASE_HW, BASE_Y - 120), (BASE_HW + 5, BASE_Y - 40), (BASE_HW - 10, BASE_Y)]
    right = [(CX + x, y) for x, y in pts_r]
    left = [(CX - x, y) for x, y in reversed(pts_r)]
    return right + left


def draw_flame(d, t, intensity):
    if intensity <= 0:
        return
    for i in range(7):
        x = CX - 180 + i * 60
        flick = 0.75 + 0.25 * math.sin(t * 14 + i * 1.7)
        h = (50 + 60 * intensity) * flick
        w = 22
        d.polygon([(x - w, BASE_Y + 75), (x, BASE_Y + 75 - h), (x + w, BASE_Y + 75)],
                  fill=(60, 120, 255))
        d.polygon([(x - w * 0.5, BASE_Y + 75), (x, BASE_Y + 75 - h * 0.55), (x + w * 0.5, BASE_Y + 75)],
                  fill=(170, 210, 255))
    # ocak ızgarası
    d.rounded_rectangle((CX - 280, BASE_Y + 75, CX + 280, BASE_Y + 95), 8, fill=(45, 40, 38))


def draw_foam(d, t, level, collapsing=0.0):
    """level 0..1 : ağzın üstünde köpük kubbesi."""
    if level <= 0.02:
        # sadece yüzey
        d.ellipse((CX - NECK_HW, RIM_Y - 16, CX + NECK_HW, RIM_Y + 16), fill=(70, 40, 22))
        return
    dome_h = 30 + 230 * level
    hw = NECK_HW + 6 + 20 * level
    # ana kubbe gövdesi
    d.chord((CX - hw, RIM_Y - dome_h, CX + hw, RIM_Y + dome_h * 0.35), 180, 360, fill=FOAM)
    d.rectangle((CX - hw, RIM_Y - 2, CX + hw, RIM_Y + 6), fill=FOAM)
    # kabarcıklar
    for bx, by, r, ph in FOAM_BUBBLES:
        # kubbe içinde konum
        x = CX + bx * hw * 0.92
        top = RIM_Y - dome_h * math.sqrt(max(0.0, 1 - bx * bx)) * 0.95
        y = lerp(RIM_Y, top, by)
        if y > RIM_Y - 4:
            continue
        rr = r * (0.55 + 0.45 * level) * (0.9 + 0.1 * math.sin(t * 3 + ph))
        if collapsing and (ph * 0.16) < collapsing:
            continue  # patlamış
        col = FOAM_L if (ph % 1) > 0.45 else mix(FOAM, FOAM_L, 0.4)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=(150, 105, 70), width=2, fill=col)
        d.ellipse((x - rr * 0.45, y - rr * 0.55, x - rr * 0.1, y - rr * 0.2), fill=(250, 232, 205))


def draw_cezve(img, t, foam_level, flame, collapsing=0.0, highlight_neck=0.0):
    d = ImageDraw.Draw(img)
    draw_flame(d, t, flame)
    # sap
    d.polygon([(CX + NECK_HW + 5, RIM_Y + 60), (CX + 470, RIM_Y - 10),
               (CX + 485, RIM_Y + 18), (CX + NECK_HW + 15, RIM_Y + 105)], fill=COPPER_D)
    d.rounded_rectangle((CX + 400, RIM_Y - 30, CX + 520, RIM_Y + 10), 18, fill=(70, 38, 18))
    # gövde
    d.polygon(cezve_poly(), fill=COPPER)
    # parlama
    d.polygon([(CX - 120, RIM_Y + 110), (CX - 95, RIM_Y + 110), (CX - 150, BASE_Y - 60),
               (CX - 180, BASE_Y - 70)], fill=(214, 140, 80))
    # desen bandı
    d.line([(CX - 175, RIM_Y + 160), (CX + 175, RIM_Y + 160)], fill=COPPER_D, width=6)
    for i in range(-5, 6):
        x = CX + i * 30
        d.polygon([(x - 10, RIM_Y + 175), (x, RIM_Y + 195), (x + 10, RIM_Y + 175)], fill=COPPER_D)
    # ağız kenarı
    d.ellipse((CX - NECK_HW - 18, RIM_Y - 14, CX + NECK_HW + 18, RIM_Y + 14), outline=(225, 150, 90), width=6)
    # gaga
    d.polygon([(CX - NECK_HW - 18, RIM_Y), (CX - NECK_HW - 55, RIM_Y - 18), (CX - NECK_HW - 10, RIM_Y + 18)],
              fill=COPPER)
    draw_foam(d, t, foam_level, collapsing)
    if highlight_neck > 0:
        a = highlight_neck
        col = mix(DARK, GOLD, a)
        for side in (-1, 1):
            x0 = CX + side * 330
            x1 = CX + side * (NECK_HW + 40)
            y = RIM_Y + 40
            d.line([(x0, y), (x1, y)], fill=col, width=10)
            d.polygon([(x1, y - 26), (x1, y + 26), (x1 - side * 40, y)], fill=col)


def draw_text_block(img, sc_t, badge, title, body, hook=False):
    d = ImageDraw.Draw(img)
    y = 230
    if badge:
        a = ease(sc_t / 0.4)
        tw = d.textlength(badge, font=F_CHIP)
        x0 = 90 - (1 - a) * 60
        col = (200, 60, 45) if badge == "DİKKAT" else GOLD
        d.rounded_rectangle((x0, y, x0 + tw + 56, y + 70), 35, fill=mix(DARK, col, a))
        d.text((x0 + 28, y + 13), badge, font=F_CHIP, fill=mix(DARK, DARK, a))
        y += 110
    f = F_HOOK if hook else F_TITLE
    for i, line in enumerate(title.split("\n")):
        a = ease((sc_t - 0.15 - i * 0.18) / 0.5)
        if a <= 0:
            continue
        accent = hook and line == "NEDEN"
        col = mix(DARK, GOLD if accent else CREAM, a)
        lh = f.size + 22
        if hook:
            tw = d.textlength(line, font=f)
            d.text(((W - tw) / 2, y + (1 - a) * 50), line, font=f, fill=col)
        else:
            d.text((90 + (1 - a) * 80, y), line, font=f, fill=col)
        y += lh
    if body:
        y += 30
        words, lines, cur = body.replace("\n", " ").split(), [], ""
        for w_ in words:
            cand = (cur + " " + w_).strip()
            if d.textlength(cand, font=F_BODY) > W - 180:
                lines.append(cur)
                cur = w_
            else:
                cur = cand
        lines.append(cur)
        for i, line in enumerate(lines):
            a = ease((sc_t - 0.7 - i * 0.15) / 0.5)
            if a <= 0:
                continue
            d.text((90, y + (1 - a) * 30), line, font=F_BODY, fill=mix(DARK, (230, 212, 185), a))
            y += 68


# ---- inset (yuvarlak yakın çekim) çizimleri
INSET_C = (800, 1010)
INSET_R = 190


def inset_base(img, a):
    d = ImageDraw.Draw(img)
    cx, cy = INSET_C
    r = INSET_R * a
    d.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), fill=GOLD)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(40, 22, 13))
    return d, cx, cy, r


def inset_particles(img, sc_t, a):
    d, cx, cy, r = inset_base(img, a)
    br = r * 0.55
    d.ellipse((cx - br, cy - br, cx + br, cy + br), fill=(80, 55, 40), outline=FOAM_L, width=4)
    n = int(46 * ease((sc_t - 0.5) / 2.5))
    for i in range(n):
        ang = i / 46 * 6.283 + 0.2 * math.sin(i)
        rr = br + 4
        x, y = cx + rr * math.cos(ang), cy + rr * math.sin(ang)
        s = 9 + (i % 3) * 2
        d.ellipse((x - s, y - s, x + s, y + s), fill=(105, 60, 30))
    d.text((cx - 72, cy - 22), "hava", font=F_LABEL, fill=CREAM)


def inset_co2(img, sc_t, a):
    d, cx, cy, r = inset_base(img, a)
    for i, (bx, by, s, sp) in enumerate(CO2_BUBBLES[:10]):
        y = cy + r * 0.8 - ((by + sc_t * sp * 0.5) % 1.0) * r * 1.6
        x = cx + bx * r * 0.55
        s *= a * 1.4
        d.ellipse((x - s, y - s, x + s, y + s), outline=CREAM, width=3)
    d.text((cx - 70, cy - 45), "CO₂", font=font(FONT_B, 70), fill=GOLD)


def inset_thermo(img, sc_t, a):
    d, cx, cy, r = inset_base(img, a)
    tw, th = 34 * a, 230 * a
    d.rounded_rectangle((cx - tw, cy - th / 2 - 20, cx + tw, cy + th / 2), 30, fill=(230, 220, 205))
    d.ellipse((cx - tw * 1.7, cy + th / 2 - 30, cx + tw * 1.7, cy + th / 2 + 40), fill=(210, 70, 50))
    fill = ease(sc_t / 4.5) * 0.65
    top = cy + th / 2 - fill * th
    d.rounded_rectangle((cx - tw * 0.5, top, cx + tw * 0.5, cy + th / 2), 15, fill=(210, 70, 50))
    d.text((cx + 50, cy - 100), "yavaş", font=F_SMALL, fill=CREAM)
    d.text((cx + 50, cy - 55), "yavaş", font=F_SMALL, fill=mix(CREAM, DARK, 0.4))


def inset_film(img, sc_t, a):
    d, cx, cy, r = inset_base(img, a)
    br = r * 0.6
    d.ellipse((cx - br, cy - br, cx + br, cy + br), fill=(80, 55, 40))
    k = ease((sc_t - 0.5) / 2.0)
    for i in range(28):
        ang = i / 28 * 6.283 + sc_t * 0.3
        x0, y0 = cx + br * math.cos(ang), cy + br * math.sin(ang)
        x1, y1 = cx + (br + 30 * k) * math.cos(ang), cy + (br + 30 * k) * math.sin(ang)
        d.line([(x0, y0), (x1, y1)], fill=GOLD, width=5)
        d.ellipse((x0 - 8, y0 - 8, x0 + 8, y0 + 8), fill=FOAM_L)
    d.text((cx - 50, cy - 40), "yağ +", font=font(FONT_B, 30), fill=CREAM)
    d.text((cx - 62, cy + 2), "protein", font=font(FONT_B, 30), fill=CREAM)


def inset_boil(img, sc_t, a):
    d, cx, cy, r = inset_base(img, a)
    for i in range(7):
        ph = (sc_t * 1.6 + i * 0.37) % 1.0
        x = cx + (i - 3) * r * 0.22
        y = cy + r * 0.5 - ph * r * 0.9
        s = 14 + 30 * ph
        if ph > 0.8:
            for k in range(6):
                ang = k * 1.047
                d.line([(x + s * math.cos(ang), y + s * math.sin(ang)),
                        (x + (s + 18) * math.cos(ang), y + (s + 18) * math.sin(ang))], fill=CREAM, width=4)
        else:
            d.ellipse((x - s, y - s, x + s, y + s), outline=CREAM, width=3)
    k = ease((sc_t - 1.5) / 0.5)
    if k > 0:
        L = r * 0.75 * k
        d.line([(cx - L, cy - L), (cx + L, cy + L)], fill=(220, 60, 45), width=22)
        d.line([(cx + L, cy - L), (cx - L, cy + L)], fill=(220, 60, 45), width=22)


INSETS = {"particles": inset_particles, "co2": inset_co2, "thermo": inset_thermo,
          "film": inset_film, "boil": inset_boil}


def draw_outro(img, sc_t):
    d = ImageDraw.Draw(img)
    y = 640
    for i, tip in enumerate(OUTRO_TIPS):
        a = ease((sc_t - 0.8 - i * 0.35) / 0.4)
        if a <= 0:
            continue
        x = 110 + (1 - a) * 80
        d.ellipse((x, y + 8, x + 44, y + 52), fill=mix(DARK, GOLD, a))
        d.line([(x + 10, y + 30), (x + 20, y + 41), (x + 35, y + 18)], fill=DARK, width=6)
        d.text((x + 70, y), tip, font=F_BODY, fill=mix(DARK, CREAM, a))
        y += 92
    a = ease((sc_t - 3.2) / 0.5)
    if a > 0:
        msg = "Kaydet • Paylaş • Afiyet olsun ☕"
        f = font(FONT_B, 46)
        tw = d.textlength(msg, font=f)
        d.text(((W - tw) / 2, 1130), msg, font=f, fill=mix(DARK, GOLD, a))


def foam_level_at(t):
    """Sahne hedeflerine yumuşak geçişli köpük seviyesi (+ çöküş)."""
    for i, s in enumerate(SCENES):
        if starts[i] <= t < starts[i] + s[0] or i == len(SCENES) - 1:
            break
    sc_t = t - starts[i]
    prev = SCENES[i - 1][4] if i > 0 else 0.0
    prev = 1.0 if prev < 0 else prev
    target = SCENES[i][4]
    if target < 0:  # kaynama sahnesi: önce taşar, sonra söner
        lvl = 1.15 if sc_t < 1.2 else lerp(1.15, 0.05, ease((sc_t - 1.2) / 1.5))
        collapse = ease((sc_t - 1.0) / 2.0)
        return lvl, collapse, i, sc_t
    if i == len(SCENES) - 1:
        prev = 0.05
    return lerp(prev, target, ease(sc_t / 1.5)), 0.0, i, sc_t


def render_frame(n):
    t = n / FPS
    img = BG.copy()
    level, collapse, i, sc_t = foam_level_at(t)
    dur, badge, title, body, _, flame, kind = SCENES[i]
    # sahne çıkış solması
    out_a = 1 - ease((sc_t - (dur - 0.35)) / 0.35) if i < len(SCENES) - 1 else 1.0

    neck = ease((sc_t - 1.0) / 0.6) * (0.75 + 0.25 * math.sin(t * 6)) if kind == "neck" else 0
    shake = 4 * math.sin(t * 50) if kind == "boil" and sc_t < 1.6 else 0
    flame_now = flame * (0.85 + 0.15 * math.sin(t * 2))
    layer = Image.new("RGB", (W, H))
    layer.paste(BG)
    draw_cezve(layer, t, level, flame_now, collapse, neck)
    if shake:
        layer = layer.transform(layer.size, Image.AFFINE, (1, 0, shake, 0, 1, 0))
    img = layer

    # yükselen CO2 kabarcıkları (2. sahne ve kanca)
    if kind in ("co2", "hook"):
        d = ImageDraw.Draw(img)
        for bx, by, s, sp in CO2_BUBBLES:
            p = (by + sc_t * sp * 0.35) % 1.0
            y = RIM_Y - 120 - p * 520
            x = CX + bx * 200 + 18 * math.sin(t * 2 + by * 9)
            alpha = min(1, p * 4) * (1 - p)
            d.ellipse((x - s, y - s, x + s, y + s), outline=mix(DARK, CREAM, alpha), width=3)
            if kind == "co2" and s > 22:
                d.text((x - 22, y - 14), "CO₂", font=font(FONT_B, 22), fill=mix(DARK, GOLD, alpha))

    if kind in INSETS:
        a = ease((sc_t - 0.6) / 0.5)
        if a > 0:
            INSETS[kind](img, sc_t, a)
    draw_text_block(img, sc_t, badge, title, body, hook=(kind == "hook"))
    if kind == "outro":
        draw_outro(img, sc_t)

    # ilerleme çubuğu
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((90, 120, W - 90, 132), 6, fill=(70, 45, 30))
    d.rounded_rectangle((90, 120, 90 + (W - 180) * (t / TOTAL), 132), 6, fill=GOLD)

    if out_a < 1:
        img = Image.blend(Image.new("RGB", (W, H), DARK), img, 0.35 + 0.65 * out_a)
    if t < 0.3:
        img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, t / 0.3)
    return img


# ---------------------------------------------------------------- ses
def make_audio(path, sr=44100):
    n = int(TOTAL * sr)
    tt = np.arange(n) / sr
    out = np.zeros(n)
    # sıcak pad: Am - F - C - G döngüsü
    chords = [[220, 261.6, 329.6], [174.6, 220, 261.6], [196, 261.6, 329.6], [196, 246.9, 293.7]]
    seg = 4.0
    for k in range(int(TOTAL / seg) + 1):
        a, b = int(k * seg * sr), min(n, int((k + 1) * seg * sr))
        if a >= n:
            break
        loc = tt[a:b] - k * seg
        env = np.minimum(1, loc / 0.8) * np.minimum(1, (seg - loc) / 0.8)
        for f in chords[k % 4]:
            out[a:b] += 0.05 * env * (np.sin(2 * np.pi * f * loc) + 0.3 * np.sin(2 * np.pi * f * 2 * loc))
    # kabarcık "blop" sesleri, köpük seviyesine göre yoğunlaşır
    r = np.random.default_rng(7)
    tcur = 0.3
    while tcur < TOTAL - 0.5:
        lvl, col, _, _ = foam_level_at(tcur)
        rate = 2 + 10 * max(lvl, 0) + (14 if col > 0 else 0)
        tcur += r.exponential(1 / rate)
        i0 = int(tcur * sr)
        L = int(0.06 * sr)
        if i0 + L >= n:
            break
        lt = np.arange(L) / sr
        f0 = r.uniform(500, 1400)
        sweep = f0 * (1 + 3 * lt / 0.06)
        out[i0:i0 + L] += 0.06 * np.exp(-lt * 60) * np.sin(2 * np.pi * np.cumsum(sweep) / sr)
    fade = np.minimum(1, tt / 0.5) * np.minimum(1, (TOTAL - tt) / 1.2)
    out = out * fade / max(1e-6, np.abs(out).max()) * 0.8
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
        env = np.convolve(np.abs(voice), np.ones(int(0.3 * sr)) / int(0.3 * sr), mode="same")
        duck = 1 - 0.7 * np.clip(env * 12, 0, 1)
        out = out * 0.45 * duck + voice * 0.95
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
    print("hazır:", OUT)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        for sec in [1.5, 6.5, 11.5, 16.5, 21.5, 26.5, 31.0, 36.0]:
            render_frame(int(sec * FPS)).resize((540, 960)).save(f"/tmp/claude-0/-home-user-Sezer/8d7ac713-b2f5-5fe2-b012-387b4c12d85b/scratchpad/prev_{sec}.png")
    else:
        main()
