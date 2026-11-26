# Orhan Gazi Bölüm 4/5 · İzmit ve Karesi — anlatım formatı (kodla çizim)
import math, sys, os
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from motor import *

VO = 0.4                      # seslendirme gecikmesi
def V(t): return t + VO       # transkript zamanı -> video zamanı
TOTAL, END_START = 30.0, 26.6
BG = make_bg()
LBL = 'HANEDAN TARİHİ · ORHAN GAZİ 4/5'

BEATS = [  # (başlangıç, satır1, satır2, vurgu rengi, kaynak)
    (0.0, 'OSMANLI SADECE', 'KILIÇLA MI BÜYÜDÜ?', BURG, None),
    (V(3.68), 'İZMİT · 1337', 'SAVAŞMADAN TESLİM', LAPIS, 'HALİL İNALCIK · DEVLET-İ ALİYYE I'),
    (V(8.9), 'KARESİ · 1345', 'İKİ KARDEŞ, BİR TAHT', BURG, 'AŞIKPAŞAZADE · TEVÂRÎH-İ ÂL-İ OSMÂN'),
    (V(14.5), 'ORHAN ARAYA GİRDİ', 'BEYLİK OSMANLI OLDU', LAPIS, 'E. ZACHARIADOU · KARASI AND THE OTTOMANS'),
    (V(17.78), 'GEMİLER VE', 'KOMUTANLAR', LAPIS, 'E. ZACHARIADOU · KARASI AND THE OTTOMANS'),
    (V(24.45), 'SIRADA:', 'RUMELİ', BURG, None),
]
SUBS = [('Osmanlı sadece', .08, 1.28), ('*kılıçla* mı', 1.36, 1.84), ('büyüdü?', 1.88, 2.6), ('*Hayır.*', 2.72, 3.6),
        ('*1337*', 3.81, 5.1), ('Yıllardır kuşatılan', 5.28, 6.32), ('*İzmit*,', 6.4, 6.9), ('*savaşmadan*', 6.96, 7.55), ('teslim oldu.', 7.6, 8.8),
        ('*1345*', 8.96, 10.3), ('Komşu *Karesi*', 10.48, 11.24), ("Beyliği'nde", 11.28, 11.9), ('iki *kardeş*', 12.0, 12.64), ('*taht* için', 12.72, 13.2),
        ('kavgaya tutuştu.', 13.28, 14.45), ('*Orhan* araya girdi', 14.56, 15.6), ('ve beyliği', 15.76, 16.32), ('topraklarına *kattı.*', 16.4, 17.76),
        ("Karesi'nin *gemicileri*", 17.8, 18.9), ('ve *komutanları*', 18.92, 19.7), ("artık Osmanlı'ydı.", 19.84, 21.36), ('Önlerinde', 21.44, 21.95),
        ('tek bir *engel* kaldı:', 22.08, 23.52), ('*deniz.*', 23.6, 24.4), ('Sırada *Rumeli* var...', 24.63, 26.2)]


# ---------------- çizimler ----------------
def sword(d, cx, cy, ang, col, hilt):
    pts = []
    L = 600
    for k in range(21):
        s = k / 20; x = -L / 2 + L * s; y = -95 * (s ** 2); w = 34 * (1 - s) + 4
        pts.append((x, y - w / 2))
    for k in range(20, -1, -1):
        s = k / 20; x = -L / 2 + L * s; y = -95 * (s ** 2); w = 34 * (1 - s) + 4
        pts.append((x, y + w / 2))
    ca, sa = math.cos(ang), math.sin(ang)
    R = lambda x, y: (cx + x * ca - y * sa, cy + x * sa + y * ca)
    d.polygon([R(x, y) for x, y in pts], fill=col, outline=INK)
    d.polygon([R(-L / 2 - 8, -40), R(-L / 2 + 8, -40), R(-L / 2 + 8, 40), R(-L / 2 - 8, 40)], fill=hilt)
    d.polygon([R(-L / 2 - 110, -14), R(-L / 2 - 8, -14), R(-L / 2 - 8, 14), R(-L / 2 - 110, 14)], fill=(110, 60, 30))


