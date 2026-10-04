// Rebuild all logo assets from the selected 4A vector master.
// PLAYWRIGHT_MODULE can point to an installed playwright/index.mjs.
// PYTHON can point to a Python environment containing Pillow.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';

const root = fileURLToPath(new URL('./', import.meta.url));
const source = await readFile(join(root, 'svg/safewall-logo.svg'), 'utf8');
const [, width, height] = source.match(/viewBox="0 0 ([\d.]+) ([\d.]+)"/).map(Number);
const paths = [...source.matchAll(/<path\b[^>]*\/>/g)].map(match => match[0]);
if (paths.length !== 2 || /<image\b|data:image/.test(source)) throw new Error('Expected a two-path vector master.');
const outline = color => paths[0].replace(/fill="[^"]+"/, `fill="${color}"`);
const svg = (viewWidth, viewHeight, content) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${viewWidth} ${viewHeight}" role="img" aria-labelledby="title"><title id="title">SafeWall</title>${content}</svg>\n`;
const square = (content, background = null, fraction = .875, size = 1024) => {
  const scale = size * fraction / width;
  const x = (size - width * scale) / 2;
  const y = (size - height * scale) / 2;
  return svg(size, size, `${background ? `<rect width="${size}" height="${size}" fill="${background}"/>` : ''}<g transform="translate(${x} ${y}) scale(${scale})">${content}</g>`);
};
const color = paths.join('');
const variants = {
  'safewall-logo-white': svg(width, height, outline('#FFFFFF')),
  'safewall-logo-ink': svg(width, height, outline('#17171C')),
  'safewall-icon': square(color),
  'safewall-icon-dark': square(color, '#17171C'),
  'safewall-icon-black': square(color, '#000000'),
  'safewall-icon-light': square(color, '#FFFFFF'),
  'safewall-icon-maskable': square(color, '#17171C', .7),
  'safewall-mask': square(outline('#000000')),
};
await mkdir(join(root, 'icons'), { recursive: true });
for (const [name, content] of Object.entries(variants)) await writeFile(join(root, `svg/${name}.svg`), content);
await writeFile(join(root, 'icons/favicon.svg'), square(color, null, .875, 64));

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch();
const renderRoot = join(root, '.render');
await mkdir(renderRoot, { recursive: true });
try {
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  const jobs = {
    logo: [source, 2048, Math.round(2048 * height / width)],
    white: [variants['safewall-logo-white'], 2048, Math.round(2048 * height / width)],
    ink: [variants['safewall-logo-ink'], 2048, Math.round(2048 * height / width)],
    transparent: [variants['safewall-icon'], 2048, 2048],
    dark: [variants['safewall-icon-dark'], 2048, 2048],
    black: [variants['safewall-icon-black'], 2048, 2048],
    light: [variants['safewall-icon-light'], 2048, 2048],
    maskable: [variants['safewall-icon-maskable'], 2048, 2048],
    trace: [source, width, height],
  };
  for (const [name, [markup, w, h]] of Object.entries(jobs)) {
    await page.setViewportSize({ width: w, height: h });
    await page.setContent(`<style>html,body{margin:0;padding:0;background:transparent}svg{display:block;width:${w}px;height:${h}px}</style>${markup}`);
    await page.screenshot({ path: join(renderRoot, `${name}.png`), omitBackground: true });
  }
} finally {
  await browser.close();
}
const result = spawnSync(process.env.PYTHON || 'python3', [join(root, 'export.py')], { stdio: 'inherit' });
if (result.error) throw result.error;
if (result.status) process.exit(result.status);
