# Meraklopedi

Tarih, gizem, bilim ve şaşırtıcı gerçekleri bir araya getiren Instagram sayfası (@meraklopedim) için tasarım ve içerik dosyaları.

**Kimlik:** lacivert `#070B16` / `#16264A`, altın `#D9A441` (degrade `#F7DE9A → #A8741F`).
Başlıklar Caladea (Bold), metinler Inter. Logo: noktası gezegen olan soru işareti.

| Klasör | İçerik |
|---|---|
| `profil/` | Profil resmi. Seçilen: **`meraklopedi_C.png`** (soru işareti). A ve B alternatifleri, `ilk-taslaklar/` ilk isim fikri için yapılanlar |
| `hikaye-kapaklari/` | 6 öne çıkan hikâye kapağı: Tarih, Gizem, Bilim, Gerçekler, Maddeler, Soru-Cevap (1080×1920) |
| `carousel/madde001/` | Madde 001 · Ölümüne Dans, 6 sayfalık carousel (1080×1350) |
| `carousel/madde002/` | Madde 002 · Okunamayan Kitap (Voynich), 6 sayfalık carousel |
| `reels/madde001/` | Madde 001 Reels videosu (55 sn, 1080×1920), seslendirme kayıtları, çizimler, sahne kartları, altyazı |
| `reels/madde002/` | Madde 002 Reels videosu (54 sn), senaryo, seslendirme, çizimler, sahne kartları, altyazı |
| `reels-kapak/` | Reels kapak şablonu ve Madde 001 kapağı |

## Yeniden üretmek

Gerekenler: Node.js + Playwright (Chromium), ffmpeg (libass ile), Inter ve Caladea yazı tipleri.

- Profil / hikâye kapakları / carousel: ilgili klasörde `node gen.js`
- Reels videoları: `reels/madde001/olustur.sh`, `reels/madde002/olustur.sh`
- Yeni Reels kapağı: `reels-kapak/README.md`

## Kaynaklar

- Seslendirme: ElevenLabs, "Ayaz" sesi (eleven_v4). Videoda `ses/seslendirme_kayit1.mp3` kullanıldı.
- Çizimler: ElevenLabs üzerinden gpt-image-2.5 ile üretildi (`reels/madde001/cizimler/`).
- Madde 001 kaynağı: John Waller, *A Time to Dance, a Time to Die* (2008).

## Reels kuralları (Madde 003'ten itibaren)

- **Süre: en fazla 25 saniye.** (Madde 001 ve 002 yaklaşık 55 saniye.)
- Seslendirme metni yaklaşık 55–60 kelime: kanca (1 cümle) → olay (2 cümle) → şaşırtıcı detay (1–2 cümle) → kapanış sorusu.
- 5 sahne: 4 çizim ve 1 kapanış kartı. Her sahne 4–6 saniye.
- Altyazılar ve kart yazıları yukarıda, Instagram arayüzünün üstünde kalır. Kart yazıları 1200. pikselden aşağı inmez.
- Ayrıntılar carousel'de anlatılır, Reels açıklamasında carousel'e yönlendirilir.