def scene_swords(fr, t, t0):
    d = ImageDraw.Draw(fr)
    grey = t >= V(2.72)
    sw = 0.05 * math.sin(t * 2.2)
    col = (170, 170, 170) if grey else (222, 226, 232)
    hilt = (150, 150, 150) if grey else GOLD
    sword(d, 540, 960, math.radians(-40) + sw, col, hilt)
    sword(d, 540, 960, math.radians(180 + 40) - sw, col, hilt)
    stamp(fr, 'YANLIŞ', 560, 930, V(2.72), t, BURG, -12, 130)


def castle(d, t, open_p, flag_p):
    s = STONE; sd = STONE_D
    d.rectangle([200, 950, 880, GROUND_Y], fill=s, outline=sd, width=4)
    for x in range(200, 880, 68):
        d.rectangle([x, 912, x + 40, 952], fill=s, outline=sd, width=3)
    for x0 in (130, 780):
        d.rectangle([x0, 820, x0 + 170, GROUND_Y], fill=s, outline=sd, width=4)
        for x in range(x0, x0 + 170, 48):
            d.rectangle([x, 784, x + 30, 822], fill=s, outline=sd, width=3)
        for yy in range(880, 1300, 90):
            d.rectangle([x0 + 70, yy, x0 + 100, yy + 40], fill=(90, 70, 55))
    for yy in range(990, GROUND_Y, 60):
        for xx in range(220 + (34 if (yy // 60) % 2 else 0), 860, 68):
            d.line([(xx, yy), (xx + 40, yy)], fill=sd, width=2)
    gx, gw, gt = 540, 190, 1080
    d.rectangle([gx - gw / 2, gt + gw / 2, gx + gw / 2, GROUND_Y], fill=(60, 45, 35))
    d.pieslice([gx - gw / 2, gt, gx + gw / 2, gt + gw], 180, 360, fill=(60, 45, 35))
    light = int(255 * open_p)
    if open_p > 0:
        d.rectangle([gx - gw / 2 + 10, gt + gw / 2, gx + gw / 2 - 10, GROUND_Y], fill=(250, 220, 150))
        d.pieslice([gx - gw / 2 + 10, gt + 10, gx + gw / 2 - 10, gt + gw - 10], 180, 360, fill=(250, 220, 150))
    dw = (gw / 2) * (1 - 0.85 * open_p)
    for side in (-1, 1):
        xa = gx + side * gw / 2; xb = xa - side * dw
        d.rectangle([min(xa, xb), gt + gw / 2, max(xa, xb), GROUND_Y], fill=(120, 72, 38), outline=(70, 40, 20), width=3)
    px = 215; d.rectangle([px - 4, 560, px + 4, 790], fill=INK)
    yb = 570 + 200 * flag_p; yo = 770 - 200 * ease_out(max(0, flag_p * 2 - 1))
    if flag_p < 0.5:
        flag(d, px + 4, yb, 150, 95, t, (110, 40, 120), 'cross', GOLD)
    else:
        flag(d, px + 4, yo, 150, 95, t, LAPIS, 'crescent')
    for x0 in (30, 930):
        d.polygon([(x0, GROUND_Y), (x0 + 60, GROUND_Y - 110), (x0 + 120, GROUND_Y)], fill=LAPIS, outline=INK)
        d.line([(x0 + 60, GROUND_Y - 110), (x0 + 60, GROUND_Y - 150)], fill=INK, width=4)


def scene_castle(fr, t, t0):
    d = ImageDraw.Draw(fr)
    op = ease_io(prog(t, V(7.6), V(8.6)))
    castle(d, t, op, op)
    badge(fr, 'SAVAŞSIZ', 700, 640, V(6.96), t, LAPIS, 56)


def figure(d, x, y, body, lean, t, turban=WHITE):
    hx = x + lean
    d.polygon([(x - 90, y), (x + 90, y), (hx + 50, y - 340), (hx - 50, y - 340)], fill=body, outline=INK)
    d.rectangle([hx - 50, y - 250, hx + 50, y - 232], fill=GOLD)
    d.ellipse([hx - 48, y - 440, hx + 48, y - 342], fill=(222, 180, 140), outline=INK)
    d.ellipse([hx - 62, y - 500, hx + 62, y - 410], fill=turban, outline=INK)
    return hx


def scene_throne(fr, t, t0):
    d = ImageDraw.Draw(fr)
    d.rectangle([450, 1180, 630, 1220], fill=GOLD, outline=INK, width=3)
    d.rectangle([465, 1220, 485, GROUND_Y], fill=GOLD); d.rectangle([595, 1220, 615, GROUND_Y], fill=GOLD)
    d.rounded_rectangle([465, 930, 615, 1185], radius=70, fill=GOLD, outline=INK, width=3)
    d.rounded_rectangle([485, 960, 595, 1180], radius=55, fill=BURG)
    s = math.sin(t * 5)
    lx = figure(d, 250, GROUND_Y, (60, 120, 80), -24 - 22 * s, t)
    rx = figure(d, 830, GROUND_Y, (200, 110, 40), 24 - 22 * s, t)
    d.line([(lx + 45, GROUND_Y - 270), (470, 1050)], fill=INK, width=14)
    d.line([(rx - 45, GROUND_Y - 270), (610, 1050)], fill=INK, width=14)
    if int(t * 6) % 2 == 0:
        for k, (x, y) in enumerate([(540, 860), (450, 890), (630, 890)]):
            d.line([(x - 18, y - 30), (x + 6, y - 6), (x - 8, y + 4), (x + 18, y + 30)], fill=BURG, width=7)
    badge(fr, 'TAHT KAVGASI', 540, 620, V(13.28), t, BURG, 56)


MAP = dict(x0=60, y0=470, x1=1020, y1=1300)
def mp(fx, fy): return (MAP['x0'] + fx * (MAP['x1'] - MAP['x0']), MAP['y0'] + fy * (MAP['y1'] - MAP['y0']))
REG = {
    'rumeli': [(0.02, 0.04), (0.46, 0.04), (0.5, 0.2), (0.3, 0.27), (0.17, 0.3), (0.05, 0.34)],
    'osm': [(0.47, 0.4), (0.68, 0.36), (0.9, 0.3), (0.97, 0.5), (0.85, 0.8), (0.55, 0.85), (0.44, 0.6)],
    'kar': [(0.13, 0.48), (0.3, 0.42), (0.47, 0.4), (0.44, 0.6), (0.55, 0.85), (0.3, 0.9), (0.1, 0.75)],
}
SEA = {
    'marmara': [(0.2, 0.33), (0.35, 0.26), (0.6, 0.24), (0.8, 0.27), (0.68, 0.36), (0.47, 0.4), (0.3, 0.42), (0.16, 0.42)],
    'ege': [(0.0, 0.4), (0.1, 0.42), (0.13, 0.48), (0.1, 0.75), (0.12, 1.0), (0.0, 1.0)],
    'karadeniz': [(0.55, 0.0), (1.0, 0.0), (1.0, 0.16), (0.8, 0.12), (0.62, 0.08)],
}
CITY = {'Bursa': (0.6, 0.5), 'İznik': (0.74, 0.44), 'İzmit': (0.82, 0.31), 'Balıkesir': (0.3, 0.64), 'Gelibolu': (0.17, 0.3)}


def draw_map(fr, t, kar_p, rumeli_p=0.0, arrow_p=0.0):
    d = ImageDraw.Draw(fr)
    d.rounded_rectangle([MAP['x0'] - 14, MAP['y0'] - 14, MAP['x1'] + 14, MAP['y1'] + 14], radius=22, fill=(236, 226, 204), outline=GOLD, width=6)
    for nm, poly in SEA.items():
        d.polygon([mp(*p) for p in poly], fill=(120, 165, 205))
    d.polygon([mp(*p) for p in REG['osm']], fill=LAPIS, outline=INK)
    kc = tuple(int(a + (b - a) * kar_p) for a, b in zip((214, 140, 60), LAPIS))
    d.polygon([mp(*p) for p in REG['kar']], fill=kc, outline=INK)
    pulse = 0.5 + 0.5 * math.sin(t * 6)
    rc = tuple(int(a + (b - a) * rumeli_p * (0.6 + 0.4 * pulse)) for a, b in zip((222, 210, 186), BURG))
    d.polygon([mp(*p) for p in REG['rumeli']], fill=rc, outline=INK)
    f = font(40)
    for txt, (fx, fy), col in [('OSMANLI', (0.7, 0.62), WHITE), ('KARESİ', (0.27, 0.58), WHITE), ('RUMELİ', (0.22, 0.16), INK if rumeli_p < 0.5 else WHITE)]:
        x, y = mp(fx, fy); w = f.getlength(txt); d.text((x - w / 2, y - 22), txt, font=f, fill=col)
    fs = font(28)
    for nm, (fx, fy) in CITY.items():
        x, y = mp(fx, fy); d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=WHITE, outline=INK, width=3)
        d.text((x + 14, y - 36), nm, font=fs, fill=WHITE, stroke_width=4, stroke_fill=INK)
    if arrow_p > 0:
        a0 = mp(0.26, 0.47); a1 = mp(0.2, 0.2)
        n = 14; m = int(n * arrow_p)
        for k in range(m):
            if k % 2 == 0:
                p0 = (a0[0] + (a1[0] - a0[0]) * k / n, a0[1] + (a1[1] - a0[1]) * k / n)
                p1 = (a0[0] + (a1[0] - a0[0]) * (k + 1) / n, a0[1] + (a1[1] - a0[1]) * (k + 1) / n)
                d.line([p0, p1], fill=BURG, width=12)
        if arrow_p >= 1:
            ang = math.atan2(a1[1] - a0[1], a1[0] - a0[0])
            tip = a1; L = 40
            d.polygon([tip, (tip[0] - L * math.cos(ang - 0.5), tip[1] - L * math.sin(ang - 0.5)), (tip[0] - L * math.cos(ang + 0.5), tip[1] - L * math.sin(ang + 0.5))], fill=BURG)


def scene_map(fr, t, t0):
    kp = ease_io(prog(t, V(16.0), V(17.0)))
    draw_map(fr, t, kp)
    badge(fr, '+1 BEYLİK', 820, 1240, V(17.04), t, BURG, 52)


def ship(d, x, y, t, ph):
    bob = 8 * math.sin(t * 2.5 + ph); y = y + bob
    d.polygon([(x - 110, y), (x + 110, y), (x + 80, y + 50), (x - 80, y + 50)], fill=(120, 72, 38), outline=INK)
    d.rectangle([x - 4, y - 190, x + 4, y], fill=INK)
    d.polygon([(x + 6, y - 180), (x + 6, y - 30), (x + 95, y - 40)], fill=(245, 236, 214), outline=INK)
    d.polygon([(x - 6, y - 170), (x - 6, y - 40), (x - 80, y - 50)], fill=(245, 236, 214), outline=INK)
    flag(d, x + 4, y - 228, 60, 36, t + ph, LAPIS, 'crescent')


def scene_sea(fr, t, t0):
    d = ImageDraw.Draw(fr)
    top = 1080
    d.rectangle([0, top, W, GROUND_Y], fill=(110, 155, 200))
    for k in range(5):
        yb = top + 20 + k * 50
        pts = [(x, yb + 10 * math.sin(x / 70 + t * 2 + k)) for x in range(0, W + 20, 20)]
        d.line(pts, fill=(230, 240, 250), width=4)
    targets = [230, 540, 850]
    for k, tx in enumerate(targets):
        p = ease_out(prog(t, V(18.3) + 0.35 * k, V(18.3) + 0.35 * k + 1.4))
        x = -200 + (tx + 200) * p
        ship(d, x, top + 40 + (k % 2) * 30, t, k * 1.7)
    if t >= V(19.04):
        for k, x in enumerate([300, 540, 780]):
            pk = back(prog(t, V(19.04) + 0.12 * k, V(19.04) + 0.12 * k + 0.3))
            if pk <= 0: continue
            r = 72 * pk; y = 610
            M = Image.new('L', (int(2 * r) + 2, int(2 * r) + 2), 0); ImageDraw.Draw(M).ellipse([0, 0, 2 * r, 2 * r], fill=255)
            P = Image.new('RGBA', M.size, (238, 228, 206, 255)); q = ImageDraw.Draw(P); c = r
            q.rounded_rectangle([c - 0.6 * r, c + 0.35 * r, c + 0.6 * r, c + 1.4 * r], radius=int(0.3 * r), fill=LAPIS)
            q.ellipse([c - 0.32 * r, c - 0.3 * r, c + 0.32 * r, c + 0.42 * r], fill=(222, 180, 140), outline=INK)
            q.pieslice([c - 0.3 * r, c + 0.02 * r, c + 0.3 * r, c + 0.62 * r], 0, 180, fill=(70, 50, 40))
            q.ellipse([c - 0.45 * r, c - 0.78 * r, c + 0.45 * r, c - 0.12 * r], fill=WHITE, outline=INK)
            fr.paste(P, (int(x - r), int(y - r)), M)
            d.ellipse([x - r, y - r, x + r, y + r], outline=LAPIS, width=7)
    stamp(fr, 'ENGEL: DENİZ', 540, 780, V(23.6), t, LAPIS, -6, 66)


def scene_rumeli(fr, t, t0):
    rp = ease_io(prog(t, V(25.04), V(25.6)))
    ap = ease_io(prog(t, V(24.7), V(26.0)))
    draw_map(fr, t, 1.0, rp, ap)


SCENES = [scene_swords, scene_castle, scene_throne, scene_map, scene_sea, scene_rumeli]


def end_overlay(fr, t):
    if t < END_START: return
    d = ImageDraw.Draw(fr)
    p = ease_out(prog(t, END_START, END_START + 0.3))
    badge(fr, 'YORUMA YAZ · TAKİP ET', 540, 1470, END_START, t, BURG, 50)
    f = font(36); txt = "Sıradaki: Orhan Gazi 5/5 · Rumeli'ye Geçiş"; w = f.getlength(txt)
    d.text((540 - w / 2, 1560), txt, font=f, fill=(255, 255, 255, int(255 * p)))
    fs = font(26, False); s = 'Kaynaklar: H. İnalcık · Aşıkpaşazade · E. Zachariadou'; w = fs.getlength(s)
    d.text((540 - w / 2, 1700), s, font=fs, fill=(210, 220, 240, int(255 * p)))


def frame(t):
    fr = BG.copy().convert('RGBA')
    top_label(fr, LBL)
    bi = max(i for i, b in enumerate(BEATS) if t >= b[0])
    b = BEATS[bi]
    SCENES[bi](fr, t, b[0])
    headline(fr, b[1], b[2], b[3], b[0], t, b[4])
    if t < END_START:
        for s, a0, a1 in SUBS:
            sub_pill(fr, s, V(a0), V(a1), t)
    end_overlay(fr, t)
    if t < 0.25:
        fr = Image.blend(Image.new('RGBA', fr.size, CREAM + (255,)), fr, t / 0.25)
    return fr.convert('RGB')


def frame_bytes(n): return frame(n / FPS).tobytes()


EP = dict(total=TOTAL, end_start=END_START, frame_bytes=frame_bytes,
          audio=dict(vo_off=VO, vo='vo.mp3', music='music.mp3', stamp='stamp.mp3', stamps=[2.72, 17.04, 23.6]))

if __name__ == '__main__':
    if sys.argv[1:2] == ['preview']:
        from PIL import Image as I
        ts = [float(x) for x in sys.argv[2].split(',')]
        sh = I.new('RGB', (360 * len(ts), 640))
        for k, tt in enumerate(ts): sh.paste(frame(tt).resize((360, 640)), (360 * k, 0))
        sh.save(sys.argv[3], quality=85)
    else:
        render(EP, sys.argv[1])
