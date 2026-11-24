// Madde 004 sahne kartları (1080x1920). cizimler/ klasöründeki görselleri kullanır.
const { chromium } = require('playwright');
const fs=require('fs');
const img=f=>'data:image/png;base64,'+fs.readFileSync('cizimler/'+f).toString('base64');
const logo='data:image/svg+xml;base64,'+fs.readFileSync('../../profil/meraklopedi_C.svg').toString('base64');
const css=`*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;position:relative;font-family:Inter;color:#EDE6D3;background:#070B16}
.bg{position:absolute;inset:0;background-repeat:no-repeat;background-size:auto 100%}
.shade{position:absolute;inset:0}.stars{position:absolute;inset:0}
.c{position:absolute;left:80px;right:80px;text-align:center}
.serif{font-family:Caladea,serif;font-weight:700}
.gold{background:linear-gradient(135deg,#F7DE9A,#D9A441 55%,#A8741F);-webkit-background-clip:text;color:transparent}
.kick{font-size:40px;letter-spacing:12px;color:#D9A441;font-weight:600}
.pill{display:inline-block;border:3px solid #D9A441;color:#F3D58A;border-radius:60px;padding:14px 34px;font-size:36px;letter-spacing:8px;font-weight:600;background:rgba(7,11,22,.55)}`;
function stars(n,seed){let s=seed;const r=()=>{s=(s*9301+49297)%233280;return s/233280};let o='<svg class="stars" width="1080" height="1920">';
 for(let i=0;i<n;i++)o+=`<circle cx="${(r()*1080)|0}" cy="${(r()*1920)|0}" r="${(1+r()*3).toFixed(1)}" fill="#F3E3B5" opacity="${(0.15+r()*0.5).toFixed(2)}"/>`;return o+'</svg>';}
const bg=(f,pos,filter='')=>`<div class="bg" style="background-image:url(${img(f)});background-position:${pos};filter:${filter}"></div>`;
const grad=`<div class="shade" style="background:linear-gradient(180deg,rgba(7,11,22,.55) 0%,rgba(7,11,22,0) 22%,rgba(7,11,22,0) 55%,rgba(7,11,22,.85) 100%)"></div>`;
const navy=`<div class="shade" style="background:radial-gradient(ellipse at 50% 40%,#17284D 0%,#0B1224 60%,#05080F 100%)"></div>`;
const P=JSON.parse(fs.readFileSync('konumlar.json','utf8')); // her çizim için yatay hiza
const cards={
 s1: bg('1_cadir.png',P['1_cadir'])+grad+`<div class="c" style="top:260px"><span class="pill">URAL DAĞLARI · 1959</span></div>`,
 s2: bg('2_izler.png',P['2_izler'])+grad+`<div class="c" style="top:260px"><span class="pill">9 DAĞCI · 1 GECE</span></div>`,
 s3: bg('3_dosya.png',P['3_dosya'])+grad+`<div class="c" style="top:260px"><span class="pill">DOSYA KAPANDI · 1959</span></div>`,
 s4: bg('4_cig.png',P['4_cig'])+grad+`<div class="c" style="top:260px"><span class="pill">RESMÎ SONUÇ · 2020: ÇIĞ</span></div>`,
 s5: navy+stars(80,21)+`<div class="c" style="top:220px"><img src="${logo}" style="width:300px;height:300px;border-radius:50%"/>
   <div class="kick" style="margin-top:50px">MADDE 004</div>
   <div class="serif gold" style="font-size:130px;line-height:1.02;margin-top:30px">Sence o gece<br>ne oldu?</div>
   <div style="font-size:42px;margin-top:40px">Dyatlov Geçidi Olayı</div>
   <div class="kick" style="margin-top:46px;font-size:34px">@MERAKLOPEDİM</div></div>`
};
const top=`<div class="c" style="top:110px;font-size:30px;letter-spacing:10px;color:#D9A441;font-weight:600;opacity:.9">MERAKLOPEDİ · MADDE 004</div>`;
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
 fs.mkdirSync('kartlar',{recursive:true});
 for(const [k,v] of Object.entries(cards)){await p.setContent(`<html><head><style>${css}</style></head><body>${v}${k!=='s5'?top:''}</body></html>`);
  await p.waitForTimeout(150);await p.screenshot({path:`kartlar/${k}.png`});}
 await b.close();})();
