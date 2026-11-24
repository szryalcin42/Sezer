const { chromium } = require('playwright');
const fs=require('fs');
const img=f=>'data:image/png;base64,'+fs.readFileSync('cizimler/'+f).toString('base64');
const logo='data:image/svg+xml;base64,'+fs.readFileSync('../../profil/meraklopedi_C.svg').toString('base64');
const css=`*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;position:relative;font-family:Inter;color:#EDE6D3;background:#070B16}
.bg{position:absolute;inset:0;background-size:cover;background-repeat:no-repeat}
.shade{position:absolute;inset:0}
.stars{position:absolute;inset:0}
.c{position:absolute;left:80px;right:80px;text-align:center}
.serif{font-family:Caladea,serif;font-weight:700}
.gold{background:linear-gradient(135deg,#F7DE9A,#D9A441 55%,#A8741F);-webkit-background-clip:text;color:transparent}
.kick{font-size:40px;letter-spacing:12px;color:#D9A441;font-weight:600}
.pill{display:inline-block;border:3px solid #D9A441;color:#F3D58A;border-radius:60px;padding:14px 34px;font-size:36px;letter-spacing:8px;font-weight:600;background:rgba(7,11,22,.55)}
`;
function stars(n,seed){let s=seed;const r=()=>{s=(s*9301+49297)%233280;return s/233280};let o='<svg class="stars" width="1080" height="1920">';
 for(let i=0;i<n;i++)o+=`<circle cx="${(r()*1080)|0}" cy="${(r()*1920)|0}" r="${(1+r()*3).toFixed(1)}" fill="#F3E3B5" opacity="${(0.15+r()*0.5).toFixed(2)}"/>`;return o+'</svg>';}
const bgimg=(f,pos,filter='')=>`<div class="bg" style="background-image:url(${img(f)});background-position:${pos};background-size:auto 100%;filter:${filter}"></div>`;
const grad=`<div class="shade" style="background:linear-gradient(180deg,rgba(7,11,22,.55) 0%,rgba(7,11,22,0) 22%,rgba(7,11,22,0) 55%,rgba(7,11,22,.85) 100%)"></div>`;
const navy=`<div class="shade" style="background:radial-gradient(ellipse at 50% 40%,#17284D 0%,#0B1224 60%,#05080F 100%)"></div>`;
const note=(x,y,s,o=1)=>`<text x="${x}" y="${y}" font-size="${s}" fill="#D9A441" opacity="${o}" font-family="DejaVu Sans">♪</text>`;
const brainSVG=()=>{let threads='',heads='';const xs=[110,230,350,470,590,710,830,950];
 xs.forEach((x,i)=>{const y=1500+(i%2)*40;heads+=`<circle cx="${x}" cy="${y}" r="44" fill="#03050B"/><path d="M${x-80} ${y+190} Q${x-80} ${y+60} ${x} ${y+55} Q${x+80} ${y+60} ${x+80} ${y+190}Z" fill="#03050B"/>`;
  threads+=`<path d="M${x} ${y-44} Q${(x+540)/2} ${(y+760)/2-120} 540 800" fill="none" stroke="#D9A441" stroke-width="2.5" opacity=".75"/>`;});
 let folds='';for(let i=0;i<9;i++){folds+=`<path d="M${400+i*6} ${700+i*22} q40 -40 80 0 t80 0 t80 0 t80 0" fill="none" stroke="#F3D58A" stroke-width="5" opacity=".55" transform="translate(${-20+((i%3)*12)} 0)"/>`;}
 return `<svg class="stars" width="1080" height="1920"><defs><radialGradient id="gl"><stop offset="0" stop-color="#D9A441" stop-opacity=".45"/><stop offset="1" stop-color="#D9A441" stop-opacity="0"/></radialGradient></defs>
 <circle cx="540" cy="780" r="380" fill="url(#gl)"/>
 <path d="M540 610 C420 560 320 640 330 740 C300 800 330 880 400 900 C430 960 520 960 540 930 C560 960 650 960 680 900 C750 880 780 800 750 740 C760 640 660 560 540 610Z" fill="rgba(217,164,65,.12)" stroke="#F3D58A" stroke-width="7"/>
 <path d="M540 615 L540 930" stroke="#F3D58A" stroke-width="5" opacity=".7"/>
 <path d="M380 700 q40 -30 80 0 q40 30 80 0" fill="none" stroke="#F3D58A" stroke-width="5" opacity=".6"/><path d="M560 700 q40 -30 80 0 q40 30 80 0" fill="none" stroke="#F3D58A" stroke-width="5" opacity=".6"/>
 <path d="M360 800 q45 -35 90 0 q40 30 80 0" fill="none" stroke="#F3D58A" stroke-width="5" opacity=".6"/><path d="M560 800 q45 -35 90 0 q40 30 80 0" fill="none" stroke="#F3D58A" stroke-width="5" opacity=".6"/>
 <path d="M420 880 q40 -25 110 0" fill="none" stroke="#F3D58A" stroke-width="5" opacity=".6"/><path d="M560 880 q60 -25 110 0" fill="none" stroke="#F3D58A" stroke-width="5" opacity=".6"/>
 ${threads}${heads}</svg>`;};

