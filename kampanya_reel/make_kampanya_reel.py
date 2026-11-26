#!/usr/bin/env python3
"""Kasım kampanyaları — araba / ev & dükkan taksit aralıkları reels'i.

Görsel ve ses yardımcıları ../firsat_reel/make_firsat_reel.py'den alınır.
Kullanım:  python3 make_kampanya_reel.py            (video)
           python3 make_kampanya_reel.py --still 5 12 (test kareleri)
           python3 make_kampanya_reel.py --kapak      (kapak resmi)
"""
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "firsat_reel"))
import make_firsat_reel as R  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

W, H, FPS = R.W, R.H, R.FPS
text, card, rrect, put = R.text, R.card, R.rrect, R.put
clamp, ease_out, ease_io, back_out, prog = R.clamp, R.ease_out, R.ease_io, R.back_out, R.prog
F_BLACK, F_BOLD, F_SEMI = R.F_BLACK, R.F_BOLD, R.F_SEMI
NAVY, TURQ, SKY, SUN, CORAL, SAND, WHITE, MUTED, CARD = (
    R.NAVY, R.TURQ, R.SKY, R.SUN, R.CORAL, R.SAND, R.WHITE, R.MUTED, R.CARD)

OUT = HERE / "kasim_kampanyalari_taksit_reel.mp4"

# ------------------------------------------------------------------ veri
URUNLER = [  # (kategori, ikon, fiyat, en düşük, en yüksek)
    ("araba", "araba", 800_000, 8_000, 53_333),
    ("araba", "araba", 1_500_000, 15_000, 100_000),
    ("ev", "ev", 2_500_000, 10_416, 166_667),
    ("ev", "ev", 4_000_000, 16_667, 266_667),
]


def tl(n):
    return f"{n:,.0f}".replace(",", ".") + " ₺"


def fiyat_kisa(n):
    if n >= 1_000_000:
        v = n / 1_000_000
        s = f"{v:.1f}".replace(".", ",").replace(",0", "")
        return f"{s} Milyon ₺"
    return tl(n)


# ------------------------------------------------------------------ zamanlama
BASE = [("hook", 5.0), ("u0", 7.0), ("u1", 6.0), ("u2", 8.0), ("u3", 8.0),
        ("ozet", 6.0), ("cta", 6.0)]
VOICE_DIR = HERE / "voice"
VOICE_DELAY, VOICE_TAIL = 0.4, 0.9
VOICES = {}
for _i in range(len(BASE)):
    _f = VOICE_DIR / f"{_i}.mp3"
    if _f.exists():
        VOICES[_i] = (_f, R.clip_len(_f))
S, _t = {}, 0.0
for _i, (_n, _d) in enumerate(BASE):
    if _i in VOICES:
        _d = max(_d, VOICE_DELAY + VOICES[_i][1] + VOICE_TAIL)
    if _i == len(BASE) - 1:
        _d += 1.5
    S[_n] = (round(_t, 3), round(_t + _d, 3))
    _t += _d
DUR = round(_t, 3)
CUTS = [v[0] for v in S.values()][1:]

# ürün sahnelerinde "en düşük" ve "en yüksek" sözcüklerinin geldiği an
# (sahne başından sn, ses gecikmesi dahil) — silencedetect ile ayarlanır
CUE = {"u0": (4.1, 5.4), "u1": (2.6, 4.0), "u2": (5.15, 7.1), "u3": (3.0, 5.35)}


def scene_alpha(t, name, fade=0.35):
    a, b = S[name]
    if t < a or t > b:
        return 0.0
    fin = 1.0 if a == 0 else clamp((t - a) / fade)
    fout = 1.0 if b >= DUR else clamp((b - t) / fade)
    return min(fin, fout)


