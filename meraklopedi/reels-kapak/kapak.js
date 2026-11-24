// Meraklopedi Reels kapak şablonu (1080x1920).
// Kullanım:
//   node kapak.js --madde 001 --baslik "Ölümüne|Dans" --alt "STRAZBURG · 1518" \
//     --gorsel gorseller/madde001_dans.png --konum "46% 0" --cikti ciktilar/madde001_kapak.png
// Başlıkta "|" satır sonu demektir. --konum, arka plan görselinin yatay/dikey hizasıdır
// (görsel 16:9 ise yüzü ortalamak için ilk değeri değiştirin).
// Gerekenler: Node.js + Playwright (Chromium), Caladea ve Inter yazı tipleri.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) =>
  v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a, []));
const madde = args.madde || '001';
const baslik = (args.baslik || 'Ölümüne|Dans').split('|').join('<br>');
const alt = args.alt || 'STRAZBURG · 1518';
const gorsel = path.resolve(__dirname, args.gorsel || 'gorseller/madde001_dans.png');
const konum = args.konum || '46% 0';
const cikti = path.resolve(__dirname, args.cikti || `ciktilar/madde${madde}_kapak.png`);
const boyut = Number(args.boyut || 200); // başlık punto

const img = 'data:image/png;base64,' + fs.readFileSync(gorsel).toString('base64');
const logo = 'data:image/svg+xml;base64,' + fs.readFileSync(path.join(__dirname, 'logo.svg')).toString('base64');

const html = `<html><head><style>*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;position:relative;overflow:hidden;background:#070B16;font-family:Inter;color:#EDE6D3}
.bg{position:absolute;inset:0;background:url(${img}) ${konum}/auto 100% no-repeat}
.sh{position:absolute;inset:0;background:linear-gradient(180deg,rgba(7,11,22,.85) 0%,rgba(7,11,22,.15) 18%,rgba(7,11,22,0) 38%,rgba(7,11,22,.55) 58%,rgba(7,11,22,.95) 78%,#070B16 100%)}
.c{position:absolute;left:70px;right:70px;text-align:center}
.gold{background:linear-gradient(135deg,#F7DE9A,#D9A441 55%,#A8741F);-webkit-background-clip:text;color:transparent}
.serif{font-family:Caladea,serif;font-weight:700}
.pill{display:inline-block;border:3px solid #D9A441;color:#F3D58A;border-radius:60px;padding:14px 36px;font-size:38px;letter-spacing:9px;font-weight:600;background:rgba(7,11,22,.6)}
</style></head><body><div class="bg"></div><div class="sh"></div>
<div class="c" style="top:1010px"><span class="pill">MADDE ${madde}</span></div>
<div class="c" style="top:1120px"><div class="serif gold" style="font-size:${boyut}px;line-height:.95;filter:drop-shadow(0 6px 18px rgba(0,0,0,.7))">${baslik}</div>
<div style="font-size:42px;letter-spacing:12px;color:#D9A441;font-weight:600;margin-top:34px">${alt}</div></div>
<div class="c" style="top:1700px"><img src="${logo}" style="width:96px;height:96px;border-radius:50%"/></div>
</body></html>`;

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.setContent(html);
  await p.waitForTimeout(300);
  fs.mkdirSync(path.dirname(cikti), { recursive: true });
  await p.screenshot({ path: cikti });
  await b.close();
  console.log('Kaydedildi:', cikti);
})();
