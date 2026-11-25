const { chromium } = require('playwright');
const fs = require('fs');
const logo = 'data:image/svg+xml;base64,'+fs.readFileSync('../../profil/meraklopedi_C.svg').toString('base64');
const MADDE='005', TOTAL=6;
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
`<div class="wm">?</div><div class="content">
 <div class="kicker">BİLİM ✦ GERÇEK</div>
 <h1 class="serif gold" style="font-size:132px">Bozulmayan<br>Yiyecek</h1>
 <div class="rule"></div>
 <p style="font-size:44px">Mutfağındaki bal,<br>sen yaşlandığında bile<br><b>bozulmamış</b> olabilir.<br>Peki nasıl?</p>
 <p style="margin-top:40px;font-size:30px;letter-spacing:6px;color:#D9A441">BAL NEDEN BOZULMAZ?</p></div>`,

`<div class="content"><div class="kicker">ANTİK MISIR</div>
 <h2 class="serif gold">Mezardan çıkan<br>bal</h2>
 <p>Arkeologlar Mısır mezarlarında <b>binlerce yıllık</b> bal çömlekleri buldu.</p>
 <p style="margin-top:30px">Bal hâlâ korunmuştu. Çok az yiyecek bu kadar uzun süre dayanabilir. Sırrı balın kimyasında.</p></div>`,

`<div class="content"><div class="kicker">1. SIR: SUSUZLUK</div>
 <div class="big serif gold" style="font-size:240px">%17</div>
 <div class="rule"></div>
 <p>Balın yalnızca yaklaşık <b>%17'si su</b>, büyük kısmı şeker.</p>
 <p style="margin-top:30px">Bu kadar şekerli ve az sulu bir ortamda bakteri ve mayalar suyunu kaybeder ve çoğalamaz.</p></div>`,

`<div class="content"><div class="kicker">2. VE 3. SIR</div>
 <h2 class="serif gold">Asit ve<br>arıların enzimi</h2>
 <p>Bal <b>asidiktir</b>: pH değeri ortalama 3,9 civarında. Mikroplar bu ortamı sevmez.</p>
 <p style="margin-top:30px">Arılar bala <b>glukoz oksidaz</b> enzimini katar. Bal sulandığında bu enzim az miktarda <b>hidrojen peroksit</b> üretir: doğal bir mikrop öldürücü.</p></div>`,

`<div class="content"><div class="kicker">BİLMEN GEREKENLER</div>
 <h2 class="serif gold" style="font-size:76px">Balını koru</h2>
 <div class="list">
  <div class="item"><div class="num">1</div><div><h3>Kapağı kapalı tut</h3><p>Bal havadaki nemi çeker. Su oranı artarsa mayalanabilir.</p></div></div>
  <div class="item"><div class="num">2</div><div><h3>Kristalleşme bozulma değil</h3><p>Donan bal bozulmuş değildir. Kavanozu ılık suda bekletince eski hâline döner.</p></div></div>
  <div class="item"><div class="num">3</div><div><h3>Bebeklere verilmez</h3><p>1 yaşından küçük bebeklere bal verilmemeli: bebek botulizmi riski var.</p></div></div>
 </div></div>`,

`<div class="wm">?</div><div class="content">
 <div class="kicker">SIRA SENDE</div>
 <h1 class="serif gold" style="font-size:112px">Bunu bal seven<br>birine gönder</h1>
 <div class="rule"></div>
 <p>Evindeki en eski yiyecek ne?<br>Yorumlara yaz, <b>takipte kal.</b></p>
 <div class="cta"><span>📩 Gönder</span><span>🔖 Kaydet</span></div>
 <div class="src">Kaynaklar: Smithsonian Magazine, "The Science Behind Honey's Eternal Shelf Life" (2013) · ABD Hastalık Kontrol Merkezleri (CDC), bebek botulizmi</div></div>`
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
