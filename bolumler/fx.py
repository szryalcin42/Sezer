# Kodla animasyon efektleri (yapay zekâ video modeli kullanmadan).
# Her sahnenin "fx" ayarı: parallax, smoke, clouds, water, birds, rays, embers.
import math
import numpy as np
from PIL import Image, ImageDraw

W, H = 1080, 1920


def _noise(w, h, scale, seed):
    r = np.random.default_rng(seed)
    small = r.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    return np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255


def fbm(w, h, seed, scales=(256, 128, 64, 32)):
    n = np.zeros((h, w), np.float32); a = 1.0; tot = 0.0
    for k, s in enumerate(scales):
        n += a * _noise(w, h, s, seed + k); tot += a; a *= 0.5
    return n / tot


SMOKE = fbm(W, H * 2, 3, (192, 96, 48, 24))
CLOUD = fbm(W * 2, 760, 7, (320, 160, 80, 40))
INK = fbm(W, H, 21, (320, 160, 80, 40))
SPARK = np.random.default_rng(5).random((H, W)).astype(np.float32)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
_cache = {}


def smoke(arr, t, plumes):
    key = ('smoke', tuple(map(tuple, plumes)))
    if key not in _cache:
        m = np.zeros((H, W), np.float32)
        for fx_, fy in plumes:
            bx, by = fx_ * W, fy * H
            up = np.clip(by - YY, 0, None)
            width = 30 + up * 0.32
            sway = 40 * np.sin(up / 160.0)
            g = np.exp(-((XX - bx - sway) ** 2) / (2 * width ** 2))
            fade = np.clip(up / 80, 0, 1) * np.clip(1 - up / 900, 0, 1)
            m = np.maximum(m, g * fade)
        _cache[key] = m
    m = _cache[key]
    rows = (np.arange(H) + int(t * 75)) % (2 * H)
    n = SMOKE[rows]
    a = (np.clip(n * 2.2 - 0.7, 0, 1) * m * 0.75)[..., None]
    col = np.array([196, 190, 180], np.float32)
    return arr * (1 - a) + col * a


def clouds(arr, t):
    sh = int(t * 22) % (2 * W)
    c = np.roll(CLOUD, -sh, axis=1)[:, :W]
    hh = c.shape[0]
    fade = np.clip(1 - np.arange(hh) / hh, 0, 1)[:, None] ** 1.2
    a = (np.clip(c * 2.0 - 1.0, 0, 1) * fade * 0.38)[..., None]
    col = np.array([250, 244, 228], np.float32)
    arr[:hh] = arr[:hh] * (1 - a) + col * a
    return arr


def water(arr, t, yr):
    y0, y1 = int(yr[0] * H), int(yr[1] * H)
    seg = arr[y0:y1]
    r, g, b = seg[..., 0], seg[..., 1], seg[..., 2]
    mask = (b > r + 18) & (b > g - 6)
    ys = np.arange(y0, y1, dtype=np.float32)
    off = (3.2 * np.sin(ys * 0.09 + t * 3.1) + 1.6 * np.sin(ys * 0.031 - t * 1.7)).astype(np.int32)
    xs = np.clip(np.arange(W)[None, :] + off[:, None], 0, W - 1)
    warped = np.take_along_axis(seg, xs[..., None].repeat(3, axis=2), axis=1)
    seg = np.where(mask[..., None], warped, seg)
    sp = SPARK[y0:y1]
    tw = 0.5 + 0.5 * np.sin(t * 5.0 + sp * 60.0)
    s = ((sp > 0.9965) & mask) * tw
    seg = seg + (s[..., None] * np.array([150, 150, 120], np.float32))
    arr[y0:y1] = seg
    return arr


def rays(arr, t, src):
    key = ('rays', tuple(src))
    if key not in _cache:
        sx, sy = src[0] * W, src[1] * H
        ang = np.arctan2(YY - sy, XX - sx)
        dist = np.sqrt((XX - sx) ** 2 + (YY - sy) ** 2)
        fall = np.clip(1 - dist / (H * 0.85), 0, 1) ** 2
        _cache[key] = (ang, fall)
    ang, fall = _cache[key]
    r = (0.5 + 0.5 * np.sin(ang * 11 + t * 0.5)) ** 3 * (0.6 + 0.4 * np.sin(ang * 5 - t * 0.3))
    a = (r * fall * 0.17)[..., None]
    return np.clip(arr + a * np.array([255, 214, 140], np.float32), 0, 255)


def birds_layer(t, n, seed=3):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    rnd = np.random.default_rng(seed)
    for k in range(n):
        y0 = rnd.uniform(380, 760); sp = rnd.uniform(70, 120); ph = rnd.uniform(0, 6.28)
        x = (rnd.uniform(-300, W) + sp * t) % (W + 300) - 150
        y = y0 + 18 * math.sin(t * 0.8 + ph)
        s = rnd.uniform(10, 17); f = math.sin(t * 11 + ph) * s * 0.6
        d.line([(x - s, y - f), (x, y + s * 0.15), (x + s, y - f)], fill=(40, 30, 25, 220), width=3, joint='curve')
    return L


def embers_layer(t, n=40, seed=9):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    rnd = np.random.default_rng(seed)
    for k in range(n):
        x0 = rnd.uniform(0, W); y0 = rnd.uniform(0, H); vy = rnd.uniform(40, 110); ph = rnd.uniform(0, 6.28); r = rnd.uniform(2, 4.5)
        y = (y0 - vy * t) % H; x = x0 + 25 * math.sin(t * 1.4 + ph)
        a = int(140 + 110 * math.sin(t * 3 + ph))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 170, 70, max(0, a)))
    return L


def apply(img, t, fx):
    """img: PIL RGB sahne karesi; fx: sahne efekt ayarları. PIL RGB döner."""
    if not fx:
        return img
    arr = np.asarray(img).astype(np.float32)
    if 'shake' in fx:
        amp = fx['shake'] * (0.55 + 0.45 * math.sin(t * 1.7))
        dx = int(amp * math.sin(t * 47.0) + amp * 0.5 * math.sin(t * 83.0)); dy = int(amp * 0.7 * math.sin(t * 59.0 + 1.0))
        arr = np.roll(np.roll(arr, dx, axis=1), dy, axis=0)
    if 'water' in fx: arr = water(arr, t, fx['water'])
    if 'clouds' in fx: arr = clouds(arr, t)
    if 'smoke' in fx: arr = smoke(arr, t, fx['smoke'])
    if 'rays' in fx: arr = rays(arr, t, fx['rays'])
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if 'birds' in fx or 'embers' in fx:
        out = out.convert('RGBA')
        if 'birds' in fx: out.alpha_composite(birds_layer(t, int(fx['birds'])))
        if 'embers' in fx: out.alpha_composite(embers_layer(t, int(fx['embers'])))
        out = out.convert('RGB')
    return out


def ink_mix(prev, cur, p):
    """Mürekkep yayılması geçişi: p 0→1."""
    m = np.clip((p * 1.3 - INK * 0.95 - 0.18) / 0.09, 0, 1)
    edge = np.exp(-((m - 0.5) ** 2) / 0.02) * 0.55
    a, b = np.asarray(prev).astype(np.float32), np.asarray(cur).astype(np.float32)
    o = a * (1 - m[..., None]) + b * m[..., None]
    o = o * (1 - edge[..., None]) + np.array([30, 18, 10], np.float32) * edge[..., None]
    return Image.fromarray(np.clip(o, 0, 255).astype(np.uint8))
