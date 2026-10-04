// Renders reel.html frame-by-frame with headless Chromium.
//   node render.mjs                -> build/frames/%05d.png (all frames)
//   node render.mjs snap 1.2 5 9.8 -> build/snaps/t_<time>.png
//   node render.mjs cover          -> build/cover.png
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.woff2': 'font/woff2' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
}).listen(0);
const port = server.address().port;

const args = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--font-render-hinting=none'];
const browser = await chromium.launch({ args });

async function openPage() {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('pageerror', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('console', m.text()); });
  await page.goto(`http://localhost:${port}/reel.html?render=1`);
  await page.waitForFunction(() => window.ready === true, null, { timeout: 120000 });
  return page;
}

const [mode, ...rest] = process.argv.slice(2);
if (mode === 'cover') {
  fs.mkdirSync(path.join(ROOT, 'build'), { recursive: true });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto(`http://localhost:${port}/cover.html`);
  await page.waitForFunction(() => window.ready === true);
  await page.screenshot({ path: path.join(ROOT, 'build/cover.png') });
} else if (mode === 'snap') {
  fs.mkdirSync(path.join(ROOT, 'build/snaps'), { recursive: true });
  const page = await openPage();
  for (const t of rest) {
    await page.evaluate(t => window.renderFrame(t), +t);
    await page.screenshot({ path: path.join(ROOT, `build/snaps/t_${(+t).toFixed(2)}.png`) });
  }
} else {
  const out = path.join(ROOT, 'build/frames'); fs.mkdirSync(out, { recursive: true });
  const workers = +(process.env.WORKERS || 3);
  const page0 = await openPage();
  const { dur, fps } = await page0.evaluate(() => ({ dur: window.DURATION, fps: window.FPS }));
  const total = Math.round(dur * fps);
  const pages = [page0, ...await Promise.all(Array.from({ length: workers - 1 }, openPage))];
  // FRAMES=a-b re-renders only that inclusive range (everything is a pure function of t)
  const [fa, fb] = (process.env.FRAMES || `0-${total - 1}`).split('-').map(Number);
  let next = fa, done = 0; const t0 = Date.now();
  await Promise.all(pages.map(async page => {
    while (true) {
      const f = next++; if (f > fb || f >= total) break;
      await page.evaluate(t => window.renderFrame(t), f / fps);
      await page.screenshot({ path: path.join(out, String(f).padStart(5, '0') + '.png') });
      if (++done % 60 === 0) console.log(`${done}/${total} frames, ${((Date.now() - t0) / done).toFixed(0)} ms/frame`);
    }
  }));
  console.log(`rendered ${done} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
}
await browser.close(); server.close();
