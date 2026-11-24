import numpy as np, math, random, subprocess, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
F = '/usr/share/fonts/truetype/noto/'
def fnt(n, s): return ImageFont.truetype(F + n, s)
SERIF_B = 'NotoSerif-Bold.ttf'; SERIF_D = 'NotoSerifDisplay-Bold.ttf'; SANS_B = 'NotoSans-Bold.ttf'; SANS = 'NotoSans-Regular.ttf'
OUT = os.environ.get('OUT', '.'); TMP = os.environ.get('TMP', '/tmp')
VO = 0.5  # voice offset
CREAM = (243, 232, 208); GOLD = (214, 172, 84); BURG = (140, 28, 36); INK = (45, 26, 16)

def ease_out(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def ease_back(x):
    x = max(0, min(1, x)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

# ---------- scenes ----------
scenes = [  # file, start, end, pan direction, source line
    ('s1.png', 0.0, 4.6 + VO, (0, -1), 'Kaynak: Halil İnalcık, Devlet-i Aliyye I'),
    ('s2.png', 4.6 + VO, 12.0 + VO, (1, 0), 'Kaynak: Halil İnalcık, Devlet-i Aliyye I'),
    ('s3.png', 12.0 + VO, 18.3 + VO, (0, 1), 'Kaynak: Aşıkpaşazade, Tevârîh-i Âl-i Osmân'),
    ('s4.png', 18.3 + VO, 24.45 + VO, (-1, 0), 'Kaynak: Aşıkpaşazade, Tevârîh-i Âl-i Osmân'),
    ('s5.png', 24.45 + VO, 28.4, (0, -1), 'Rivayet · Kaynak: Aşıkpaşazade, Tevârîh-i Âl-i Osmân'),
]
END_START, TOTAL = 28.4, 32.0
XF = 0.5  # crossfade
SCALE0 = 1.12
imgs = []
for f, *_ in scenes:
    im = Image.open('in/' + f).convert('RGB')
    s = max(W / im.width, H / im.height) * SCALE0
    imgs.append(im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS))

def scene_frame(i, t):
    f, a, b, (dx, dy), _ = scenes[i]
    p = (t - a) / (b - a)
    z = 1.0 + 0.07 * p  # zoom in within the oversize image
    im = imgs[i]
    cw, ch = W * SCALE0 / z, H * SCALE0 / z
    cw = min(cw, im.width); ch = min(ch, im.height)
    mx, my = (im.width - cw) / 2, (im.height - ch) / 2
    cx = mx + dx * mx * (p - 0.5) * 1.6; cy = my + dy * my * (p - 0.5) * 1.6
    return im.resize((W, H), Image.BICUBIC, box=(cx, cy, cx + cw, cy + ch))

# ---------- static overlays ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
VIG = np.clip(1.0 - 0.75 * np.clip(r - 0.55, 0, 1) ** 1.6, 0.25, 1.0)
grad = np.ones((H, 1), np.float32)
top = np.linspace(0, 1, 420); grad[:420, 0] = 0.35 + 0.65 * top ** 0.8
bot = np.linspace(1, 0, 620); grad[H - 620:, 0] = 0.30 + 0.70 * bot ** 0.9
VIG = (VIG * grad)[..., None]

def text_center(d, y, txt, fn, fill, spacing=0, shadow=True):
    if spacing:
        widths = [d.textlength(c, font=fn) for c in txt]; tw = sum(widths) + spacing * (len(txt) - 1)
        x = (W - tw) / 2
        for c, w in zip(txt, widths):
            if shadow: d.text((x + 2, y + 3), c, font=fn, fill=(0, 0, 0, 160))
            d.text((x, y), c, font=fn, fill=fill); x += w + spacing
    else:
        tw = d.textlength(txt, font=fn); x = (W - tw) / 2
        if shadow: d.text((x + 2, y + 3), txt, font=fn, fill=(0, 0, 0, 170))
        d.text((x, y), txt, font=fn, fill=fill)

HEAD = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(HEAD)
text_center(d, 92, 'HANEDAN TARİHİ', fnt(SANS_B, 30), GOLD + (255,), spacing=9)
d.line([(W / 2 - 150, 142), (W / 2 + 150, 142)], fill=GOLD + (200,), width=2)
d.polygon([(W / 2, 134), (W / 2 + 8, 142), (W / 2, 150), (W / 2 - 8, 142)], fill=GOLD + (255,))
text_center(d, 158, 'OSMAN GAZİ', fnt(SERIF_D, 76), CREAM + (255,))
# "BÖLÜM 1/5" pill
fb = fnt(SANS_B, 34); tw = d.textlength('BÖLÜM 1/5', font=fb)
d.rounded_rectangle([(W - tw) / 2 - 26, 262, (W + tw) / 2 + 26, 316], radius=27, fill=BURG + (235,), outline=GOLD + (255,), width=2)
d.text(((W - tw) / 2, 266), 'BÖLÜM 1/5', font=fb, fill=CREAM + (255,))

def src_layer(txt):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(L)
    text_center(dd, 1812, txt, fnt(SANS, 28), (225, 210, 180, 235))
    return L
SRC = [src_layer(s[4]) for s in scenes]

# ---------- particles ----------
random.seed(7)
parts = [[random.uniform(0, W), random.uniform(0, H), random.uniform(1.5, 4.5), random.uniform(-6, 6), random.uniform(-22, -8), random.uniform(0, 6.28)] for _ in range(70)]
def particles(t):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(L)
    for x0, y0, rr, vx, vy, ph in parts:
        x = (x0 + vx * t + 18 * math.sin(t * 0.6 + ph)) % W; y = (y0 + vy * t) % H
        a = int(70 + 60 * math.sin(t * 1.3 + ph))
        dd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 226, 170, max(0, a)))
    return L

