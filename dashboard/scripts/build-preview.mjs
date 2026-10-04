import { readFile, writeFile } from 'node:fs/promises';
import { extname } from 'node:path';
import { syncBrand } from './sync-brand.mjs';

const root = new URL('../', import.meta.url);
const read = path => readFile(new URL(path, root), 'utf8');
await syncBrand();
const [html, css, config, contract, data, app] = await Promise.all([
  read('dist/index.html'), read('dist/styles.css'), read('dist/config.js'), read('dist/contract.js'), read('dist/data.js'), read('dist/app.js'),
]);
// Source modules stay canonical. This file-only demo has no network imports.
const script = [config, contract, data, app].map(code => code.replace(/^import .* from ['"].+['"];\n/gm, '').replace(/^export /gm, '')).join('\n');
let bundled = html
  .replace('<link rel="stylesheet" href="/styles.css">', () => `<style>\n${css}\n</style>`)
  .replace('<script type="module" src="/app.js"></script>', () => `<script type="module">\n${script}\n</script>`);
// Embed brand assets too: the standalone file must work after moving it offline.
const imageTypes = { '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon' };
const assets = [...new Set([...html.matchAll(/(?:src|href)="(\/[^"]+)"/g)].map(match => match[1]).filter(path => imageTypes[extname(path)]))];
for (const path of assets) {
  const bytes = await readFile(new URL(`dist${path}`, root));
  bundled = bundled.replaceAll(`"${path}"`, `"data:${imageTypes[extname(path)]};base64,${bytes.toString('base64')}"`);
}
await writeFile(new URL('Podglad.html', root), bundled);
console.log('Podgląd bez serwera: dashboard/Podglad.html');
