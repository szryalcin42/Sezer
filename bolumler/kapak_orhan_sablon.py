# Orhan Gazi serisi kapak kalıbı: lacivert-altın, sivri kemer çerçeve, bölüm madalyonu.
# Kullanım: python3 kapak_orhan_sablon.py <kaynak.png> <çıktı.jpg> "<BAŞLIK>" "<1/5>"
import sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
F = '/usr/share/fonts/truetype/noto/'
def fnt(n, s): return ImageFont.truetype(F + n, s)
SRC, OUTP, TITLE, NUM = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
PADISAH, SIRA = 'ORHAN GAZİ', 'II. PADİŞAH'
LAPIS = (16, 32, 70); GOLD = (222, 182, 96); GOLD_D = (160, 120, 52); CREAM = (246, 236, 212)

# --- lacivert dokulu zemin
rng = np.random.default_rng(5)
base = np.ones((H, W, 3), np.float32) * np.array(LAPIS, np.float32)
nz = rng.normal(0, 1, (H // 6, W // 6)).astype(np.float32)
nz = np.array(Image.fromarray(((nz * 18) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) - 128
base += nz[..., None] * 0.35
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
base *= np.clip(1.15 - 0.6 * r, 0.45, 1.1)[..., None]
img = Image.fromarray(base.clip(0, 255).astype(np.uint8)).convert('RGBA')

# --- sivri kemer maskesi
X0, X1, YS, YB, R = 110, 970, 1005, 1190, 860
w = X1 - X0
cxL, cxR = X0 + R, X1 - R
def arch_poly(x0, x1, ys, yb, rr):
    pts = []
    cl, cr = x0 + rr, x1 - rr
    mid = (x0 + x1) / 2
    for i in range(0, 101):
        x = x0 + (mid - x0) * i / 100
        pts.append((x, ys - math.sqrt(max(rr * rr - (x - cl) ** 2, 0))))
    for i in range(0, 101):
        x = mid + (x1 - mid) * i / 100
        pts.append((x, ys - math.sqrt(max(rr * rr - (x - cr) ** 2, 0))))
    pts += [(x1, yb), (x0, yb)]
    return pts
APEX = YS - math.sqrt(R * R - (w / 2 - R) ** 2)
mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).polygon(arch_poly(X0, X1, YS, YB, R), fill=255)

# --- sahne görseli kemerin içine
src = Image.open(SRC).convert('RGB')
bw, bh = X1 - X0, int(YB - APEX)
s = max(bw / src.width, bh / src.height) * 1.08
src = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
ox, oy = (src.width - bw) // 2, (src.height - bh) // 2
src = src.crop((ox, oy, ox + bw, oy + bh))
a = np.asarray(src).astype(np.float32)
g = np.ones((bh, 1), np.float32); g[-220:, 0] = np.linspace(1, 0.55, 220)
a = (a * g[..., None]).clip(0, 255)
scene = Image.new('RGBA', (W, H), (0, 0, 0, 0)); scene.paste(Image.fromarray(a.astype(np.uint8)), (X0, int(APEX)))
# gölge
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(mask.point(lambda v: int(v * 0.75)))
img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)), (0, 12))
img.paste(scene, (0, 0), mask)

d = ImageDraw.Draw(img)
# kemer çerçevesi: çift altın çizgi
for off, wd, col in [(0, 6, GOLD), (16, 2, GOLD_D)]:
    d.line(arch_poly(X0 - off, X1 + off, YS, YB + off, R + off) + [arch_poly(X0 - off, X1 + off, YS, YB + off, R + off)[0]], fill=col + (255,), width=wd, joint='curve')
# kemer tepesinde küçük alem
ax = W / 2; ay = APEX - 30
d.ellipse([ax - 9, ay - 9, ax + 9, ay + 9], fill=GOLD + (255,))
d.polygon([(ax, ay - 46), (ax + 12, ay - 18), (ax - 12, ay - 18)], fill=GOLD + (255,))

