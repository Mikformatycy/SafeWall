// Deterministic HTML/CSS animation capture. Uses the canonical SVG in brand/.
import { mkdir } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { join } from 'node:path';

const root = fileURLToPath(new URL('./', import.meta.url));
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const requested = process.argv[2] || 'landscape';
const formats = { portrait: [1080, 1920], landscape: [1920, 1080] };
if (requested !== 'all' && !formats[requested]) throw new Error('Use portrait, landscape or all.');
await mkdir(join(root, '.artifacts'), { recursive: true });
const browser = await chromium.launch();

try {
  for (const [format, [width, height]] of Object.entries(formats)) {
    if (requested !== 'all' && requested !== format) continue;
    const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const source = new URL(pathToFileURL(join(root, 'src/outro.html')));
    source.searchParams.set('format', format);
    await page.goto(source.href);
    await page.evaluate(async () => {
      window.outro.setTime(0);
      await document.fonts.ready;
      await Promise.all([...document.images].map(img => img.decode()));
    });
    const { fps, duration } = await page.evaluate(() => window.outro);
    const frames = Math.round(duration * fps / 1000);
    const output = join(root, `safewall-outro-${format}.mp4`);
    const encoder = spawn('ffmpeg', [
      '-y', '-hide_banner', '-loglevel', 'error',
      '-f', 'image2pipe', '-framerate', String(fps), '-vcodec', 'png', '-i', 'pipe:0',
      '-an', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-threads', '4',
      '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709',
      '-colorspace', 'bt709', '-movflags', '+faststart', output,
    ], { stdio: ['pipe', 'ignore', 'pipe'] });
    let diagnostics = '';
    encoder.stderr.on('data', chunk => diagnostics += chunk);
    const complete = new Promise((resolve, reject) => {
      encoder.on('error', reject);
      encoder.on('close', code => code === 0 ? resolve() : reject(new Error(diagnostics || `ffmpeg exited ${code}`)));
    });
    // Mark failures handled while capture runs; await the same promise below.
    complete.catch(() => {});
    let inputError;
    encoder.stdin.on('error', error => { inputError = error; });
    try {
      for (let frame = 0; frame < frames; frame++) {
        if (inputError) throw inputError;
        await page.evaluate(t => window.outro.setTime(t), frame * 1000 / fps);
        const png = await page.screenshot({ type: 'png', animations: 'allow' });
        if (!encoder.stdin.write(png)) await once(encoder.stdin, 'drain');
        if (frame % 60 === 0) console.log(`${format}: ${frame}/${frames}`);
      }
      encoder.stdin.end();
      await complete;
      await page.evaluate(() => window.outro.setTime(2000));
      await page.screenshot({ path: join(root, `poster-${format}.png`) });
      if (errors.length) throw new Error(errors.join('\n'));
      console.log(`${format}: ${frames} frames, ${duration / 1000}s → ${output}`);
    } catch (error) {
      encoder.stdin.destroy();
      encoder.kill();
      throw error;
    } finally { await page.close(); }
  }
} finally { await browser.close(); }
