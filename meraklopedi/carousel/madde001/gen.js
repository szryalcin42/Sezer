const { chromium } = require('playwright');
const fs = require('fs');
const logo = 'data:image/svg+xml;base64,'+fs.readFileSync('../../profil/meraklopedi_C.svg').toString('base64');
const MADDE='001', TOTAL=6;
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
 <div class="kicker">TARİH ✦ GİZEM</div>
 <h1 class="serif gold">Ölümüne<br>Dans</h1>
 <div class="rule"></div>
 <p style="font-size:44px">1518'de bir şehirde insanlar<br><b>durmadan dans etmeye</b> başladı.<br>Kimse nedenini bilmiyordu.</p>
 <p style="margin-top:40px;font-size:30px;letter-spacing:6px;color:#D9A441">STRAZBURG · 1518</p></div>`,

`<div class="content"><div class="kicker">TEMMUZ 1518</div>
 <h2 class="serif gold">Her şey tek bir<br>kadınla başladı</h2>
 <p><b>Frau Troffea</b> adlı bir kadın, Strazburg'un dar sokaklarından birinde aniden dans etmeye başladı.</p>
 <p style="margin-top:30px">Müzik yoktu. Kutlama yoktu.<br>Ve günlerce <b>durmadı.</b></p></div>`,

`<div class="content"><div class="kicker">SALGIN BÜYÜYOR</div>
 <div class="big serif gold">Yüzlerce</div>
 <div class="rule"></div>
 <p>Bir hafta içinde ona onlarca kişi katıldı. Bazı kayıtlara göre bir ay içinde sayı <b>yüzlerce kişiye</b> ulaştı.</p>
 <p style="margin-top:30px">Bitkinlikten yere yığılanlar oldu. Ölüm sayıları ise <b>bugün hâlâ tartışmalı.</b></p></div>`,

`<div class="content"><div class="kicker">TUHAF ÇÖZÜM</div>
 <h2 class="serif gold">Yetkililer<br>daha çok müzik istedi</h2>
 <p>Hekimlere göre sorun "sıcak kan"dı. Çözüm: <b>dans ederek atmak.</b></p>
 <p style="margin-top:30px">Şehir müzisyen tuttu, dans için alan ve sahne hazırladı.</p>
 <p style="margin-top:30px">Sonuç? Salgın <b>daha da büyüdü.</b></p></div>`,

`<div class="content"><div class="kicker">PEKİ NEDEN?</div>
 <h2 class="serif gold">3 teori</h2>
 <div class="list">
  <div class="item"><div class="num">1</div><div><h3>Kitlesel psikojenik hastalık</h3><p>Açlık, salgın ve korkunun yarattığı toplu bir stres tepkisi. Bugün en çok kabul gören açıklama.</p></div></div>
  <div class="item"><div class="num">2</div><div><h3>Çavdar mahmuzu</h3><p>Küflü çavdardaki zehir sanrı ve kasılmalara yol açar. Ama günlerce dans ettirmesi pek olası değil.</p></div></div>
  <div class="item"><div class="num">3</div><div><h3>Aziz Vitus laneti</h3><p>Halk, bu azizin insanları dansla cezalandırdığına inanıyordu. İnanç, davranışı besledi.</p></div></div>
 </div></div>`,

`<div class="wm">?</div><div class="content">
 <div class="kicker">SIRA SENDE</div>
 <h1 class="serif gold" style="font-size:120px">Sence ne<br>oldu?</h1>
 <div class="rule"></div>
 <p>Cevabını yorumlara yaz.<br>Bir sonraki madde için <b>takipte kal.</b></p>
 <div class="cta"><span>🔖 Kaydet</span><span>↗ Paylaş</span></div>
 <div class="src">Kaynak: John Waller, <i>A Time to Dance, a Time to Die: The Extraordinary Story of the Dancing Plague of 1518</i> (2008)</div></div>`
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
