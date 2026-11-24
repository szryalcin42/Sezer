const { chromium } = require('playwright');
const fs = require('fs');
const GOLD='#D9A441', NAVY1='#13213D', NAVY2='#070B16';
const defs = `<defs>
 <radialGradient id="bg" cx="50%" cy="42%" r="70%"><stop offset="0" stop-color="${NAVY1}"/><stop offset="1" stop-color="${NAVY2}"/></radialGradient>
 <linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F3D58A"/><stop offset=".55" stop-color="${GOLD}"/><stop offset="1" stop-color="#A8741F"/></linearGradient>
</defs><rect width="1080" height="1080" fill="url(#bg)"/>`;
function stars(n, seed, box){let s=seed;const r=()=>{s=(s*9301+49297)%233280;return s/233280};let o='';for(let i=0;i<n;i++){const x=box[0]+r()*box[2],y=box[1]+r()*box[3],rad=1.5+r()*3.5;o+=`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${rad.toFixed(1)}" fill="#F3E3B5" opacity="${(0.35+r()*0.6).toFixed(2)}"/>`}return o;}
const ring = `<circle cx="540" cy="540" r="440" fill="none" stroke="url(#g)" stroke-width="10" opacity=".9"/>`;

// A: Anahtar deliği + yıldızlar
const keyhole = 'M540 250 a150 150 0 0 1 82 275 l58 270 h-280 l58-270 a150 150 0 0 1 82-275z';
const A = `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080">${defs}
${stars(40,7,[60,60,960,960]).replace(/opacity="/g,'opacity="0.4*').replace(/0\.4\*/g,'')}
${ring}
<clipPath id="kh"><path d="${keyhole}"/></clipPath>
<path d="${keyhole}" fill="url(#g)"/>
<g clip-path="url(#kh)"><path d="${keyhole}" fill="${NAVY2}" transform="translate(540 522) scale(.82) translate(-540 -522)"/>
<g transform="translate(540 522) scale(.82) translate(-540 -522)" clip-path="url(#kh)">${stars(45,3,[380,250,320,560])}
<circle cx="560" cy="380" r="34" fill="url(#g)"/><ellipse cx="560" cy="380" rx="70" ry="16" fill="none" stroke="#F3D58A" stroke-width="6" transform="rotate(-20 560 380)"/></g></g>
</svg>`;

// B: Monogram M + metin halkası
const B = `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080">${defs}
<circle cx="540" cy="540" r="455" fill="none" stroke="url(#g)" stroke-width="6"/>
<circle cx="540" cy="540" r="335" fill="none" stroke="url(#g)" stroke-width="3" opacity=".7"/>
<path id="tp" d="M540 540 m-395 0 a395 395 0 1 1 790 0 a395 395 0 1 1 -790 0" fill="none"/>
<text font-family="Inter" font-weight="600" font-size="54" letter-spacing="14" fill="url(#g)"><textPath href="#tp" startOffset="0">TARİH ✦ GİZEM ✦ BİLİM ✦ GERÇEK ✦ TARİH ✦ GİZEM ✦</textPath></text>
<text x="540" y="672" text-anchor="middle" font-family="Caladea, Bitstream Charter, serif" font-weight="700" font-size="400" fill="url(#g)">M</text>
<circle cx="540" cy="752" r="9" fill="url(#g)"/>
</svg>`;

// C: Göz + gezegen iris
const C = `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080">${defs}
${ring}
<path d="M180 540 Q540 190 900 540 Q540 890 180 540Z" fill="none" stroke="url(#g)" stroke-width="26" stroke-linejoin="round"/>
<circle cx="540" cy="540" r="150" fill="${NAVY2}" stroke="url(#g)" stroke-width="14"/>
<clipPath id="ir"><circle cx="540" cy="540" r="143"/></clipPath>
<g clip-path="url(#ir)">${stars(30,11,[390,390,300,300])}</g>
<circle cx="540" cy="540" r="62" fill="url(#g)"/>
<ellipse cx="540" cy="540" rx="128" ry="30" fill="none" stroke="#F3D58A" stroke-width="10" transform="rotate(-22 540 540)"/>
<path d="M540 478 a62 62 0 0 1 0 124" fill="url(#g)" transform="rotate(-22 540 540)"/>
<g stroke="url(#g)" stroke-width="12" stroke-linecap="round"><line x1="540" y1="250" x2="540" y2="300"/><line x1="380" y1="290" x2="405" y2="335"/><line x1="700" y1="290" x2="675" y2="335"/></g>
</svg>`;

(async()=>{
 const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1080,height:1080}});
 const files={A,B,C};
 for(const [k,svg] of Object.entries(files)){fs.writeFileSync(`${k}.svg`,svg);
  await p.setContent(`<html><body style="margin:0">${svg}</body></html>`);
  await p.screenshot({path:`profil_${k}.png`});}
 // önizleme: dairesel, büyük ve küçük boy
 const img=k=>'data:image/png;base64,'+fs.readFileSync(`profil_${k}.png`).toString('base64');
 const names={A:'A · Anahtar Deliği',B:'B · Monogram',C:'C · Gözlem'};
 const html=`<html><body style="margin:0;background:#fafafa;font-family:Inter;padding:40px;width:1120px">
 <div style="display:flex;gap:50px">${Object.keys(files).map(k=>`<div style="text-align:center">
 <img src="${img(k)}" style="width:320px;height:320px;border-radius:50%;display:block"/>
 <div style="margin:18px 0 10px;font-weight:600;font-size:22px">${names[k]}</div>
 <div style="display:flex;gap:18px;justify-content:center;align-items:center">
 <img src="${img(k)}" style="width:110px;border-radius:50%"/><img src="${img(k)}" style="width:56px;border-radius:50%"/><img src="${img(k)}" style="width:32px;border-radius:50%"/></div></div>`).join('')}</div></body></html>`;
 const q=await b.newPage({viewport:{width:1200,height:620},deviceScaleFactor:2});
 await q.setContent(html); await q.waitForTimeout(300); await q.screenshot({path:'onizleme.png',fullPage:true});
 await b.close();})();
