#!/usr/bin/env python3
"""Kupa Ustası — 'Akdeniz'de şampiyonluk kupası bu hafta sahibini bulacak mı?'
9:16 dikey Reels (1080x1920, 30 fps).

Girdi : assets/voice.mp3 (ElevenLabs dış ses) + assets/1..5_*.png (sahne görselleri)
Çıktı : kupa_ustasi_reel.mp4

Kullanım:  python3 make_kupa_reel.py [--preview]
"""
import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

# ------------------------------------------------------------------ ayarlar
USTA_ADI = "KUPA USTASI"                       # ustanın/dükkânın adıyla değiştirilebilir
ALT_BASLIK = "Akdeniz Bölgesi · Şampiyonluk Kupası"

W, H, FPS = 1080, 1920, 30
HERE = Path(__file__).resolve().parent
A = HERE / "assets"
OUT = HERE / "kupa_ustasi_reel.mp4"

F_BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
F_XBOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
F_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

GOLD = (240, 190, 100)
GOLD_D = (176, 122, 40)
CREAM = (250, 238, 215)
DARK = (22, 13, 6)


def fnt(p, s):
    return ImageFont.truetype(p, s)


VO = 0.30            # dış sesin videodaki başlangıcı (sn)
TAIL = 2.6           # sesten sonra kapanış kartı süresi

# Ön plan çerçevesi (4:5) — Instagram arayüzünün altında kalmasın diye yukarıda
FG_Y, FG_W, FG_H = 200, 1080, 1350

# ------------------------------------------------------------------ sahneler
# (başlangıç sn, görsel, odak x başlangıç→bitiş (0..1), zoom başlangıç→bitiş, adım etiketi)
SCENES = [
    (0.00, "1_kupa_tozlu.png", (0.50, 0.50), (1.00, 1.16), ""),
    (8.95, "2_kulp.png", (0.48, 0.56), (1.08, 1.00), "1 · KULP DÜZELTME"),
    (11.15, "3_lehim.png", (0.40, 0.48), (1.00, 1.10), "2 · LEHİM"),
    (13.74, "4_cila.png", (0.52, 0.45), (1.10, 1.00), "3 · ZIMPARA & CİLA"),
    (17.54, "5_parlak.png", (0.50, 0.50), (1.00, 1.14), ""),
    (24.45, "AFTER", None, None, ""),       # önce / sonra kapanışı
]
XFADE = 0.28

# Altyazılar (video zamanı). *yıldızlı* kelimeler altın renkte.
SUBS = [
    (4.47, 7.41, "Ama kupa sahaya çıkmadan önce, bir durağı daha var:"),
    (7.67, 8.95, "*ustanın tezgâhı.*"),
    (8.95, 11.15, "Ezilen kulplar *tek tek* düzeltiliyor."),
    (11.15, 13.74, "Çatlayan ek yerleri, sabırla *lehimleniyor.*"),
    (13.74, 17.54, "Sonra zımpara... cila... ve saatlerce süren *el emeği.*"),
    (17.54, 21.10, "İşte karşınızda: *ilk günkü gibi* parlayan şampiyonluk kupası."),
    (21.35, 23.00, "Peki bu kupayı *kim kaldıracak?*"),
    (24.50, 25.90, "*Tahminini* yorumlara yaz."),
    (26.06, 30.40, "Kupan hangi hâlde olursa olsun, *ustaya getir;* şampiyonlar gibi parlasın."),
]


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return float(r.stdout.strip())


VOICE_LEN = dur(A / "voice.mp3")
TOTAL = round(VO + VOICE_LEN + TAIL, 2)
NFRAMES = int(TOTAL * FPS)


# ------------------------------------------------------------------ yardımcılar
def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def load(name):
    return Image.open(A / name).convert("RGB")


IMGS = {s[1]: load(s[1]) for s in SCENES if s[1] != "AFTER"}


