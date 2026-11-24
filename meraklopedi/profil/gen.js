const { chromium } = require('playwright');
const fs = require('fs');
const GOLD='#D9A441', NAVY1='#13213D', NAVY2='#070B16', LIGHT='#F3D58A';
const defs = `<defs>
 <radialGradient id="bg" cx="50%" cy="42%" r="70%"><stop offset="0" stop-color="${NAVY1}"/><stop offset="1" stop-color="${NAVY2}"/></radialGradient>
 <linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${LIGHT}"/><stop offset=".55" stop-color="${GOLD}"/><stop offset="1" stop-color="#A8741F"/></linearGradient>
 <radialGradient id="glow" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="${GOLD}" stop-opacity=".35"/><stop offset="1" stop-color="${GOLD}" stop-opacity="0"/></radialGradient>
</defs><rect width="1080" height="1080" fill="url(#bg)"/>`;
function stars(n, seed, box, maxr=4){let s=seed;const r=()=>{s=(s*9301+49297)%233280;return s/233280};let o='';for(let i=0;i<n;i++){const x=box[0]+r()*box[2],y=box[1]+r()*box[3],rad=1.5+r()*maxr;o+=`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${rad.toFixed(1)}" fill="#F3E3B5" opacity="${(0.3+r()*0.6).toFixed(2)}"/>`}return o;}
const spark=(x,y,s)=>`<path d="M${x} ${y-s} Q${x} ${y} ${x+s} ${y} Q${x} ${y} ${x} ${y+s} Q${x} ${y} ${x-s} ${y} Q${x} ${y} ${x} ${y-s}Z" fill="${LIGHT}"/>`;
const ring = `<circle cx="540" cy="540" r="440" fill="none" stroke="url(#g)" stroke-width="10" opacity=".9"/>`;
const planet=(x,y,r,rot=-20)=>`<circle cx="${x}" cy="${y}" r="${r}" fill="url(#g)"/><ellipse cx="${x}" cy="${y}" rx="${r*2.1}" ry="${r*0.5}" fill="none" stroke="${LIGHT}" stroke-width="${r*0.18}" transform="rotate(${rot} ${x} ${y})"/><path d="M${x-r} ${y} a${r} ${r} 0 0 0 ${2*r} 0" fill="url(#g)" transform="rotate(${rot} ${x} ${y})"/>`;

// A: Açık kitap + içinden yükselen evren
const A = `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080">${defs}
${stars(30,5,[90,90,900,900],2.5)}${ring}
<ellipse cx="540" cy="430" rx="260" ry="200" fill="url(#glow)"/>
<g stroke="url(#g)" stroke-width="16" stroke-linejoin="round" fill="${NAVY2}">
 <path d="M540 760 Q400 680 230 715 L230 505 Q400 450 540 545 Z"/>
 <path d="M540 760 Q680 680 850 715 L850 505 Q680 450 540 545 Z"/>
</g>
<path d="M210 745 Q390 715 540 785 Q690 715 870 745" fill="none" stroke="url(#g)" stroke-width="14" stroke-linecap="round"/>
<g stroke="${GOLD}" stroke-width="7" stroke-linecap="round" opacity=".7">
 <path d="M285 590 Q390 575 485 610" fill="none"/><path d="M285 640 Q390 625 485 660" fill="none"/>
 <path d="M795 590 Q690 575 595 610" fill="none"/><path d="M795 640 Q690 625 595 660" fill="none"/></g>
${stars(26,9,[380,240,320,280],3.5)}
${planet(540,365,48)}
${spark(410,300,26)}${spark(680,270,20)}${spark(630,470,14)}${spark(450,450,12)}
</svg>`;

// B: Mühür: M monogram + yazı halkası + anahtar deliği
const kh=(x,y,s)=>`<path d="M${x} ${y} a${s} ${s} 0 0 1 ${s*0.55} ${s*1.83} l${s*0.38} ${s*1.8} h-${s*1.86} l${s*0.38}-${s*1.8} a${s} ${s} 0 0 1 ${s*0.55}-${s*1.83}z" fill="url(#g)"/>`;
const B = `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080">${defs}
<circle cx="540" cy="540" r="455" fill="none" stroke="url(#g)" stroke-width="6"/>
<circle cx="540" cy="540" r="335" fill="none" stroke="url(#g)" stroke-width="3" opacity=".7"/>
<path id="tp" d="M540 540 m-395 0 a395 395 0 1 1 790 0 a395 395 0 1 1 -790 0" fill="none"/>
<text font-family="Inter" font-weight="600" font-size="50" fill="url(#g)"><textPath href="#tp" startOffset="0" textLength="2440" lengthAdjust="spacing">MERAKLOPEDİ ✦ TARİH ✦ GİZEM ✦ BİLİM ✦ GERÇEK ✦</textPath></text>
<text x="540" y="650" text-anchor="middle" font-family="Caladea, Bitstream Charter, serif" font-weight="700" font-size="380" fill="url(#g)">M</text>
${kh(540,700,22)}
${spark(540,268,20)}
</svg>`;

// C: Soru işareti — noktası gezegen
const C = `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080">${defs}
${stars(40,13,[110,110,860,860],3)}${ring}
<ellipse cx="540" cy="790" rx="170" ry="120" fill="url(#glow)"/>
<path d="M395 400 Q395 235 545 235 Q690 235 690 375 Q690 460 610 505 Q545 545 545 620 L545 660" fill="none" stroke="url(#g)" stroke-width="72" stroke-linecap="round"/>
${planet(545,790,52,-18)}
${spark(760,280,24)}${spark(330,640,18)}${spark(740,620,12)}
</svg>`;

(async()=>{
 const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1080,height:1080}});
 const files={A,B,C};
 for(const [k,svg] of Object.entries(files)){fs.writeFileSync(`meraklopedi_${k}.svg`,svg);
  await p.setContent(`<html><body style="margin:0">${svg}</body></html>`);
  await p.waitForTimeout(200); await p.screenshot({path:`meraklopedi_${k}.png`});}
 const img=k=>'data:image/png;base64,'+fs.readFileSync(`meraklopedi_${k}.png`).toString('base64');
 const names={A:'A · Açık Kitap',B:'B · Mühür',C:'C · Soru İşareti'};
 const html=`<html><body style="margin:0;background:#fafafa;font-family:Inter;padding:40px;width:1120px">
 <div style="display:flex;gap:50px">${Object.keys(files).map(k=>`<div style="text-align:center">
 <img src="${img(k)}" style="width:320px;height:320px;border-radius:50%;display:block"/>
 <div style="margin:18px 0 10px;font-weight:600;font-size:22px">${names[k]}</div>
 <div style="display:flex;gap:18px;justify-content:center;align-items:center">
 <img src="${img(k)}" style="width:110px;border-radius:50%"/><img src="${img(k)}" style="width:56px;border-radius:50%"/><img src="${img(k)}" style="width:32px;border-radius:50%"/></div></div>`).join('')}</div></body></html>`;
 const q=await b.newPage({viewport:{width:1200,height:620},deviceScaleFactor:2});
 await q.setContent(html); await q.waitForTimeout(300); await q.screenshot({path:'onizleme.png',fullPage:true});
 await b.close();})();
