#!/usr/bin/env python3
"""Kasım fırsatları reels'i için kapak resmi (1080x1920).

Önemli içerik ortadaki 1080x1440 alanda tutulur; profil ızgarasında
(3:4) kırpıldığında da okunur.  Kullanım: python3 make_kapak.py
"""
import math
import random

from PIL import Image, ImageDraw

import make_firsat_reel as R

W, H = R.W, R.H
img = R.BG.copy()
R.waves(img, 1.3)

# arka planda ışınlar
rays = Image.new("RGBA", (1600, 1600), (0, 0, 0, 0))
d = ImageDraw.Draw(rays)
for k in range(18):
    a0 = k * (2 * math.pi / 18) + 0.1
    d.polygon([(800, 800), (800 + 1100 * math.cos(a0), 800 + 1100 * math.sin(a0)),
               (800 + 1100 * math.cos(a0 + 0.11), 800 + 1100 * math.sin(a0 + 0.11))],
              fill=R.SUN + (16,))
R.put(img, rays, W / 2, 640, "mm")

# konfeti (kenarlarda)
rng = random.Random(5)
d = ImageDraw.Draw(img)
for _ in range(70):
    x = rng.choice([rng.uniform(20, 190), rng.uniform(890, 1060)])
    y = rng.uniform(260, 1500)
    sz = rng.uniform(10, 20)
    col = rng.choice([R.TURQ, R.SKY, R.SUN, R.CORAL, R.SAND])
    ang = rng.uniform(0, math.pi)
    pts = [(x + sz * math.cos(ang + q) * (0.8 if i % 2 else 0.35),
            y + sz * math.sin(ang + q) * (0.8 if i % 2 else 0.35))
           for i, q in enumerate([0, math.pi / 2, math.pi, 3 * math.pi / 2])]
    d.polygon(pts, fill=col + (200,))

# başlık
R.text(img, "KASIM", W // 2, 370, R.F_BLACK(170), R.WHITE)
R.text(img, "FIRSATLARI", W // 2, 525, R.F_BLACK(140), R.SUN)
R.card(img, W / 2, 695, 760, 170, 85, R.CORAL, 1.0)
R.text(img, "SON 2 GÜN!", W // 2, 695, R.F_BLACK(104), R.WHITE)

# ikonlar
for i, ic in enumerate(["ev", "araba", "dukkan"]):
    x = W / 2 - 300 + i * 300
    R.card(img, x, 905, 240, 240, 48, R.CARD, 0.1)
    R.put(img, R.icon_layer(ic, 200), x, 905, "mm")

# 4 adım
R.text(img, "4 ADIMDA", W // 2, 1095, R.F_BLACK(110), R.WHITE)
R.text(img, "PLANINI YAP", W // 2, 1200, R.F_BLACK(84), R.TURQ)
labels = ["Ödeme\ngücü", "İhtiyaç\nbelirle", "Ödeme\nplanı", "Ödeme\ndüzeni"]
cols = [R.TURQ, R.SKY, R.SUN, R.CORAL]
for i in range(4):
    x = W / 2 - 330 + i * 220
    R.card(img, x, 1325, 96, 96, 48, cols[i], 1.0)
    R.text(img, str(i + 1), x, 1325, R.F_BLACK(54), R.NAVY)
    if i < 3:
        R.rrect(img, (x + 56, 1322, x + 164, 1328), 3, (255, 255, 255), 0.3)
    for j, ln in enumerate(labels[i].split("\n")):
        R.text(img, ln, x, 1400 + j * 38, R.F_BOLD(32), R.WHITE)

# bonus şeridi
R.card(img, W / 2, 1555, 900, 120, 60, R.CARD, 0.12)
R.card(img, 235, 1555, 210, 84, 42, R.SUN, 1.0)
R.text(img, "BONUS", 235, 1555, R.F_BLACK(44), R.NAVY)
R.text(img, "Rehin / İpotek masrafları", 360, 1537, R.F_BOLD(36), R.WHITE, "lm")
R.text(img, "BİZDEN!", 360, 1579, R.F_BLACK(38), R.SUN, "lm")

out = R.HERE / "kasim_firsatlari_kapak.png"
img.convert("RGB").save(out)
# 3:4 ızgara önizlemesi (ortadan kırpım)
img.convert("RGB").crop((0, 240, 1080, 1680)).save(R.HERE / "kasim_firsatlari_kapak_3x4.jpg", quality=92)
print("yazıldı:", out)