def make_bg(img):
    """Görseli dikeye büyüt, bulanıklaştır, karart."""
    s = H / img.height
    big = img.resize((int(img.width * s), H), Image.BICUBIC)
    x0 = (big.width - W) // 2
    big = big.crop((x0, 0, x0 + W, H)).filter(ImageFilter.GaussianBlur(38))
    big = ImageEnhance.Brightness(big).enhance(0.40)
    # alttan/üstten koyu gradyan
    g = np.linspace(0, 1, H)
    shade = (0.55 + 0.45 * (1 - np.abs(g - 0.45) * 1.6).clip(0, 1))[:, None, None]
    arr = (np.asarray(big).astype(np.float32) * shade).clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr)


BGS = {k: make_bg(v) for k, v in IMGS.items()}

# yuvarlak köşeli ön plan maskesi
FG_MASK = Image.new("L", (FG_W - 60, FG_H), 0)
ImageDraw.Draw(FG_MASK).rounded_rectangle((0, 0, FG_W - 61, FG_H - 1), 44, fill=255)
FG_W_IN = FG_W - 60   # kenarlardan 30 px boşluk


def fg_frame(img, fx, zoom):
    """Yatay görselden 4:5 pencere kırp (odak fx, zoom)."""
    ar = FG_W_IN / FG_H
    ch = img.height / zoom
    cw = ch * ar
    cx = fx * img.width
    cx = min(max(cx, cw / 2), img.width - cw / 2)
    cy = img.height / 2
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return img.resize((FG_W_IN, FG_H), Image.BICUBIC, box=box)


def scene_at(t):
    idx = 0
    for i, s in enumerate(SCENES):
        if t >= s[0]:
            idx = i
    return idx


def scene_end(i):
    return SCENES[i + 1][0] if i + 1 < len(SCENES) else TOTAL


# ----- önce / sonra kapanış paneli
def after_panel():
    pw, ph = FG_W_IN, FG_H
    panel = Image.new("RGB", (pw, ph), DARK)
    half = (ph - 16) // 2
    for k, (name, label, fx) in enumerate([("1_kupa_tozlu.png", "ÖNCE", 0.5),
                                           ("5_parlak.png", "SONRA", 0.5)]):
        im = IMGS[name]
        ar = pw / half
        cw = im.width * 0.78
        ch = cw / ar
        if ch > im.height:
            ch = im.height
            cw = ch * ar
        cx, cy = fx * im.width, im.height * (0.46 if k == 0 else 0.42)
        cy = min(max(cy, ch / 2), im.height - ch / 2)
        crop = im.resize((pw, half), Image.BICUBIC,
                         box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
        if k == 0:
            crop = ImageEnhance.Color(crop).enhance(0.55)
        panel.paste(crop, (0, k * (half + 16)))
        d = ImageDraw.Draw(panel)
        f = fnt(F_BLACK, 46)
        tw = d.textlength(label, font=f)
        y = k * (half + 16) + 28
        col = (90, 90, 90) if k == 0 else GOLD
        d.rounded_rectangle((28, y, 28 + tw + 56, y + 74), 37, fill=col)
        d.text((56, y + 10), label, font=f, fill=CREAM if k == 0 else DARK)
    d = ImageDraw.Draw(panel)
    d.rectangle((0, half, pw, half + 16), fill=GOLD)
    return panel


AFTER = after_panel()
AFTER_BG = BGS["5_parlak.png"]


# ------------------------------------------------------------------ metin çizimi
def rich_tokens(text):
    out, gold = [], False
    for part in text.split("*"):
        for w in part.split():
            out.append((w, gold))
        gold = not gold
    return out


F_SUB = fnt(F_XBOLD, 56)


def draw_subtitle(img, text, a, y_center=1450):
    if a <= 0:
        return img
    d0 = ImageDraw.Draw(img)
    toks = rich_tokens(text)
    maxw = W - 170
    lines, cur, cw = [], [], 0
    sp = d0.textlength(" ", font=F_SUB)
    for w, g in toks:
        ww = d0.textlength(w, font=F_SUB)
        if cur and cw + sp + ww > maxw:
            lines.append((cur, cw))
            cur, cw = [], 0
        cw = cw + (sp if cur else 0) + ww
        cur.append((w, g, ww))
    if cur:
        lines.append((cur, cw))
    lh = 72
    bw = max(l[1] for l in lines) + 76
    bh = len(lines) * lh + 44
    x0 = (W - bw) / 2
    y0 = y_center - bh / 2 + (1 - ease_out(a)) * 24
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x0 + 6, y0 + 10, x0 + bw + 6, y0 + bh + 10), 30,
                                         fill=(0, 0, 0, int(120 * a)))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    layer = Image.alpha_composite(layer, sh)
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), 30, fill=(22, 13, 6, int(215 * a)),
                        outline=GOLD_D + (int(255 * a),), width=3)
    y = y0 + 20
    for words, lw in lines:
        x = (W - lw) / 2
        for w, g, ww in words:
            col = (GOLD if g else (255, 255, 255)) + (int(255 * a),)
            d.text((x, y), w, font=F_SUB, fill=col)
            x += ww + sp
        y += lh
    return Image.alpha_composite(img, layer)