# ---------- wax seal stamps ----------
def make_seal(txt):
    S = 320; im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); dd = ImageDraw.Draw(im)
    rnd = random.Random(txt); c = S / 2; pts = []
    for k in range(48):
        a = 2 * math.pi * k / 48; rr = 128 + rnd.uniform(-9, 9)
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    dd.polygon(pts, fill=(150, 26, 32, 255))
    dd.ellipse([c - 104, c - 104, c + 104, c + 104], outline=(105, 14, 20, 255), width=6)
    dd.ellipse([c - 92, c - 92, c + 92, c + 92], outline=(190, 70, 70, 140), width=2)
    size = 64
    while True:
        fn = fnt(SERIF_B, size); tw = dd.textlength(txt, font=fn)
        if tw <= 160 or size <= 30: break
        size -= 2
    bb = dd.textbbox((0, 0), txt, font=fn); th = bb[3] - bb[1]
    dd.text((c - tw / 2 + 2, c - th / 2 - bb[1] + 3), txt, font=fn, fill=(90, 10, 15, 255))
    dd.text((c - tw / 2, c - th / 2 - bb[1]), txt, font=fn, fill=(250, 228, 190, 255))
    im = im.rotate(-9, resample=Image.BICUBIC)
    sh = Image.new('RGBA', (S, S), (0, 0, 0, 0)); sh.putalpha(im.split()[3].point(lambda v: v * 0.5))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    out = Image.new('RGBA', (S + 20, S + 20), (0, 0, 0, 0)); out.alpha_composite(sh, (12, 14)); out.alpha_composite(im, (0, 0))
    return out
stamps = [  # text, time, scene index
    ('600 YIL', 1.44 + VO, 0), ('1243', 4.94 + VO, 1), ('SÖĞÜT', 16.8 + VO, 2), ('OSMAN', 20.72 + VO, 3), ('RÜYA', 25.12 + VO, 4)]
SEALS = [make_seal(s[0]) for s in stamps]
SEAL_C = (842, 520)