const cards={
 s1: bgimg('kadin2.png','46% 0')+grad,
 s2: bgimg('sehir2.png','49% 0')+grad+`<div class="c" style="top:260px"><span class="pill">STRAZBURG · TEMMUZ 1518</span></div>`,
 s3: bgimg('kadin1.png','42% 0')+grad,
 s4a: bgimg('kadin3.png','8% 0','brightness(.45) saturate(.7)')+grad+`<div class="c" style="top:560px"><div class="kick">BİR HAFTA İÇİNDE</div><div class="serif gold" style="font-size:190px;margin-top:20px">Onlarca</div></div>`,
 s4b: bgimg('kadin3.png','8% 0','brightness(.3) saturate(.6)')+grad+`<div class="c" style="top:520px"><div class="kick">BİR AY İÇİNDE</div><div class="serif gold" style="font-size:200px;margin-top:20px">Yüzlerce</div><div class="kick" style="margin-top:30px;font-size:30px;color:#cdbf9a">BAZI KAYITLARA GÖRE</div></div>`,
 s5a: bgimg('kadin4.png','55% 0','grayscale(.85) brightness(.35) contrast(1.1)')+grad,
 s5b: bgimg('kadin4.png','55% 0','grayscale(.9) brightness(.22) contrast(1.1)')+grad+`<div class="c" style="top:600px"><div class="kick">ÖLÜM SAYISI</div><div class="serif gold" style="font-size:320px;line-height:1">?</div><div class="kick" style="font-size:32px;color:#cdbf9a">HÂLÂ TARTIŞMALI</div></div>`,
 s6a: bgimg('sehir4.png','52% 0','brightness(.35)')+grad+`<div class="c" style="top:560px"><div class="kick">PEKİ</div><div class="serif gold" style="font-size:130px;line-height:1.05;margin-top:24px">Yetkililer<br>ne yaptı?</div></div>`,
 s6b: navy+stars(70,4)+`<svg class="stars" width="1080" height="1920">${note(140,520,160,.8)}${note(820,430,120,.6)}${note(800,1500,180,.85)}${note(180,1250,110,.55)}${note(480,330,90,.5)}${note(900,820,90,.5)}${note(90,880,80,.45)}</svg>
   <div class="c" style="top:620px"><div class="kick">ÇÖZÜM</div><div class="serif gold" style="font-size:150px;line-height:1.02;margin-top:24px">Daha çok<br>müzik!</div><div style="font-size:40px;margin-top:40px;color:#E9E3D3">Müzisyen tuttular, sahne kurdular.</div></div>`,
 s6c: bgimg('kadin3.png','50% 0','brightness(.28) sepia(.4) saturate(1.3)')+grad+`<div class="c" style="top:600px"><div class="kick">SONUÇ</div><div class="serif gold" style="font-size:130px;line-height:1.05;margin-top:24px">Salgın daha<br>da büyüdü</div></div>`,
 s7a: navy+stars(60,9)+brainSVG()+`<div class="c" style="top:230px"><div class="kick">EN GÜÇLÜ AÇIKLAMA</div><div class="serif gold" style="font-size:84px;line-height:1.1;margin-top:20px">Kitlesel psikojenik<br>hastalık</div></div>`,
 s7b: navy+stars(60,9)+brainSVG()+`<div class="shade" style="background:rgba(5,8,15,.55)"></div><div class="c" style="top:640px"><div class="serif gold" style="font-size:112px;line-height:1.08">Zihin, bütün<br>bir topluluğu<br>ele geçirdi</div></div>`,
 s8: navy+stars(80,21)+`<div class="c" style="top:360px"><img src="${logo}" style="width:300px;height:300px;border-radius:50%"/>
   <div class="kick" style="margin-top:50px">MADDE 001</div>
   <div class="serif gold" style="font-size:150px;line-height:1.02;margin-top:30px">Sence ne<br>oldu?</div>
   <div style="font-size:46px;margin-top:50px">Cevabını yorumlara yaz 👇</div>
   <div class="kick" style="margin-top:60px;font-size:34px">@MERAKLOPEDİM</div></div>`
};
const top=`<div class="c" style="top:110px;font-size:30px;letter-spacing:10px;color:#D9A441;font-weight:600;opacity:.9">MERAKLOPEDİ · MADDE 001</div>`;
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
 for(const [k,v] of Object.entries(cards)){await p.setContent(`<html><head><style>${css}</style></head><body>${v}${k!=='s8'?top:''}</body></html>`);
  await p.waitForTimeout(150);await p.screenshot({path:`kartlar/${k}.png`});}
 await b.close();})();