def draw_big(img, lines, a, y_center, size=118, colors=None, stroke=8):
    """Kanca / soru gibi büyük, konturlu yazı. lines: [(metin, renk)]"""
    if a <= 0:
        return img
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    total = 0
    fonts = []
    for txt, col, sz in lines:
        f = fnt(F_BLACK, sz)
        fonts.append(f)
        total += sz * 1.12
    y = y_center - total / 2
    for i, ((txt, col, sz), f) in enumerate(zip(lines, fonts)):
        k = ease_out((a - i * 0.12) / 0.6) if a < 1 else 1
        if k <= 0:
            y += sz * 1.12
            continue
        tw = d.textlength(txt, font=f)
        scale_y = y + (1 - k) * 40
        d.text(((W - tw) / 2, scale_y), txt, font=f, fill=col + (int(255 * k),),
               stroke_width=stroke, stroke_fill=(15, 8, 3, int(235 * k)))
        y += sz * 1.12
    return Image.alpha_composite(img, layer)


def draw_chip(img, text, a, y, bg=GOLD, fg=DARK, size=40):
    if a <= 0:
        return img
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = fnt(F_BLACK, size)
    tw = d.textlength(text, font=f)
    pad = size * 0.8
    x0 = (W - tw) / 2 - pad
    x1 = (W + tw) / 2 + pad
    hgt = size * 1.75
    yy = y + (1 - ease_out(a)) * 20
    d.rounded_rectangle((x0, yy, x1, yy + hgt), hgt / 2, fill=bg + (int(240 * a),))
    d.text(((W - tw) / 2, yy + (hgt - size * 1.2) / 2), text, font=f, fill=fg + (int(255 * a),))
    return Image.alpha_composite(img, layer)


F_HEAD = fnt(F_SERIF, 50)
F_HEAD2 = fnt(F_BOLD, 30)


