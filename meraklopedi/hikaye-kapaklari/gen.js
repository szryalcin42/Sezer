const { chromium } = require('playwright');
const fs=require('fs');
const G='url(#g)', L='#F3D58A';
const s=`stroke="${G}" stroke-width="22" fill="none" stroke-linecap="round" stroke-linejoin="round"`;
const icons={
 tarih:`<path d="M410 330 H670 M410 750 H670" ${s}/><path d="M440 340 C440 470 540 500 540 540 C540 580 440 610 440 740 M640 340 C640 470 540 500 540 540 C540 580 640 610 640 740" ${s}/>
  <path d="M470 700 Q540 640 610 700 L620 735 H460Z" fill="${G}"/><path d="M490 420 H590 Q560 480 540 500 Q520 480 490 420Z" fill="${G}"/><line x1="540" y1="520" x2="540" y2="650" stroke="${L}" stroke-width="6" stroke-dasharray="4 14"/>`,
 gizem:`<path d="M540 330 a110 110 0 0 1 60 202 l42 218 h-204 l42-218 a110 110 0 0 1 60-202z" fill="${G}"/>
  <circle cx="540" cy="440" r="45" fill="#0B1224"/><path d="M520 470 h40 l18 200 h-76z" fill="#0B1224"/>`,
 bilim:`<ellipse cx="540" cy="540" rx="230" ry="88" ${s}/><ellipse cx="540" cy="540" rx="230" ry="88" ${s} transform="rotate(60 540 540)"/><ellipse cx="540" cy="540" rx="230" ry="88" ${s} transform="rotate(-60 540 540)"/><circle cx="540" cy="540" r="42" fill="${G}"/>`,
 gercekler:`<path d="M540 300 C430 300 370 380 370 470 C370 540 410 580 440 620 C460 650 465 680 465 700 H615 C615 680 620 650 640 620 C670 580 710 540 710 470 C710 380 650 300 540 300Z" ${s}/>
  <path d="M470 750 H610 M490 800 H590" ${s}/><path d="M555 380 L500 500 H560 L520 610" stroke="${L}" stroke-width="18" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`,
 maddeler:`<path d="M540 760 Q440 700 300 725 L300 390 Q440 360 540 430 Z" ${s}/><path d="M540 760 Q640 700 780 725 L780 390 Q640 360 540 430 Z" ${s}/>
  <path d="M350 480 Q420 465 490 495 M350 550 Q420 535 490 565 M730 480 Q660 465 590 495 M730 550 Q660 535 590 565" stroke="${L}" stroke-width="10" fill="none" stroke-linecap="round" opacity=".8"/>`,
 sorular:`<path d="M330 360 Q330 300 390 300 H690 Q750 300 750 360 V620 Q750 680 690 680 H500 L400 770 L420 680 H390 Q330 680 330 620Z" ${s}/>
  <path d="M480 440 Q480 375 540 375 Q600 375 600 430 Q600 470 565 490 Q540 505 540 540" stroke="${L}" stroke-width="22" fill="none" stroke-linecap="round"/><circle cx="540" cy="600" r="16" fill="${L}"/>`
};
function stars(n,seed){let q=seed;const r=()=>{q=(q*9301+49297)%233280;return q/233280};let o='';
 for(let i=0;i<n;i++)o+=`<circle cx="${(r()*1080)|0}" cy="${(r()*1920)|0}" r="${(1+r()*3).toFixed(1)}" fill="#F3E3B5" opacity="${(0.15+r()*0.45).toFixed(2)}"/>`;return o;}
const svg=(k,i)=>`<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920">
<defs><radialGradient id="bg" cx="50%" cy="50%" r="65%"><stop offset="0" stop-color="#16264A"/><stop offset=".6" stop-color="#0B1224"/><stop offset="1" stop-color="#05080F"/></radialGradient>
<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F7DE9A"/><stop offset=".55" stop-color="#D9A441"/><stop offset="1" stop-color="#A8741F"/></linearGradient>
<radialGradient id="glow"><stop offset="0" stop-color="#D9A441" stop-opacity=".22"/><stop offset="1" stop-color="#D9A441" stop-opacity="0"/></radialGradient></defs>
<rect width="1080" height="1920" fill="url(#bg)"/>${stars(70,i*13+5)}
<circle cx="540" cy="960" r="430" fill="url(#glow)"/>
<circle cx="540" cy="960" r="400" fill="none" stroke="url(#g)" stroke-width="8" opacity=".9"/>
<g transform="translate(0 420)">${icons[k]}</g></svg>`;
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
 const ks=Object.keys(icons);
 for(let i=0;i<ks.length;i++){const v=svg(ks[i],i);fs.writeFileSync(`kapak_${ks[i]}.svg`,v);
  await p.setContent(`<html><body style="margin:0">${v}</body></html>`);await p.screenshot({path:`kapak_${ks[i]}.png`});}
 const names={tarih:'Tarih',gizem:'Gizem',bilim:'Bilim',gercekler:'Gerçekler',maddeler:'Maddeler',sorular:'Soru-Cevap'};
 const im=k=>'data:image/png;base64,'+fs.readFileSync(`kapak_${k}.png`).toString('base64');
 const q=await b.newPage({viewport:{width:1100,height:300},deviceScaleFactor:2});
 await q.setContent(`<body style="margin:0;background:#fff;font-family:Inter;padding:40px 30px;display:flex;gap:34px">${ks.map(k=>`<div style="text-align:center;width:140px">
  <div style="width:136px;height:136px;border-radius:50%;padding:5px;border:2px solid #ddd;margin:auto"><div style="width:122px;height:122px;border-radius:50%;background:url(${im(k)}) center/122px auto"></div></div>
  <div style="font-size:18px;margin-top:10px;color:#222">${names[k]}</div></div>`).join('')}</body>`);
 await q.waitForTimeout(300);await q.screenshot({path:'onizleme.png'});await b.close();})();