def header(img, A):
    text(img, "KASIM KAMPANYALARI", W // 2, 240, F_BOLD(40), SUN, alpha=A)
    text(img, "taksitini sen belirle", W // 2, 290, F_SEMI(30), MUTED, alpha=A)


ICON_S = {k: R.icon_layer(k, 230) for k in ("ev", "araba", "dukkan")}
ICON_XS = {k: R.icon_layer(k, 80, col=NAVY, acc=WHITE) for k in ("ev", "araba", "dukkan")}


# ------------------------------------------------------------------ sahneler
def sc_hook(img, t, A):
    t0 = S["hook"][0]
    p = back_out(prog(t, t0 + 0.1, 0.6))
    text(img, "KASIM", W // 2, 470, F_BLACK(170), WHITE, alpha=A * clamp(p),
         scale=max(0.01, 0.7 + 0.3 * p))
    p2 = back_out(prog(t, t0 + 0.45, 0.6))
    text(img, "KAMPANYALARI", W // 2, 630, F_BLACK(116), SUN, alpha=A * clamp(p2),
         scale=max(0.01, 0.7 + 0.3 * p2))
    for i, ic in enumerate(["araba", "ev", "dukkan"]):
        x = W / 2 - 300 + i * 300
        q = back_out(prog(t, t0 + 1.4 + i * 0.35, 0.5))
        bob = 8 * math.sin((t - t0) * 3 + i) * clamp(q)
        card(img, x, 900 + bob, 250, 250, 50, CARD, A * 0.1 * clamp(q), scale=max(0.01, q))
        put(img, ICON_S[ic], x, 900 + bob, "mm", A * clamp(q), scale=max(0.01, q * 0.9))
    p3 = back_out(prog(t, t0 + 2.6, 0.6))
    pulse = 1 + 0.04 * math.sin((t - t0) * 7) * clamp(p3)
    sc = max(0.01, p3 * pulse)
    card(img, W / 2, 1180, 880, 160, 80, CORAL, A * clamp(p3), scale=sc)
    text(img, "TAKSİTİNİ SEN BELİRLE!", W // 2, 1180, F_BLACK(70), WHITE, alpha=A * clamp(p3), scale=sc)


def sc_urun(img, t, A, idx):
    name = f"u{idx}"
    t0 = S[name][0]
    lt = t - t0
    kat, ic, fiyat, lo, hi = URUNLER[idx]
    c_lo, c_hi = CUE[name]
    header(img, A)
    col = TURQ if kat == "araba" else SUN
    # kategori etiketi
    lab = "ARABA ALMAK İSTEYENLERE" if kat == "araba" else "EV & DÜKKAN ALMAK İSTEYENLERE"
    p = ease_out(prog(t, t0 + 0.1, 0.5))
    pw = 760 if kat == "araba" else 900
    card(img, W / 2, 410, pw, 96, 48, col, A * p)
    text(img, lab, W // 2 + 40, 410, F_BLACK(38 if kat == "araba" else 36), NAVY, alpha=A * p)
    put(img, ICON_XS[ic], W / 2 - pw / 2 + 64, 410, "mm", A * p)
    # sayfa göstergesi
    for k in range(4):
        x = W / 2 - 66 + k * 44
        card(img, x, 490, 28 if k == idx else 14, 14, 7, col if k == idx else WHITE,
             A * (1 if k == idx else 0.3))
    # büyük ikon + fiyat
    q = back_out(prog(t, t0 + 0.3, 0.6))
    if kat == "araba":
        put(img, ICON_S["araba"], W / 2, 640, "mm", A * clamp(q), scale=max(0.01, q))
    else:
        put(img, ICON_S["ev"], W / 2 - 130, 640, "mm", A * clamp(q), scale=max(0.01, q * 0.85))
        text(img, "&", W // 2, 650, F_BLACK(60), MUTED, alpha=A * clamp(q))
        put(img, ICON_S["dukkan"], W / 2 + 130, 640, "mm", A * clamp(q), scale=max(0.01, q * 0.85))
    p2 = back_out(prog(t, t0 + 0.8, 0.6))
    cnt = fiyat * ease_out(prog(t, t0 + 0.8, 1.0))
    text(img, tl(round(cnt / 1000) * 1000), W // 2, 840, F_BLACK(140), WHITE,
         alpha=A * clamp(p2), scale=max(0.01, 0.7 + 0.3 * p2))
    text(img, "araba için" if kat == "araba" else "ev & dükkan için", W // 2, 945,
         F_BOLD(50), SAND, alpha=A * clamp(p2))
    # kaydırma çubuğu: en düşük -> en yüksek, sonra "sen seç" salınımı
    x0, x1, y = 150, 930, 1135
    pt = ease_out(prog(t, t0 + c_lo - 0.5, 0.5))
    rrect(img, (x0, y - 12, x1, y + 12), 12, (255, 255, 255), A * 0.15 * pt)
    if lt < c_hi:
        f = 0.0
    elif lt < c_hi + 0.9:
        f = ease_io((lt - c_hi) / 0.9)
    else:
        f = 0.5 + 0.5 * math.cos((lt - c_hi - 0.9) * 1.1)  # 1 -> 0 -> 1 ... (sen seç)
    kx = x0 + (x1 - x0) * f
    rrect(img, (x0, y - 12, kx, y + 12), 12, col, A * pt)
    card(img, kx, y, 56, 56, 28, WHITE, A * pt)
    card(img, kx, y, 30, 30, 15, col, A * pt)
    val = lo + (hi - lo) * f
    if 0.02 < f < 0.98:
        val = round(val / 100) * 100
    else:
        val = lo if f <= 0.02 else hi
    bx = min(max(kx, 210), W - 210)
    card(img, bx, y - 90, 360, 90, 28, NAVY, A * pt)
    card(img, bx, y - 90, 360, 90, 28, None, A * pt, outline=col, width=3)
    text(img, tl(val), bx, y - 92, F_BLACK(52), WHITE, alpha=A * pt)
    # en düşük / en yüksek kartları
    for j, (lbl, v, cue, cc) in enumerate([("EN DÜŞÜK", lo, c_lo, TURQ), ("EN YÜKSEK", hi, c_hi, SUN)]):
        q = back_out(prog(t, t0 + cue - 0.1, 0.5))
        x = W / 2 - 225 + j * 450
        a = A * clamp(q)
        sc = max(0.01, q)
        card(img, x, 1350, 420, 200, 40, CARD, a * 0.1, scale=sc)
        card(img, x, 1350, 420, 200, 40, None, a, scale=sc, outline=cc, width=4)
        text(img, lbl, x, 1295, F_BOLD(36), cc, alpha=a, scale=sc)
        text(img, tl(v), x, 1370, F_BLACK(68), WHITE, alpha=a, scale=sc)
    q = back_out(prog(t, t0 + c_hi + 0.6, 0.5))
    card(img, W / 2, 1535, 380, 84, 42, col, A * clamp(q), scale=max(0.01, q))
    text(img, "TAKSİTLE", W // 2, 1535, F_BLACK(46), NAVY, alpha=A * clamp(q), scale=max(0.01, q))


def sc_ozet(img, t, A):
    t0 = S["ozet"][0]
    header(img, A)
    p = ease_out(prog(t, t0 + 0.1, 0.5))
    text(img, "TAKSİT ARALIKLARI", W // 2, 430, F_BLACK(80), WHITE, alpha=A * p)
    text(img, "en düşük → en yüksek taksit", W // 2, 505, F_SEMI(36), SAND, alpha=A * p)
    vmax = 270_000
    x0, x1 = 110, 970
    for i, (kat, ic, fiyat, lo, hi) in enumerate(URUNLER):
        y = 640 + i * 220
        q = ease_out(prog(t, t0 + 0.5 + i * 0.35, 0.8))
        a = A * clamp(q * 2)
        col = TURQ if kat == "araba" else SUN
        put(img, R.icon_layer(ic, 70), x0 + 35, y, "mm", a)
        ad = "Araba" if kat == "araba" else "Ev & Dükkan"
        text(img, f"{fiyat_kisa(fiyat)} {ad}", x0 + 90, y, F_BOLD(40), WHITE, "lm", a)
        rrect(img, (x0, y + 60, x1, y + 76), 8, (255, 255, 255), a * 0.12)
        bl = x0 + (x1 - x0) * lo / vmax
        bh = x0 + (x1 - x0) * hi / vmax
        rrect(img, (bl, y + 52, bl + max(24, (bh - bl) * q), y + 84), 16, col, a)
        lo_s = f"en düşük {tl(lo)}   ·   "
        text(img, lo_s, x0, y + 122, F_SEMI(32), MUTED, "lm", a)
        lw = R.text_layer(lo_s, F_SEMI(32), MUTED).width
        text(img, f"en yüksek {tl(hi)}", x0 + lw, y + 120, F_BLACK(36), col, "lm",
             a * clamp(q * 2 - 1))
    p2 = ease_out(prog(t, t0 + 2.4, 0.5))
    text(img, "Bütçene uygun olanı sen seç!", W // 2, 1560, F_BOLD(46), SAND, alpha=A * p2)


def sc_cta(img, t, A):
    t0 = S["cta"][0]
    lt = t - t0
    header(img, A)
    p = ease_out(prog(t, t0 + 0.1, 0.5))
    text(img, "Kendi ödemeni", W // 2, 560, F_BOLD(64), SAND, alpha=A * p)
    p2 = back_out(prog(t, t0 + 0.4, 0.6))
    text(img, "BELİRLE!", W // 2, 700, F_BLACK(160), WHITE, alpha=A * clamp(p2),
         scale=max(0.01, 0.7 + 0.3 * p2))
    p3 = ease_out(prog(t, t0 + 1.6, 0.5))
    text(img, "Teslimatını öğrenmek için", W // 2, 900, F_BOLD(54), WHITE, alpha=A * p3)
    p4 = back_out(prog(t, t0 + 2.4, 0.6))
    ring = (lt * 0.8) % 1.0
    card(img, W / 2, 1080, 800 + 120 * ring, 160 + 60 * ring, 110, None,
         A * clamp(p4) * (1 - ring) * 0.8, outline=TURQ, width=4)
    sc = max(0.01, p4 * (1 + 0.04 * math.sin(lt * 6) * clamp(p4)))
    card(img, W / 2, 1080, 800, 160, 80, TURQ, A * clamp(p4), scale=sc)
    text(img, "HEMEN İLETİŞİME GEÇ", W // 2, 1080, F_BLACK(60), NAVY, alpha=A * clamp(p4), scale=sc)
    if R.ILETISIM:
        text(img, R.ILETISIM, W // 2, 1220, F_BOLD(50), WHITE, alpha=A * clamp(p4))
    p5 = back_out(prog(t, t0 + 3.4, 0.6))
    card(img, W / 2, 1370, 700, 120, 60, CORAL, A * clamp(p5), scale=max(0.01, p5))
    text(img, "FIRSATLARI KAÇIRMA!", W // 2, 1370, F_BLACK(56), WHITE, alpha=A * clamp(p5),
         scale=max(0.01, p5))
    for i, ic in enumerate(["araba", "ev", "dukkan"]):
        q = ease_out(prog(t, t0 + 3.8 + i * 0.15, 0.4))
        put(img, R.icon_layer(ic, 110), W / 2 - 180 + i * 180, 1540, "mm", A * q)


SCENES = [("hook", sc_hook)] + [(f"u{i}", (lambda i: lambda img, t, A: sc_urun(img, t, A, i))(i))
                                 for i in range(4)] + [("ozet", sc_ozet), ("cta", sc_cta)]


def frame(t):
    img = R.BG.copy()
    R.waves(img, t)
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
    return img


def kapak():
    img = R.BG.copy()
    R.waves(img, 1.3)
    rays = Image.new("RGBA", (1600, 1600), (0, 0, 0, 0))
    d = ImageDraw.Draw(rays)
    for k in range(18):
        a0 = k * (2 * math.pi / 18) + 0.1
        d.polygon([(800, 800), (800 + 1100 * math.cos(a0), 800 + 1100 * math.sin(a0)),
                   (800 + 1100 * math.cos(a0 + 0.11), 800 + 1100 * math.sin(a0 + 0.11))],
                  fill=SUN + (16,))
    put(img, rays, W / 2, 600, "mm")
    text(img, "KASIM", W // 2, 360, F_BLACK(160), WHITE)
    text(img, "KAMPANYALARI", W // 2, 510, F_BLACK(116), SUN)
    card(img, W / 2, 670, 880, 140, 70, CORAL, 1.0)
    text(img, "TAKSİTİNİ SEN BELİRLE!", W // 2, 670, F_BLACK(64), WHITE)
    for i, (kat, ic, fiyat, lo, hi) in enumerate(URUNLER):
        y = 850 + i * 190
        col = TURQ if kat == "araba" else SUN
        card(img, W / 2, y, 920, 165, 40, CARD, 0.1)
        rrect(img, (W / 2 - 460, y - 82, W / 2 - 448, y + 82), 6, col, 1.0)
        put(img, R.icon_layer(ic, 110), 160, y, "mm")
        ad = "ARABA" if kat == "araba" else "EV & DÜKKAN"
        text(img, fiyat_kisa(fiyat), 240, y - 30, F_BLACK(50), WHITE, "lm")
        text(img, ad, 240, y + 30, F_BOLD(34), col, "lm")
        text(img, f"{tl(lo)} – ", 920, y - 28, F_BOLD(36), MUTED, "rm")
        text(img, tl(hi), 920, y + 26, F_BLACK(46), col, "rm")
    text(img, "aylık taksit: en düşük – en yüksek", W // 2, 1615, F_SEMI(32), SAND)
    out = HERE / "kasim_kampanyalari_kapak.png"
    img.convert("RGB").save(out)
    img.convert("RGB").crop((0, 240, 1080, 1680)).save(HERE / "kasim_kampanyalari_kapak_3x4.jpg",
                                                        quality=92)
    print("yazıldı:", out)


def main():
    if "--kapak" in sys.argv:
        return kapak()
    if "--still" in sys.argv:
        for s in sys.argv[sys.argv.index("--still") + 1:]:
            frame(float(s)).convert("RGB").save(HERE / f"still_{s}.png")
        return
    # ses: firsat_reel'in müzik/miks fonksiyonunu bu reel'in zamanlamasıyla kullan
    R.S, R.DUR, R.CUTS, R.VOICES, R.BASE = S, DUR, CUTS, VOICES, BASE
    R.VOICE_DELAY = VOICE_DELAY
    wav = HERE / "_muzik.wav"
    R.make_audio(wav)
    nframes = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(OUT)],
        stdin=subprocess.PIPE)
    for i in range(nframes):
        ff.stdin.write(frame(i / FPS).convert("RGB").tobytes())
    ff.stdin.close()
    ff.wait()
    wav.unlink()
    print("yazıldı:", OUT, f"({DUR:.1f} sn)")


if __name__ == "__main__":
    main()