def draw_header(img, t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = ease(t / 0.5)
    tw = d.textlength(USTA_ADI, font=F_HEAD)
    d.text(((W - tw) / 2, 62), USTA_ADI, font=F_HEAD, fill=GOLD + (int(255 * a),),
           stroke_width=2, stroke_fill=(0, 0, 0, int(160 * a)))
    tw2 = d.textlength(ALT_BASLIK, font=F_HEAD2)
    d.text(((W - tw2) / 2, 128), ALT_BASLIK, font=F_HEAD2, fill=(255, 255, 255, int(225 * a)))
    # ince ilerleme çubuğu
    d.rounded_rectangle((60, 30, W - 60, 37), 4, fill=(255, 255, 255, 60))
    d.rounded_rectangle((60, 30, 60 + (W - 120) * min(1, t / TOTAL), 37), 4, fill=GOLD + (255,))
    return Image.alpha_composite(img, layer)


# altın toz / kıvılcım parçacıkları
RNG = np.random.default_rng(3)
DUST = RNG.uniform(0, 1, size=(70, 4))


def draw_dust(img, t, strength, warm=False):
    if strength <= 0:
        return img
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for px, py, ps, ph in DUST:
        y = FG_Y + FG_H * ((py - t * (0.03 + 0.05 * ps)) % 1.0)
        x = 30 + FG_W_IN * px + 14 * math.sin(t * 1.3 + ph * 6)
        r = 1.5 + 3.5 * ps
        tw = 0.5 + 0.5 * math.sin(t * 5 + ph * 20)
        col = (255, 170, 70) if warm else (255, 225, 160)
        d.ellipse((x - r, y - r, x + r, y + r), fill=col + (int(170 * strength * tw),))
    return Image.alpha_composite(img, layer)


def frame_base(i, t):
    """i. sahnenin arka plan + ön planını RGB olarak döndürür."""
    st, name, fxs, zs, _ = SCENES[i]
    en = scene_end(i)
    k = ease((t - st) / max(0.01, en - st))
    if name == "AFTER":
        bg = AFTER_BG.copy()
        fg = AFTER
        pop = ease_out((t - st) / 0.5)
        s = 0.92 + 0.08 * pop
        fg = fg.resize((int(FG_W_IN * s), int(FG_H * s)), Image.BICUBIC)
        mask = FG_MASK.resize(fg.size)
        bg.paste(fg, ((W - fg.width) // 2, FG_Y + (FG_H - fg.height) // 2), mask)
        return bg, 1.0
    img = IMGS[name]
    fx = fxs[0] + (fxs[1] - fxs[0]) * k
    z = zs[0] + (zs[1] - zs[0]) * k
    bg = BGS[name].copy()
    fg = fg_frame(img, fx, z)
    bg.paste(fg, (30, FG_Y), FG_MASK)
    return bg, 1.0


BORDER = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(BORDER).rounded_rectangle((30, FG_Y, 30 + FG_W_IN - 1, FG_Y + FG_H - 1), 44,
                                         outline=GOLD_D + (200,), width=3)


def render_frame(n):
    t = n / FPS
    i = scene_at(t)
    base, _ = frame_base(i, t)
    # sahne geçişi (çapraz geçiş)
    st = SCENES[i][0]
    if i > 0 and t - st < XFADE:
        prev, _ = frame_base(i - 1, t)
        base = Image.blend(prev, base, ease((t - st) / XFADE))
    img = base.convert("RGBA")
    img = Image.alpha_composite(img, BORDER)

    name = SCENES[i][1]
    if name == "1_kupa_tozlu.png":
        img = draw_dust(img, t, 0.9)
    elif name == "3_lehim.png":
        img = draw_dust(img, t * 2.5, 0.8, warm=True)
    elif name == "5_parlak.png":
        img = draw_dust(img, t, 1.0)

    # parlama flaşı ("İşte karşınızda")
    fl = 17.54
    if fl - 0.05 <= t < fl + 0.7:
        a = (1 - ease((t - fl) / 0.7)) * 0.85
        img = Image.alpha_composite(img, Image.new("RGBA", (W, H), (255, 236, 190, int(255 * a))))

    # adım etiketi
    label = SCENES[i][4]
    if label:
        a = ease_out((t - st) / 0.35) * (1 - ease((t - (scene_end(i) - 0.25)) / 0.25))
        img = draw_chip(img, label, a, FG_Y + 40, size=38)

    # KANCA (0 – 4.3 sn)
    if t < 4.35:
        a_in = min(1.0, (t - 0.15) / 0.9)
        a_out = 1 - ease((t - 4.0) / 0.35)
        if a_in > 0:
            img = draw_chip(img, "AKDENİZ BÖLGESİ", min(1, a_in * 1.5) * a_out, 560,
                            bg=(200, 40, 35), fg=(255, 255, 255), size=40)
            img = draw_big(img, [("ŞAMPİYONLUK", GOLD, 112),
                                 ("KUPASI", GOLD, 150),
                                 ("BU HAFTA", (255, 255, 255), 104),
                                 ("SAHİBİNİ", (255, 255, 255), 104),
                                 ("BULACAK MI?", (255, 255, 255), 104)],
                           a_in * a_out if a_in >= 1 else a_in * a_out, 1020)

    # SORU (21.3 – 24.45)
    if 21.3 <= t < 24.45:
        a_in = min(1.0, (t - 21.3) / 0.7)
        a_out = 1 - ease((t - 24.15) / 0.3)
        img = draw_big(img, [("KAZANAN", (255, 255, 255), 132),
                             ("KİM", GOLD, 190),
                             ("OLACAK?", GOLD, 150)], a_in * a_out, 830)

    # altyazılar
    for s0, s1, txt in SUBS:
        if s0 - 0.05 <= t < s1:
            a = ease((t - s0) / 0.18) * (1 - ease((t - (s1 - 0.12)) / 0.12))
            img = draw_subtitle(img, txt, a)

    # kapanış çağrısı
    if t >= 24.45:
        a = ease_out((t - 24.6) / 0.5)
        img = draw_chip(img, "TAHMİNİNİ YORUMLARA YAZ  ↓", a, 1590, size=40)
    if t >= 30.3:
        a = ease_out((t - 30.3) / 0.45)
        img = draw_chip(img, "KUPAN DA PARLASIN · USTAYA GETİR", a, 1360,
                        bg=(255, 255, 255), fg=DARK, size=40)

    img = draw_header(img, t)
    out = img.convert("RGB")
    # giriş / çıkış karartması
    if t < 0.25:
        out = Image.blend(Image.new("RGB", (W, H)), out, t / 0.25)
    if t > TOTAL - 0.4:
        out = Image.blend(Image.new("RGB", (W, H)), out, max(0, (TOTAL - t) / 0.4))
    return out


# ------------------------------------------------------------------ ses
SR = 44100


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def make_audio(path):
    n = int(TOTAL * SR)
    tt = np.arange(n) / SR
    rng = np.random.default_rng(11)
    music = np.zeros(n)

    # 1) Sinematik altlık: Re minör drone + yavaş nabız, finalde majöre açılır
    def tone(f, amp, t0, t1, attack=1.5, release=1.5):
        a, b = int(t0 * SR), min(n, int(t1 * SR))
        lt = tt[a:b] - t0
        env = np.minimum(1, lt / attack) * np.minimum(1, (t1 - t0 - lt) / release).clip(0, 1)
        music[a:b] += amp * env * (np.sin(2 * np.pi * f * lt) + 0.25 * np.sin(2 * np.pi * 2 * f * lt))

    for f in (73.42, 110.0, 146.83, 174.61):           # Dm
        tone(f, 0.05, 0.0, 17.8, 1.2, 0.6)
    for f in (73.42, 110.0, 146.83, 185.0, 220.0):    # D majör — kupa parladığında
        tone(f, 0.05, 17.4, 24.6, 0.3, 1.0)
    for f in (58.27, 116.54, 146.83, 174.61):         # Bb — soru
        tone(f, 0.045, 21.2, 24.8, 0.5, 0.6)
    for f in (73.42, 110.0, 146.83, 185.0, 220.0, 293.66):
        tone(f, 0.045, 24.4, TOTAL, 0.8, 1.6)

    # nabız (kick) – her 0.75 sn, gerilim için
    def kick(t0, amp=0.5):
        i0 = int(t0 * SR)
        L = int(0.35 * SR)
        if i0 + L >= n:
            return
        lt = np.arange(L) / SR
        f = 45 + 70 * np.exp(-lt * 25)
        music[i0:i0 + L] += amp * np.exp(-lt * 9) * np.sin(2 * np.pi * np.cumsum(f) / SR)

    tk = 0.3
    while tk < TOTAL - 2.5:
        if not (17.4 < tk < 17.9):
            kick(tk, 0.42 if tk < 17.5 else 0.32)
        tk += 0.75

    # 2) Efektler
    sfx = np.zeros(n)

    def clink(t0, amp=0.35):
        i0 = int(t0 * SR)
        L = int(0.9 * SR)
        lt = np.arange(L) / SR
        s = np.zeros(L)
        for f, d in ((1870, 7), (2950, 9), (4410, 12), (5230, 15)):
            s += np.sin(2 * np.pi * f * lt) * np.exp(-lt * d)
        s[:int(0.004 * SR)] += rng.normal(0, 1, int(0.004 * SR))
        e = min(n, i0 + L)
        sfx[i0:e] += amp * s[:e - i0] / 4

    for t0 in (9.25, 9.85, 10.45):                     # çekiç
        clink(t0, 0.55)

    def noise_band(t0, t1, lo, hi, amp, flutter=0.0):
        a, b = int(t0 * SR), min(n, int(t1 * SR))
        L = b - a
        x = rng.normal(0, 1, L)
        X = np.fft.rfft(x)
        fr = np.fft.rfftfreq(L, 1 / SR)
        X[(fr < lo) | (fr > hi)] = 0
        y = np.fft.irfft(X, L)
        y /= np.abs(y).max() + 1e-9
        lt = np.arange(L) / SR
        env = np.minimum(1, lt / 0.25) * np.minimum(1, (L / SR - lt) / 0.4)
        if flutter:
            env *= 0.75 + 0.25 * np.sin(2 * np.pi * flutter * lt)
        sfx[a:b] += amp * env * y

    noise_band(11.2, 13.7, 1500, 9000, 0.16, flutter=11)  # lehim alevi tıslaması
    noise_band(13.8, 17.4, 300, 2600, 0.13, flutter=23)   # cila çarkı vınlaması
    noise_band(21.1, 21.6, 200, 5000, 0.12)               # whoosh (soru)

    # parlama "ding" + ışıltı
    i0 = int(17.54 * SR)
    L = int(2.5 * SR)
    lt = np.arange(L) / SR
    ding = sum(np.sin(2 * np.pi * f * lt) * np.exp(-lt * d)
               for f, d in ((1318.5, 2.2), (1760.0, 2.6), (2637.0, 3.5), (3520.0, 4.5)))
    sfx[i0:i0 + L] += 0.18 * ding
    for k in range(14):
        t0 = 17.6 + k * 0.09 + rng.uniform(0, 0.04)
        j = int(t0 * SR)
        LL = int(0.25 * SR)
        l2 = np.arange(LL) / SR
        sfx[j:j + LL] += 0.05 * np.sin(2 * np.pi * rng.uniform(3000, 6000) * l2) * np.exp(-l2 * 18)

    # 3) Dış ses + ducking
    v = decode(A / "voice.mp3")
    voice = np.zeros(n)
    j = int(VO * SR)
    v = v[: n - j]
    voice[j:j + len(v)] = v
    voice /= np.abs(voice).max() + 1e-9
    env = np.convolve(np.abs(voice), np.ones(int(0.25 * SR)) / int(0.25 * SR), mode="same")
    duck = 1 - 0.65 * np.clip(env * 10, 0, 1)

    music /= np.abs(music).max() + 1e-9
    sfx /= np.abs(sfx).max() + 1e-9
    fade = np.minimum(1, tt / 0.4) * np.clip((TOTAL - tt) / 1.5, 0, 1)
    out = (music * 0.30 * duck + sfx * 0.32 * (0.55 + 0.45 * duck)) * fade + voice * 0.92
    out = np.clip(out, -1, 1)
    pcm = (out * 32767).astype(np.int16)
    st = np.stack([pcm, pcm], axis=1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())


def main():
    wav = HERE / "_mix.wav"
    make_audio(wav)
    tmp = OUT.with_name("_tmp_" + OUT.name)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
           "-shortest", "-movflags", "+faststart", str(tmp)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(NFRAMES):
        p.stdin.write(render_frame(k).tobytes())
        if k % 150 == 0:
            print(f"kare {k}/{NFRAMES}", flush=True)
    p.stdin.close()
    if p.wait() != 0:
        sys.exit("ffmpeg hata verdi")
    tmp.replace(OUT)
    wav.unlink(missing_ok=True)
    print("hazır:", OUT, f"({TOTAL:.1f} sn)")


if __name__ == "__main__":
    if "--preview" in sys.argv:
        outdir = Path(sys.argv[sys.argv.index("--preview") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        for sec in [2.5, 6.0, 9.8, 12.3, 15.5, 19.0, 22.5, 25.0, 31.0]:
            render_frame(int(sec * FPS)).resize((540, 960)).save(outdir / f"p_{sec:05.1f}.png")
    else:
        main()
