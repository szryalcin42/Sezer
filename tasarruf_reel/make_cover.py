#!/usr/bin/env python3
"""Reels kapak resmi (1080x1920). Önemli içerik ortadaki 1080x1350 alanda
tutulur; profil ızgarasındaki kırpmada da okunur."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import make_reel as R

HERE = Path(__file__).resolve().parent
img = R.BG.copy()
d = ImageDraw.Draw(img)
W = R.W

# güvenli alan: y = 285 .. 1635
fb = R.font(R.FONT_B, 40)
tw = d.textlength("TASARRUF FİNANSMAN", font=fb)
d.rounded_rectangle((90, 330, 90 + tw + 64, 330 + 80), 40, fill=R.GREEN)
d.text((122, 347), "TASARRUF FİNANSMAN", font=fb, fill=R.NAVY)

f = R.font(R.FONT_B, 118)
y = 450
for line, col in (("FAİZSİZ", R.GREEN), ("EV SAHİBİ", R.WHITE), ("OLMAK", R.WHITE), ("MÜMKÜN MÜ?", R.GOLD)):
    d.text((90, y), line, font=f, fill=col)
    y += 138

# görsel: parlayan ev + üstü çizili yüzde + anahtar
glow = Image.new("L", img.size, 0)
ImageDraw.Draw(glow).ellipse((430, 1000, 1030, 1600), fill=120)
glow = glow.filter(ImageFilter.GaussianBlur(90))
img = Image.composite(Image.new("RGB", img.size, (40, 160, 130)), img, glow)
d = ImageDraw.Draw(img)
R.draw_house(d, 730, 1330, 1.55, R.WHITE, R.GREEN)

px, py = 120, 1150
d.text((px, py), "%", font=R.font(R.FONT_B, 230), fill=R.RED)
d.line([(px - 15, py + 260), (px + 215, py + 30)], fill=R.WHITE, width=20)

kx, ky = 260, 1520
d.ellipse((kx - 150, ky - 45, kx - 60, ky + 45), outline=R.GOLD, width=18)
d.rectangle((kx - 62, ky - 10, kx + 150, ky + 10), fill=R.GOLD)
d.rectangle((kx + 90, ky, kx + 108, ky + 45), fill=R.GOLD)
d.rectangle((kx + 125, ky, kx + 143, ky + 35), fill=R.GOLD)

R.ctext(d, 1700, "30 saniyede anlatıyoruz ▶", R.font(R.FONT_B, 46), R.WHITE)

out = HERE / "kapak.png"
img.save(out)

print("hazır:", out)