# ---------- subtitles ----------
subs = [
    (0.08, 1.40, 'Bu küçük çadırdan,'),
    (1.44, 4.55, 'altı yüz yıl sürecek bir *imparatorluk* doğacaktı.'),
    (4.94, 6.50, '*Bin iki yüz kırk üç.*'),
    (6.56, 9.80, 'Moğollar, *Kösedağ*\'da Selçuklu ordusunu ezdi.'),
    (9.84, 12.00, 'Anadolu *paramparça* oldu.'),
    (12.32, 14.20, 'Bizans sınırında, *Kayı* boyundan'),
    (14.24, 16.76, '*Ertuğrul Gazi*\'nin küçük beyliği vardı:'),
    (16.80, 18.30, '*Söğüt* ve *Domaniç*.'),
    (18.48, 21.86, 'Ertuğrul Gazi ölünce, başa oğlu *Osman* geçti.'),
    (21.88, 24.40, 'Elinde yalnızca *birkaç yüz atlı* vardı.'),
    (24.70, 27.70, 'Ama bir *rüyası* vardı...'),
]
SF = fnt(SERIF_B, 54)
def render_sub(txt):
    parts = []; hl = False
    for p in txt.split('*'):
        if p: parts.append((p, hl))
        hl = not hl
    # word-wrap on words keeping highlight flags; punctuation attaches
    words = []
    for p, h in parts:
        for i, w in enumerate(p.split(' ')):
            if w == '':
                if words: words[-1][2] = True
                continue
            if i > 0 and words: words[-1][2] = True
            words.append([w, h, False])
    dummy = ImageDraw.Draw(Image.new('RGBA', (10, 10))); sp = dummy.textlength(' ', font=SF)
    maxw = 860; lines = [[]]; cw = 0
    for w in words:
        ww = dummy.textlength(w[0], font=SF)
        if lines[-1] and cw + ww > maxw: lines.append([]); cw = 0
        lines[-1].append(w); cw += ww + (sp if w[2] else 0)
    lh = 72; bw = max(sum(dummy.textlength(w[0], font=SF) + (sp if w[2] else 0) for w in ln) for ln in lines) + 80
    bh = lh * len(lines) + 46
    L = Image.new('RGBA', (int(bw) + 40, int(bh) + 40), (0, 0, 0, 0)); dd = ImageDraw.Draw(L)
    sh = Image.new('RGBA', L.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([24, 28, bw + 16, bh + 20], radius=18, fill=(0, 0, 0, 150))
    L.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    dd.rounded_rectangle([20, 20, bw + 20, bh + 20], radius=16, fill=(244, 233, 207, 246), outline=(120, 70, 30, 255), width=3)
    dd.rounded_rectangle([30, 30, bw + 10, bh + 10], radius=12, outline=(176, 128, 64, 180), width=1)
    y = 20 + 22
    for ln in lines:
        lw = sum(dummy.textlength(w[0], font=SF) + (sp if w[2] else 0) for w in ln) - (sp if ln[-1][2] else 0)
        x = 20 + (bw - lw) / 2
        for w, h, s in ln:
            dd.text((x, y), w, font=SF, fill=(BURG if h else INK) + (255,)); x += dd.textlength(w, font=SF) + (sp if s else 0)
        y += lh
    return L
SUBS = [(a + VO, b + VO, render_sub(t)) for a, b, t in subs]
SUB_CY = 1500

# ---------- end card ----------
def end_card():
    rnd = np.random.default_rng(3)
    base = np.ones((H, W, 3), np.float32) * np.array([236, 222, 190], np.float32)
    noise = rnd.normal(0, 1, (H // 4, W // 4)).astype(np.float32)
    nz = np.array(Image.fromarray(((noise * 20) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) - 128
    base += nz[..., None] * 0.6
    rr = np.sqrt(((xx - W / 2) / (W * 0.6)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2)
    base *= np.clip(1 - 0.45 * np.clip(rr - 0.5, 0, 1), 0.5, 1)[..., None]
    im = Image.fromarray(base.clip(0, 255).astype(np.uint8)).convert('RGBA'); dd = ImageDraw.Draw(im)
    dd.rectangle([40, 40, W - 40, H - 40], outline=(150, 105, 45, 255), width=4)
    dd.rectangle([56, 56, W - 56, H - 56], outline=(150, 105, 45, 160), width=1)
    text_center(dd, 210, 'HANEDAN TARİHİ', fnt(SANS_B, 40), BURG + (255,), spacing=10, shadow=False)
    dd.line([(W / 2 - 180, 280), (W / 2 + 180, 280)], fill=(150, 105, 45, 255), width=2)
    text_center(dd, 400, 'SIRADAKİ BÖLÜM', fnt(SANS_B, 38), (110, 75, 40, 255), spacing=6, shadow=False)
    text_center(dd, 470, 'OSMAN GAZİ · 2/5', fnt(SERIF_D, 78), INK + (255,), shadow=False)
    text_center(dd, 580, 'Rüya', fnt(SERIF_D, 110), BURG + (255,), shadow=False)
    bx0, by0, bx1, by1 = 110, 830, W - 110, 1240
    dd.rounded_rectangle([bx0, by0, bx1, by1], radius=20, fill=(52, 30, 18, 245), outline=GOLD + (255,), width=3)
    text_center(dd, by0 + 40, 'KAYNAKLAR', fnt(SANS_B, 40), GOLD + (255,), spacing=6, shadow=False)
    f2 = fnt(SANS, 34)
    items = ['1. Halil İnalcık, Devlet-i Aliyye I', '2. Aşıkpaşazade, Tevârîh-i Âl-i Osmân', '3. Neşrî, Kitâb-ı Cihan-nümâ']
    for k, it in enumerate(items): dd.text((bx0 + 50, by0 + 130 + k * 70), it, font=f2, fill=CREAM + (255,))
    text_center(dd, 1290, 'Rüya sahnesi rivayettir.', fnt(SANS, 32), (110, 75, 40, 255), shadow=False)
    fb2 = fnt(SANS_B, 44); t = 'TAKİP ET'; tw2 = dd.textlength(t, font=fb2)
    dd.rounded_rectangle([(W - tw2) / 2 - 50, 1460, (W + tw2) / 2 + 50, 1550], radius=45, fill=BURG + (255,))
    dd.text(((W - tw2) / 2, 1474), t, font=fb2, fill=CREAM + (255,))
    text_center(dd, 1600, 'Hikâye devam ediyor', fnt(SERIF_B, 40), INK + (255,), shadow=False)
    return im.convert('RGB')
END = end_card()
END_SEAL = make_seal('1/5')

# ---------- render ----------
def frame(t):
    if t >= END_START:
        p = (t - END_START) / 0.5
        last = scene_frame(4, min(t, scenes[4][2]))
        fr = Image.blend(last, END, ease_out(p)) if p < 1 else END.copy()
        fr = fr.convert('RGBA')
        ts = t - (END_START + 0.6)
        if ts > 0:
            sc = 1.0 + 0.8 * (1 - ease_out(ts / 0.18)); s = END_SEAL
            if sc != 1: s = s.resize((int(s.width * sc), int(s.height * sc)), Image.BICUBIC)
            if ts < 0.18: s.putalpha(s.split()[3].point(lambda v: int(v * ease_out(ts / 0.18))))
            fr.alpha_composite(s, (int(W / 2 - s.width / 2 + 330), int(380 - s.height / 2 - 40)))
        return fr.convert('RGB')
    # active scene(s)
    idx = max(i for i, s in enumerate(scenes) if t >= s[1])
    img = scene_frame(idx, t)
    if idx > 0 and t < scenes[idx][1] + XF:
        prev = scene_frame(idx - 1, t)
        img = Image.blend(prev, img, ease_out((t - scenes[idx][1]) / XF))
    arr = np.asarray(img).astype(np.float32)
    flick = 1.0 + 0.025 * math.sin(t * 9.1) + 0.015 * math.sin(t * 23.7)
    arr = (arr * np.clip(VIG * flick, 0, 1.05)).clip(0, 255)
    if t < 0.4: arr *= t / 0.4
    fr = Image.fromarray(arr.astype(np.uint8)).convert('RGBA')
    fr.alpha_composite(particles(t))
    fr.alpha_composite(HEAD)
    # source line (fade with scenes)
    fr.alpha_composite(SRC[idx])
    # seals
    for k, (txt, ts0, si) in enumerate(stamps):
        if si != idx or t < ts0: continue
        ts = t - ts0; s = SEALS[k]
        if ts < 0.2:
            sc = 1.0 + 0.9 * (1 - ease_out(ts / 0.2)); s = s.resize((int(s.width * sc), int(s.height * sc)), Image.BICUBIC)
            s.putalpha(s.split()[3].point(lambda v, a=ease_out(ts / 0.2): int(v * a)))
        elif ts < 0.35:
            sc = 1.0 - 0.05 * math.sin((ts - 0.2) / 0.15 * math.pi); s = s.resize((int(s.width * sc), int(s.height * sc)), Image.BICUBIC)
        fr.alpha_composite(s, (int(SEAL_C[0] - s.width / 2), int(SEAL_C[1] - s.height / 2)))
    # subtitle
    for a, b, L in SUBS:
        if a <= t < b + 0.15:
            p = min(1, (t - a) / 0.25); q = 1 if t < b else max(0, 1 - (t - b) / 0.15)
            al = ease_out(p) * q; off = int(18 * (1 - ease_out(p)))
            s = L.copy(); s.putalpha(s.split()[3].point(lambda v: int(v * al)))
            fr.alpha_composite(s, (int(W / 2 - s.width / 2), int(SUB_CY - s.height / 2 + off)))
    return fr.convert('RGB')

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        for t in [2.3, 8.0, 17.6, 22.5, 26.0, 30.5]:
            frame(t).save(f'{OUT}/kontrol_{t:.1f}s.jpg', quality=88)
        sys.exit()
    N = int(TOTAL * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', f'{TMP}/video.mp4'], stdin=subprocess.PIPE)
    for n in range(N):
        p.stdin.write(frame(n / FPS).tobytes())
    p.stdin.close(); p.wait()
    # audio mix
    st = [int((s[1]) * 1000) for s in stamps] + [int((END_START + 0.6) * 1000)]
    stamp_in = ''.join(f'[4:a]adelay={d}|{d},volume=0.9[st{k}];' for k, d in enumerate(st))
    # need separate input copies for each stamp
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{TMP}/video.mp4', '-i', 'in/vo.mp3', '-i', 'in/music.mp3',
           '-i', 'in/sfx_wind.mp3', '-i', 'in/sfx_cav.mp3', '-i', 'in/sfx_horse.mp3']
    for _ in st: cmd += ['-i', 'in/sfx_stamp.mp3']
    fc = (f'[1:a]adelay={int(VO*1000)}|{int(VO*1000)},volume=1.0[vo];'
          f'[2:a]atrim=0:{TOTAL},volume=\'if(lt(t,{END_START}),0.16,0.16+0.30*min(1,(t-{END_START})/0.6))\':eval=frame,afade=t=out:st={TOTAL-1.2}:d=1.2[mu];'
          f'[3:a]volume=0.45,afade=t=in:d=0.4,afade=t=out:st=4.2:d=1.2[wi];'
          f'[4:a]adelay=5300|5300,volume=0.40,afade=t=out:st=10.5:d=1.5[cv];'
          f'[5:a]adelay=19000|19000,volume=0.35,afade=t=out:st=23.0:d=1.5[hr];')
    labels = []
    for k, d in enumerate(st):
        fc += f'[{6+k}:a]adelay={d}|{d},volume=0.9[st{k}];'; labels.append(f'[st{k}]')
    fc += '[vo][mu][wi][cv][hr]' + ''.join(labels) + f'amix=inputs={5+len(st)}:normalize=0:duration=longest,atrim=0:{TOTAL},loudnorm=I=-14:TP=-1.5:LRA=11[a]'
    cmd += ['-filter_complex', fc, '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', str(TOTAL),
            f'{OUT}/HanedanTarihi_OsmanGazi_Bolum1.mp4']
    subprocess.run(cmd, check=True)
    print('done')
