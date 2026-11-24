// Voynich tarzı, tamamen özgün bir parşömen sayfası çizimi (SVG) üretir.
function rng(seed){let s=seed;return()=>{s=(s*9301+49297)%233280;return s/233280};}
function glyph(r,x,y){const k=Math.floor(r()*8);const w=[12,14,12,12,14,24,10,16][k];let d='';
 switch(k){case 0:d=`M${x+6} ${y-6} a6 6 0 1 0 0.1 0`;break;                         // o
  case 1:d=`M${x+6} ${y-6} a6 6 0 1 0 0.1 0 M${x+12} ${y-8} v8`;break;               // a
  case 2:d=`M${x+11} ${y-10} q-12 -2 -10 6 q2 6 10 4`;break;                         // c/e
  case 3:d=`M${x+2} ${y-12} v12 M${x+8} ${y-12} v12`;break;                           // ii
  case 4:d=`M${x+8} ${y-6} a5 5 0 1 0 0.1 0 M${x+13} ${y-6} q0 12 -9 14`;break;        // 9
  case 5:d=`M${x+2} ${y} v-22 q6 -6 8 4 q2 -10 8 -4 v22 M${x} ${y-8} h22`;break;       // gallows
  case 6:d=`M${x+2} ${y-12} q8 2 4 12`;break;                                         // r
  case 7:d=`M${x+2} ${y-2} q4 -12 8 -2 q4 10 6 -8`;break;}                            // s
 return {d,w};}
function textLines(r,x0,y0,width,lines,lh){let out='';for(let l=0;l<lines;l++){let x=x0;const y=y0+l*lh;
  while(x<x0+width-40){const n=2+Math.floor(r()*5);for(let i=0;i<n&&x<x0+width-20;i++){const g=glyph(r,x,y);out+=`<path d="${g.d}"/>`;x+=g.w;}x+=14;}}
 return out;}
function plant(r,cx,top,bottom){let o='';
 // kökler
 for(let i=0;i<11;i++){const dx=-200+i*40+(r()-.5)*30;o+=`<path d="M${cx} ${bottom-60} q${dx/2} 40 ${dx} ${60+r()*40}" stroke="#5B3A1E" stroke-width="5" fill="none"/>`;}
 o+=`<ellipse cx="${cx}" cy="${bottom-70}" rx="60" ry="38" fill="#B07A45" stroke="#5B3A1E" stroke-width="5"/>`;
 // gövde
 o+=`<path d="M${cx} ${bottom-100} C${cx-30} ${bottom-260} ${cx+30} ${top+220} ${cx} ${top+120}" stroke="#4E5E2A" stroke-width="10" fill="none"/>`;
 // yapraklar
 for(let i=0;i<6;i++){const y=bottom-170-i*((bottom-top-300)/6);const s=i%2?1:-1;const L=110+r()*70;
  o+=`<path d="M${cx} ${y} q${s*L*0.5} -${40+r()*30} ${s*L} ${-10} q-${s*L*0.45} ${50} -${s*L} ${10}Z" fill="#7C8F43" stroke="#3E4A20" stroke-width="4" opacity=".92"/>`;}
 // çiçek
 o+=`<g transform="translate(${cx} ${top+100})">`;for(let i=0;i<8;i++)o+=`<ellipse rx="22" ry="52" cy="-50" fill="#5E7FA8" stroke="#2F4466" stroke-width="4" transform="rotate(${i*45})" opacity=".9"/>`;
 o+=`<circle r="26" fill="#C9963E" stroke="#6B4A1E" stroke-width="4"/></g>`;return o;}
function parsomen(w,h,seed=7){const r=rng(seed);
 let edge='M30 40 ';for(let x=30;x<=w-30;x+=40)edge+=`L${x} ${30+r()*20} `;for(let y=40;y<=h-30;y+=40)edge+=`L${w-30+(r()-.5)*20} ${y} `;
 for(let x=w-30;x>=30;x-=40)edge+=`L${x} ${h-30-r()*20} `;for(let y=h-40;y>=40;y-=40)edge+=`L${30+(r()-.5)*20} ${y} `;edge+='Z';
 let stains='';for(let i=0;i<14;i++)stains+=`<circle cx="${r()*w}" cy="${r()*h}" r="${30+r()*120}" fill="#8A6234" opacity="${(0.03+r()*0.06).toFixed(3)}"/>`;
 const t1=textLines(r,90,110,w-180,4,46), t2=textLines(r,90,h-260,w-180,4,46);
 return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
 <defs><radialGradient id="pg" cx="50%" cy="45%" r="70%"><stop offset="0" stop-color="#EAD9B4"/><stop offset=".7" stop-color="#D7BE8C"/><stop offset="1" stop-color="#A9844F"/></radialGradient>
 <filter id="ink"><feTurbulence baseFrequency="0.9" numOctaves="1" seed="3"/><feDisplacementMap in="SourceGraphic" scale="2.5"/></filter></defs>
 <clipPath id="pc"><path d="${edge}"/></clipPath><path d="${edge}" fill="url(#pg)"/><g clip-path="url(#pc)">${stains}</g>
 <g fill="none" stroke="#3B2614" stroke-width="3.2" stroke-linecap="round" filter="url(#ink)" opacity=".88">${t1}${t2}</g>
 <g filter="url(#ink)">${plant(r,w/2,330,h-300)}</g>
 <g fill="none" stroke="#3B2614" stroke-width="3" opacity=".85" filter="url(#ink)">${textLines(r,w/2+190,560,w/2-270,6,42)}</g>
 </svg>`;}
module.exports={parsomen};
if(require.main===module){require('fs').writeFileSync(process.argv[2]||'parsomen.svg',parsomen(900,1300));}
