// Kullanım: node render.js [sayfa.html] [ses_klasörü] [cikti.mp4]
//   varsayılan: reel.html voice akdeniz_cumartesi_reel.mp4
// reel.html'i 30 fps kare kare çeker, voice/<sahne>.mp3 dış seslerini sahnelere
// yerleştirir ve 1080x1920 MP4 üretir. Sahne süreleri sese göre uzatılır
// (animasyon zamanı parça parça doğrusal olarak esnetilir).
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const FPS = 30;
const VOICE_OFFSET = 0.25; // sahne başladıktan sonra sesin gireceği an
const TAIL = 0.45;          // ses bittikten sonra sahnede kalma
const END_HOLD = 1.5;       // son sahnede ses bittikten sonra bekleme

const dur = f => parseFloat(execFileSync('ffprobe', ['-v', 'error', '-show_entries',
  'format=duration', '-of', 'csv=p=0', f]).toString());

(async () => {
  const html = path.resolve(__dirname, process.argv[2] || 'reel.html');
  const vdir = path.resolve(__dirname, process.argv[3] || 'voice');
  const out = path.resolve(__dirname, process.argv[4] || 'akdeniz_cumartesi_reel.mp4');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + html);
  await page.evaluate(() => document.fonts.ready);
  const D = await page.evaluate(() => window.BOUNDS); // tasarım zamanında sahne sınırları
  const n = D.length - 1;
  const voices = [], R = [0];
  for (let i = 0; i < n; i++) {
    const f = path.join(vdir, `${i}.mp3`);
    const vd = fs.existsSync(f) ? dur(f) : 0;
    if (vd) voices.push({ f, at: R[i] + VOICE_OFFSET });
    const need = vd ? VOICE_OFFSET + vd + (i === n - 1 ? END_HOLD : TAIL) : 0;
    R.push(R[i] + Math.max(D[i + 1] - D[i], need));
  }
  const total = R[n];
  const warp = t => { // gerçek zaman -> tasarım zamanı
    for (let i = 0; i < n; i++) if (t <= R[i + 1])
      return D[i] + (t - R[i]) / (R[i + 1] - R[i]) * (D[i + 1] - D[i]);
    return D[n];
  };
  console.log('Sahne başlangıçları (sn):', R.map(x => x.toFixed(2)).join(' '));

  // 1) dış ses kanalı
  const wav = path.join(vdir, '_mix.wav');
  const args = ['-y', '-loglevel', 'error'];
  voices.forEach(v => args.push('-i', v.f));
  const fc = voices.map((v, i) => `[${i}:a]aresample=44100,adelay=${Math.round(v.at * 1000)}:all=1[a${i}]`).join(';')
    + ';' + voices.map((_, i) => `[a${i}]`).join('') + `amix=inputs=${voices.length}:normalize=0,apad,atrim=0:${total.toFixed(3)},loudnorm=I=-14:TP=-1.5[out]`;
  args.push('-filter_complex', fc, '-map', '[out]', '-ar', '44100', wav);
  execFileSync('ffmpeg', args);

  // 2) görüntü + ses
  const frames = Math.round(total * FPS);

  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-i', wav, '-map', '0:v', '-map', '1:a',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium',
    '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out],
    { stdio: ['pipe', 'ignore', 'inherit'] });

  for (let i = 0; i < frames; i++) {
    const t = i / FPS;
    await page.evaluate(([dt, p]) => { window.render(dt);
      document.getElementById('progress').style.width = (p * 1080) + 'px'; }, [warp(t), t / total]);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log(`kare ${i}/${frames}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  fs.unlinkSync(wav);
  console.log('Hazır:', out, `(${total.toFixed(1)} sn)`);
})();
