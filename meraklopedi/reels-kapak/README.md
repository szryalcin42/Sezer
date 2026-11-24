# Meraklopedi · Reels kapak şablonu

Her "Madde" Reels'i için aynı tasarımda kapak üretir (1080×1920).

- Arka planda sahnenin çizimi; alt kısım koyulaşarak yazıya yer açar.
- Ortada **MADDE ###** etiketi, altın serif başlık ve alt başlık (yer · yıl).
- En altta Meraklopedi logosu (`logo.svg`).
- Bütün yazılar profil ızgarasının 3:4 kırpma alanının içinde kalır.

Renkler: lacivert `#070B16` / `#16264A`, altın `#D9A441` (degrade `#F7DE9A → #A8741F`).
Yazı tipleri: başlık Caladea (Bold), diğerleri Inter.

## Yeni kapak üretmek

```bash
node kapak.js --madde 002 --baslik "Voynich|El Yazması" --alt "İTALYA · 1400'LER" \
  --gorsel gorseller/madde002.png --konum "50% 0"
```

Çıktı `ciktilar/madde002_kapak.png` olarak kaydedilir.

## Dosyalar

- `kapak.js` — şablon
- `logo.svg` — profil logosu (gezegenli soru işareti)
- `gorseller/madde001_dans.png` — Madde 001 çizimi
- `ciktilar/madde001_kapak.png` — Madde 001 kapağı
