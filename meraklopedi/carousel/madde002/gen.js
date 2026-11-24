const { chromium } = require('playwright');
const fs = require('fs');
const logo = 'data:image/svg+xml;base64,'+fs.readFileSync('../../profil/meraklopedi_C.svg').toString('base64');
const MADDE='002', TOTAL=6;
const {parsomen}=require('./parsomen.js');
const pars=(seed,w=900,h=1300)=>'data:image/svg+xml;base64,'+Buffer.from(parsomen(w,h,seed)).toString('base64');
const css = `
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;font-family:Inter;color:#E9E3D3;
 background:radial-gradient(ellipse at 50% 35%,#16264A 0%,#0B1224 60%,#060A14 100%);position:relative;overflow:hidden}
.frame{position:absolute;inset:36px;border:2px solid rgba(217,164,65,.55);border-radius:6px}
.top{position:absolute;top:70px;left:90px;right:90px;display:flex;justify-content:space-between;align-items:center;
 font-size:22px;letter-spacing:6px;font-weight:600;color:#D9A441}
.top .tag{border:2px solid #D9A441;padding:8px 18px;border-radius:40px;letter-spacing:4px}
.bot{position:absolute;bottom:70px;left:90px;right:90px;display:flex;justify-content:space-between;align-items:center;
 font-size:22px;letter-spacing:4px;color:rgba(233,227,211,.6)}
.bot img{width:64px;height:64px;border-radius:50%}
.gold{background:linear-gradient(135deg,#F3D58A,#D9A441 55%,#A8741F);-webkit-background-clip:text;color:transparent}
.serif{font-family:Caladea,serif}
.content{position:absolute;top:200px;left:90px;right:90px;bottom:180px;display:flex;flex-direction:column;justify-content:center}
.kicker{font-size:26px;letter-spacing:8px;color:#D9A441;font-weight:600;margin-bottom:28px}
h1{font-size:150px;line-height:1;font-weight:700}
h2{font-size:86px;line-height:1.05;font-weight:700;margin-bottom:40px}
p{font-size:40px;line-height:1.5;font-weight:400}
p b{color:#F3D58A;font-weight:600}
.rule{width:120px;height:4px;background:#D9A441;margin:44px 0}
.stars{position:absolute;inset:0;pointer-events:none}
.big{font-size:200px;line-height:1;font-weight:700}
.list{display:flex;flex-direction:column;gap:34px}
.item{display:flex;gap:30px;align-items:flex-start}
.num{flex:none;width:76px;height:76px;border-radius:50%;border:3px solid #D9A441;display:flex;align-items:center;justify-content:center;
 font-family:Caladea,serif;font-size:40px;font-weight:700;color:#D9A441}
.item h3{font-size:42px;color:#F3D58A;margin-bottom:6px}
.item p{font-size:34px;line-height:1.4}
.wm{position:absolute;right:-60px;bottom:120px;font-family:Caladea,serif;font-size:900px;font-weight:700;line-height:.8;color:rgba(217,164,65,.07)}
.src{font-size:26px;line-height:1.5;color:rgba(233,227,211,.6);margin-top:50px;border-top:1px solid rgba(217,164,65,.4);padding-top:26px}
.cta{display:flex;gap:24px;margin-top:20px}
.cta span{border:2px solid #D9A441;color:#F3D58A;padding:16px 28px;border-radius:50px;font-size:30px;font-weight:600}
`;
function stars(n,seed){let s=seed;const r=()=>{s=(s*9301+49297)%233280;return s/233280};let o='<svg class="stars" width="1080" height="1350">';
 for(let i=0;i<n;i++)o+=`<circle cx="${(r()*1080).toFixed(0)}" cy="${(r()*1350).toFixed(0)}" r="${(1+r()*2.5).toFixed(1)}" fill="#F3E3B5" opacity="${(0.15+r()*0.45).toFixed(2)}"/>`;return o+'</svg>';}
const page=(i,body,{showTop=true}={})=>`<html><head><style>${css}</style></head><body>${stars(60,i*7+3)}<div class="frame"></div>
${showTop?`<div class="top"><span>MERAKLOPEDİ</span><span class="tag">MADDE ${MADDE}</span></div>`:''}
${body}
<div class="bot"><img src="${logo}"/><span>${String(i).padStart(2,'0')} / ${String(TOTAL).padStart(2,'0')}</span><span>${i<TOTAL?'KAYDIR →':'@meraklopedim'}</span></div></body></html>`;

