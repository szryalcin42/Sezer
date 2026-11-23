#!/usr/bin/env python3
"""Sezer konuşan videosuna başlık + altyazı ekler (ASS / libass, ek kredi yok).

Kullanım:  python3 altyazi_ekle.py
Girdi:     sezer_konusan_video.mp4
Çıktı:     sezer_reel_altyazili.mp4
Zamanlamalar sesteki duraklamalardan (ffmpeg silencedetect) alındı.
"""
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "sezer_konusan_video.mp4"
OUT = HERE / "sezer_reel_altyazili.mp4"
ASS = HERE / "altyazi.ass"

GOLD = r"{\c&H3DC8FF&}"   # ASS renkleri BGR: #FFC83D
WHITE = r"{\c&HFFFFFF&}"

def hl(text):
    """[kelime] -> altın renkli vurgu."""
    return text.replace("[", GOLD).replace("]", WHITE)

# (başlangıç, bitiş, metin) – saniye
SUBS = [
    (0.00, 1.55, "Merhaba, ben [Sezer]."),
    (1.55, 2.90, "Faizsiz ev mi?"),
    (2.90, 4.75, "İş var, ama [hile yok]."),
    (4.75, 6.45, "Her ay taksitini ödüyorsun;"),
    (6.45, 8.60, "her taksit, evinin bir [tuğlası]."),
    (8.60, 10.47, "Çekiliş yok, [kura yok]."),
    (10.47, 13.15, "Teslimat tarihin sözleşmede\\N[baştan belli]."),
    (13.15, 17.10, "Evine girdikten sonra kalan tutarı\\N[faizsiz taksitlerle] ödüyorsun."),
    (17.10, 18.85, "Acele yok, [hesap var]."),
    (18.85, 22.12, "Tuğlayı sen koy,\\N[anahtarı Katılımevim] versin!"),
]

def ts(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"

header = r"""[Script Info]
ScriptType: v4.00+
PlayResX: 1088
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Baslik,Inter ExtraBold,78,&H00FFFFFF,&H00FFFFFF,&H00502A14,&H00502A14,-1,0,0,0,100,100,0,0,3,26,0,8,60,60,150,1
Style: AltBaslik,Inter SemiBold,44,&H003DC8FF,&H00FFFFFF,&H00502A14,&H00502A14,-1,0,0,0,100,100,1,0,3,12,0,8,60,60,262,1
Style: Altyazi,Inter ExtraBold,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,3,2,70,70,170,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

events = [
    # Başlık: lacivert kutu, baştan sona, yukarıdan kayarak gelir
    f"Dialogue: 1,{ts(0)},{ts(22.12)},Baslik,,0,0,0,,"
    r"{\fad(300,0)\move(544,90,544,150,0,350)\an8}Ödeme planı nasıl işler?",
    f"Dialogue: 1,{ts(0.3)},{ts(22.12)},AltBaslik,,0,0,0,,"
    r"{\fad(400,0)}Sezer · Katılımevim Danışmanı",
]
for start, end, text in SUBS:
    events.append(
        f"Dialogue: 0,{ts(start)},{ts(end)},Altyazi,,0,0,0,,"
        r"{\fad(80,60)\t(0,120,\fscx104\fscy104)\t(120,220,\fscx100\fscy100)}" + hl(text)
    )

ASS.write_text(header + "\n".join(events) + "\n", encoding="utf-8")

subprocess.run([
    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
    "-i", str(SRC),
    "-vf", f"ass={ASS.name}",
    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
    "-c:a", "copy", "-movflags", "+faststart",
    str(OUT),
], check=True, cwd=HERE)
print("Yazıldı:", OUT)
