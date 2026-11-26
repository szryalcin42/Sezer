# HanedanTarihi "anlatım" formatı motoru: her şey kodla çizilir (görsel üretimi yok).
# Bölüm dosyası: BEATS, SUBS, çizim fonksiyonları ve ses ayarlarını tanımlar, sonra render(EP) çağırır.
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
FD = '/usr/share/fonts/truetype/liberation/'
INK = (38, 30, 26); CREAM = (247, 241, 229); LAPIS = (28, 52, 120); LAPIS_L = (70, 105, 175)
GOLD = (205, 160, 70); BURG = (172, 30, 40); STONE = (216, 202, 176); STONE_D = (168, 148, 116)
WHITE = (255, 255, 255); GROUND_Y = 1330
_fc = {}


def font(size, bold=True):
    k = (size, bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FD + ('LiberationSans-Bold.ttf' if bold else 'LiberationSans-Regular.ttf'), size)
    return _fc[k]


def ease_out(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def ease_io(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def back(x):
    x = max(0.0, min(1.0, x)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def prog(t, a, b): return max(0.0, min(1.0, (t - a) / (b - a))) if b > a else float(t >= a)


# ---------------- zemin ----------------
def make_bg():
    im = Image.new('RGB', (W, H), CREAM); d = ImageDraw.Draw(im)
    for yy in range(60, GROUND_Y - 40, 120):
        for xx in range(60 + (60 if (yy // 120) % 2 else 0), W, 120):
            r = 14
            pts = []
            for k in range(16):
                a = math.pi * k / 8; rr = r if k % 2 == 0 else r * 0.45
                pts.append((xx + rr * math.cos(a), yy + rr * math.sin(a)))
            d.polygon(pts, fill=(238, 229, 210))
    d.rectangle([0, GROUND_Y, W, GROUND_Y + 14], fill=GOLD)
    d.rectangle([0, GROUND_Y + 14, W, H], fill=LAPIS)
    for xx in range(0, W + 1, 270):
        d.rectangle([xx - 2, GROUND_Y + 40, xx + 2, H], fill=(22, 42, 100))
    d.rectangle([0, 1640, W, 1644], fill=(22, 42, 100))
    for xx in range(135, W, 270):
        d.ellipse([xx - 7, 1600 - 7, xx + 7, 1600 + 7], fill=GOLD)
    return im


# ---------------- yazı yardımcıları ----------------
def text_img(text, size, color, cond=0.8):
    f = font(size); bb = f.getbbox(text)
    w, h = bb[2] - bb[0] + 4, bb[3] - bb[1] + 4
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - bb[0], 2 - bb[1]), text, font=f, fill=color)
    if cond != 1.0:
        im = im.resize((max(1, int(w * cond)), h), Image.LANCZOS)
    return im


def headline(fr, l1, l2, acc, t0, t, src=None):
    p = ease_out(prog(t, t0, t0 + 0.28))
    if p <= 0: return
    for k, (txt, col, y) in enumerate([(l1, INK, 118), (l2, acc, 236)]):
        if not txt: continue
        size = 112
        while True:
            im = text_img(txt, size, col)
            if im.width <= W - 80 or size < 60: break
            size -= 4
        pk = ease_out(prog(t, t0 + 0.06 * k, t0 + 0.06 * k + 0.28))
        im.putalpha(im.split()[3].point(lambda v, a=pk: int(v * a)))
        fr.alpha_composite(im, (int(40 - 60 * (1 - pk)), y))
    if src:
        ps = prog(t, t0 + 0.3, t0 + 0.6)
        if ps > 0:
            d = ImageDraw.Draw(fr)
            f = font(26); a = int(255 * ps)
            d.ellipse([42, 381, 54, 393], fill=BURG + (a,))
            d.text((64, 374), src, font=f, fill=(70, 60, 55, a))


def top_label(fr, txt):
    d = ImageDraw.Draw(fr)
    d.ellipse([40, 64, 54, 78], fill=BURG)
    d.text((64, 58), txt, font=font(26), fill=INK)


def sub_pill(fr, text, t0, t1, t, y=1470):
    if not (t0 <= t < t1 + 0.12): return
    p = ease_out(prog(t, t0, t0 + 0.12)); q = 1 - prog(t, t1, t1 + 0.12)
    a = p * q
    parts = []; hl = False
    for s in text.split('*'):
        if s: parts.append((s, hl))
        hl = not hl
    f = font(56)
    tw = sum(f.getlength(s) for s, _ in parts)
    pw, ph = tw + 60, 92
    L = Image.new('RGBA', (int(pw) + 20, ph + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rounded_rectangle([10, 14, pw + 10, ph + 14], radius=18, fill=(0, 0, 0, 70))
    d.rounded_rectangle([10, 8, pw + 10, ph + 8], radius=18, fill=WHITE)
    x = 40
    for s, h in parts:
        d.text((x, 24), s, font=f, fill=BURG if h else INK); x += f.getlength(s)
    sc = 0.85 + 0.15 * back(prog(t, t0, t0 + 0.16))
    L = L.resize((max(1, int(L.width * sc)), max(1, int(L.height * sc))), Image.BICUBIC)
    L.putalpha(L.split()[3].point(lambda v: int(v * a)))
    fr.alpha_composite(L, (int(W / 2 - L.width / 2), int(y - L.height / 2)))


def stamp(fr, text, cx, cy, t0, t, col=BURG, rot=-12, size=96):
    if t < t0: return
    p = prog(t, t0, t0 + 0.18)
    f = font(size); tw = f.getlength(text)
    w, h = int(tw + 70), int(size * 1.45)
    L = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rounded_rectangle([10, 10, w + 10, h + 10], radius=16, outline=col, width=10)
    d.text((10 + (w - tw) / 2, 10 + (h - size * 1.15) / 2), text, font=f, fill=col)
    L = L.rotate(rot, expand=True, resample=Image.BICUBIC)
    sc = 1.0 + 0.7 * (1 - ease_out(p))
    L = L.resize((int(L.width * sc), int(L.height * sc)), Image.BICUBIC)
    L.putalpha(L.split()[3].point(lambda v: int(v * min(1, p * 1.4))))
    fr.alpha_composite(L, (int(cx - L.width / 2), int(cy - L.height / 2)))


def badge(fr, text, cx, cy, t0, t, col=LAPIS, size=58):
    if t < t0: return
    p = back(prog(t, t0, t0 + 0.3))
    f = font(size); tw = f.getlength(text)
    w, h = int(tw + 60), int(size * 1.6)
    L = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=col)
    d.text(((w - tw) / 2, (h - size * 1.15) / 2), text, font=f, fill=WHITE)
    sc = max(0.05, p)
    L = L.resize((max(1, int(w * sc)), max(1, int(h * sc))), Image.BICUBIC)
    fr.alpha_composite(L, (int(cx - L.width / 2), int(cy - L.height / 2)))


def flag(d, px, top, w, h, t, base, emblem=None, emb_col=WHITE):
    pts_top, pts_bot = [], []
    for k in range(13):
        x = px + w * k / 12; wav = 10 * math.sin(t * 6 + k * 0.6) * (k / 12)
        pts_top.append((x, top + wav)); pts_bot.append((x, top + h + wav))
    d.polygon(pts_top + pts_bot[::-1], fill=base)
    if emblem == 'crescent':
        cx, cy = px + w * 0.45, top + h / 2 + 5 * math.sin(t * 6 + 3)
        r = h * 0.3
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=emb_col)
        d.ellipse([cx - r + r * 0.45, cy - r * 0.85, cx + r * 1.25, cy + r * 0.85], fill=base)
    if emblem == 'cross':
        cx, cy = px + w * 0.45, top + h / 2 + 5 * math.sin(t * 6 + 3)
        s = h * 0.32
        d.rectangle([cx - s * 0.18, cy - s, cx + s * 0.18, cy + s], fill=emb_col)
        d.rectangle([cx - s * 0.7, cy - s * 0.18, cx + s * 0.7, cy + s * 0.18], fill=emb_col)


def render(EP, out_path, workers=4):
    import multiprocessing as mp
    N = int(EP['total'] * FPS)
    tmpv = out_path + '.video.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', tmpv], stdin=subprocess.PIPE)
    with mp.Pool(workers) as pool:
        for fr in pool.imap(EP['frame_bytes'], range(N), chunksize=8):
            p.stdin.write(fr)
    p.stdin.close(); p.wait()
    a = EP['audio']; VO = a['vo_off']
    st = [int((x + VO) * 1000) for x in a.get('stamps', [])]
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-i', tmpv, '-i', a['vo'], '-i', a['music']]
    for _ in st: cmd += ['-i', a['stamp']]
    T, ES = EP['total'], EP['end_start']
    fc = (f'[1:a]adelay={int(VO*1000)}|{int(VO*1000)}[vo];'
          f"[2:a]atrim=0:{T},volume='if(lt(t,{ES}),0.12,0.12+0.22*min(1,(t-{ES})/0.6))':eval=frame,afade=t=out:st={T-1.2}:d=1.2[mu];")
    labels = ['[vo]', '[mu]']
    for k, dl in enumerate(st):
        fc += f'[{3+k}:a]adelay={dl}|{dl},volume=0.8[s{k}];'; labels.append(f'[s{k}]')
    fc += ''.join(labels) + f'amix=inputs={len(labels)}:normalize=0:duration=longest,atrim=0:{T},loudnorm=I=-14:TP=-1.5:LRA=11[a]'
    cmd += ['-filter_complex', fc, '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', str(T), out_path]
    subprocess.run(cmd, check=True)
    os.remove(tmpv)