const slides=[
`<img src="${pars(7)}" style="position:absolute;right:-230px;top:560px;width:600px;transform:rotate(10deg);opacity:.22;filter:sepia(.3)"/>
<div class="content">
 <div class="kicker">GİZEM ✦ BİLİM</div>
 <h1 class="serif gold">Okunamayan<br>Kitap</h1>
 <div class="rule"></div>
 <p style="font-size:44px">600 yıllık bir el yazması.<br>Bilinmeyen bir alfabe.<br>Ve hâlâ <b>tek bir kelimesi</b><br>çözülemedi.</p>
 <p style="margin-top:40px;font-size:30px;letter-spacing:6px;color:#D9A441">VOYNICH EL YAZMASI</p></div>`,

`<div class="content"><div class="kicker">1912 · ROMA YAKINLARI</div>
 <h2 class="serif gold">Bir sandık<br>eski kitap</h2>
 <p>Kitapçı <b>Wilfrid Voynich</b>, Cizvitlere ait Villa Mondragone'den bir grup eski el yazması satın aldı.</p>
 <p style="margin-top:30px">Aralarında biri vardı ki <b>hiçbir dile benzemiyordu.</b> Kitap bugün onun adıyla anılıyor.</p></div>`,

`<div class="content"><div class="kicker">KARBON TESTİ · 2009</div>
 <div class="big serif gold" style="font-size:170px">1404–1438</div>
 <div class="rule"></div>
 <p>Arizona Üniversitesi'nin testine göre kitabın parşömeni bu yıllar arasında üretildi.</p>
 <p style="margin-top:30px">Yani kitap gerçekten <b>Orta Çağ'ın sonlarından</b> kalma.</p></div>`,

`<img src="${pars(19)}" style="position:absolute;left:50%;top:165px;width:450px;transform:translateX(-50%) rotate(-3deg);box-shadow:0 20px 60px rgba(0,0,0,.6)"/>
<div class="content" style="top:880px;bottom:150px;justify-content:flex-start"><div class="kicker">İÇİNDE NE VAR?</div>
 <p style="font-size:34px">Yaklaşık <b>240 sayfa</b>: kimsenin tanımlayamadığı bitkiler, yıldız haritaları, havuzlarda yıkanan figürler, ilaç kavanozları… Ve hepsinin yanında <b>bilinmeyen bir yazı.</b></p></div>
<div style="position:absolute;left:90px;right:90px;top:835px;font-size:20px;color:rgba(233,227,211,.5);text-align:center">Temsilî çizim: Meraklopedi</div>`,

`<div class="content"><div class="kicker">KİMLER DENEDİ?</div>
 <h2 class="serif gold" style="font-size:72px;margin-bottom:30px">Kod kırıcılar bile<br>pes etti</h2>
 <p style="font-size:34px;margin-bottom:34px">II. Dünya Savaşı'nın ünlü kriptologu <b>William Friedman</b> dâhil yüzlerce uzman denedi. 3 ana teori var:</p>
 <div class="list">
  <div class="item"><div class="num">1</div><div><h3>Şifreli bir metin</h3><p>Bilinen bir dil, gizli bir sistemle yazıldı.</p></div></div>
  <div class="item"><div class="num">2</div><div><h3>Kayıp bir dil</h3><p>Metin, gerçek dillere benzer istatistiksel düzen gösteriyor.</p></div></div>
  <div class="item"><div class="num">3</div><div><h3>Usta işi bir aldatmaca</h3><p>Anlamsız ama anlamlı görünecek şekilde üretildi.</p></div></div>
 </div></div>`,

`<div class="wm">?</div><div class="content">
 <div class="kicker">SIRA SENDE</div>
 <h1 class="serif gold" style="font-size:120px">Sence ne<br>yazıyor?</h1>
 <div class="rule"></div>
 <p>Tahminini yorumlara yaz.<br>Kitabın tüm sayfaları Yale Üniversitesi'nin sitesinde <b>ücretsiz</b> incelenebiliyor.</p>
 <div class="cta"><span>🔖 Kaydet</span><span>↗ Paylaş</span></div>
 <div class="src">Kaynak: Yale Üniversitesi Beinecke Kütüphanesi, MS 408 · Karbon tarihlendirmesi: Arizona Üniversitesi (2009)</div></div>`
];

(async()=>{
 const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1080,height:1350}});
 const paths=[];
 for(let i=0;i<slides.length;i++){const f=`madde${MADDE}_${String(i+1).padStart(2,'0')}.png`;
  await p.setContent(page(i+1,slides[i])); await p.waitForTimeout(250); await p.screenshot({path:f}); paths.push(f);}
 // önizleme ızgarası
 const img=f=>'data:image/png;base64,'+fs.readFileSync(f).toString('base64');
 const q=await b.newPage({viewport:{width:1500,height:1000}});
 await q.setContent(`<body style="margin:0;background:#eee;padding:30px;display:grid;grid-template-columns:repeat(3,460px);gap:20px">${paths.map(f=>`<img src="${img(f)}" style="width:460px;border-radius:8px"/>`).join('')}</body>`);
 await q.waitForTimeout(300); await q.screenshot({path:'onizleme.png',fullPage:true});
 await b.close();})();