# --- tezhip kenar çerçevesi
for off, wd in [(34, 3), (48, 1)]:
    d.rectangle([off, off, W - off, H - off], outline=GOLD + (230,), width=wd)
for (cx, cy) in [(41, 41), (W - 41, 41), (41, H - 41), (W - 41, H - 41)]:
    d.polygon([(cx, cy - 16), (cx + 16, cy), (cx, cy + 16), (cx - 16, cy)], fill=GOLD + (255,))
for y in range(120, H - 100, 64):
    for x in (41, W - 41):
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=GOLD + (200,))

def ctext(y, t, f, fill, sp=0, stroke=0):
    ws = [d.textlength(c, font=f) for c in t] if sp else None
    tw = (sum(ws) + sp * (len(t) - 1)) if sp else d.textlength(t, font=f)
    x = (W - tw) / 2
    if sp:
        for c, wc in zip(t, ws): d.text((x, y), c, font=f, fill=fill, stroke_width=stroke, stroke_fill=(8, 14, 30)); x += wc + sp
    else:
        d.text((x, y), t, font=f, fill=fill, stroke_width=stroke, stroke_fill=(8, 14, 30))

# üst marka
ctext(120, 'HANEDAN TARİHİ', fnt('NotoSans-Bold.ttf', 40), GOLD + (255,), sp=12)
d.line([(W / 2 - 170, 182), (W / 2 + 170, 182)], fill=GOLD + (200,), width=2)

# --- bölüm madalyonu kemerin alt kenarına oturur
mc, mr = (W / 2, YB), 92
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse([mc[0] - mr - 14, mc[1] - mr - 6, mc[0] + mr + 14, mc[1] + mr + 22], fill=(0, 0, 0, 170))
img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(12))); d = ImageDraw.Draw(img)
pts = []
for k in range(32):
    ang = 2 * math.pi * k / 32; rr = mr + (8 if k % 2 == 0 else 0)
    pts.append((mc[0] + rr * math.cos(ang), mc[1] + rr * math.sin(ang)))
d.polygon(pts, fill=GOLD + (255,))
d.ellipse([mc[0] - mr + 10, mc[1] - mr + 10, mc[0] + mr - 10, mc[1] + mr - 10], fill=LAPIS + (255,), outline=GOLD_D + (255,), width=3)
fb = fnt('NotoSans-Bold.ttf', 24); tw = d.textlength('BÖLÜM', font=fb)
d.text((mc[0] - tw / 2, mc[1] - 58), 'BÖLÜM', font=fb, fill=GOLD + (255,))
fn = fnt('NotoSerifDisplay-Bold.ttf', 74); tw = d.textlength(NUM, font=fn)
d.text((mc[0] - tw / 2, mc[1] - 36), NUM, font=fn, fill=CREAM + (255,))

# --- başlıklar
ctext(1312, SIRA, fnt('NotoSans-Bold.ttf', 34), GOLD + (255,), sp=8)
ctext(1352, PADISAH, fnt('NotoSerifDisplay-Bold.ttf', 128), CREAM + (255,), stroke=2)
sz = 104
while d.textlength(TITLE, font=fnt('NotoSerifDisplay-Bold.ttf', sz)) > 900 and sz > 60: sz -= 4
ctext(1512, TITLE, fnt('NotoSerifDisplay-Bold.ttf', sz), GOLD + (255,), stroke=2)
# alt süs
y = 1655; d.line([(W / 2 - 220, y), (W / 2 - 24, y)], fill=GOLD + (220,), width=2); d.line([(W / 2 + 24, y), (W / 2 + 220, y)], fill=GOLD + (220,), width=2)
d.polygon([(W / 2, y - 10), (W / 2 + 10, y), (W / 2, y + 10), (W / 2 - 10, y)], fill=GOLD + (255,))

img.convert('RGB').save(OUTP, quality=93)
print('ok', round(APEX))
