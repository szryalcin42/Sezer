#!/usr/bin/env bash
# Madde 004 Reels videosunu yeniden oluşturur.
# Gerekenler: ffmpeg (libass ile), Node.js + Playwright, Inter ve Caladea yazı tipleri.
# Kullanım: ./olustur.sh [cikti.mp4]
set -euo pipefail
cd "$(dirname "$0")"
OUT="${1:-meraklopedi_madde004_reels.mp4}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# 1) Sahne kartlarını çiz (kartlar/*.png)
node kartlar.js

# 2) Her sahne için yavaş yakınlaşma/uzaklaşma klibi (segs.txt: ad başlangıç bitiş yön)
: > "$TMP/list.txt"
while read -r n s e d; do
  fr=$(python3 -c "print(round(($e-$s)*30))")
  if [ "$d" = in ]; then z="1+0.10*on/$fr"; else z="1.10-0.10*on/$fr"; fi
  ffmpeg -nostdin -loglevel error -y -loop 1 -i "kartlar/$n.png" \
    -vf "scale=2160:3840,zoompan=z='$z':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$fr:s=1080x1920:fps=30,format=yuv420p" \
    -frames:v "$fr" -c:v libx264 -preset veryfast -crf 18 "$TMP/$n.mp4"
  echo "file '$TMP/$n.mp4'" >> "$TMP/list.txt"
done < segs.txt
ffmpeg -nostdin -loglevel error -y -f concat -safe 0 -i "$TMP/list.txt" -c copy "$TMP/video.mp4"

# 3) Arka plan uğultusu (sentez)
ffmpeg -nostdin -loglevel error -y -f lavfi -i "sine=f=55:d=27" -f lavfi -i "sine=f=82.4:d=27" \
  -f lavfi -i "sine=f=110:d=27" -f lavfi -i "anoisesrc=d=56:c=brown:a=0.05" \
  -filter_complex "[0]volume=0.5,tremolo=f=0.15:d=0.6[a];[1]volume=0.35,tremolo=f=0.11:d=0.7[b];[2]volume=0.15,tremolo=f=0.23:d=0.8[c];[3]lowpass=f=400[d];[a][b][c][d]amix=4:normalize=0,lowpass=f=900,afade=t=in:d=2,afade=t=out:st=23:d=2,volume=0.6" \
  -ar 44100 "$TMP/muzik.wav"

# 4) Seslendirme + müzik + altyazı + vinyet/gren
ffmpeg -nostdin -loglevel error -y -i "$TMP/video.mp4" -i ses/seslendirme_25sn.mp3 -i "$TMP/muzik.wav" \
  -filter_complex "[0:v]vignette=PI/5,noise=alls=2:allf=t,ass=alt.ass,fade=t=in:d=0.5,format=yuv420p[v];[2:a]volume=0.22[m];[1:a][m]amix=2:duration=longest:normalize=0,alimiter=limit=0.95[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 23 -maxrate 8M -bufsize 16M \
  -c:a aac -b:a 192k -movflags +faststart -t 25.0 "$OUT"
echo "Hazır: $OUT"
