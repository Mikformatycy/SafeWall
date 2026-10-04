import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { resolve, extname, sep } from 'node:path';
import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';

const root = fileURLToPath(new URL('./dist/', import.meta.url));
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon', '.json': 'application/json' };

export async function readRevision() {
  const files = ['index.html', 'app.js', 'data.js', 'contract.js', 'config.js', 'assets/brand/safewall-logo.svg', 'assets/brand/safewall-mask.svg', 'assets/brand/favicon-32.png', 'favicon.svg', 'favicon.ico', 'apple-touch-icon.png', 'styles.css'];
  const contents = await Promise.all(files.map(file => readFile(resolve(root, file))));
  const markup = createHash('sha256');
  for (const content of contents.slice(0, -1)) markup.update(content).update('\0');
  return {
    markup: markup.digest('hex'),
    styles: createHash('sha256').update(contents.at(-1)).digest('hex'),
  };
}

export function createAppServer({ dev = false, getRevision = readRevision } = {}) {
  return createServer(async (req, res) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Referrer-Policy', 'no-referrer');
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'");
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      res.writeHead(405, { Allow: 'GET, HEAD' }).end();
      return;
    }
    try {
      const url = new URL(req.url, 'http://localhost');
      if (dev && url.pathname === '/__dev/revision') {
        const revision = await getRevision();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(req.method === 'HEAD' ? undefined : JSON.stringify(revision));
        return;
      }
      if (dev && url.pathname === '/__dev/reload.js') {
        const code = await readFile(new URL('./scripts/live-reload.js', import.meta.url));
        res.writeHead(200, { 'Content-Type': types['.js'] });
        res.end(req.method === 'HEAD' ? undefined : code);
        return;
      }
      if (url.pathname === '/api/v1/dashboard') {
        res.writeHead(503, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'DATA_SOURCE_NOT_CONFIGURED', message: 'Nie podłączono jeszcze odczytów z Raspberry Pi.' }));
        return;
      }
      if (url.pathname === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'ok', dataSource: 'demo-only', version: '0.1.0' }));
        return;
      }
      const pathname = decodeURIComponent(url.pathname);
      const file = resolve(root, pathname === '/' ? 'index.html' : `.${pathname}`);
      if (!file.startsWith(root.endsWith(sep) ? root : root + sep) || !types[extname(file)]) {
        res.writeHead(404).end('Not found');
        return;
      }
      const revision = dev && file === resolve(root, 'index.html') ? await getRevision() : null;
      let body = await readFile(file);
      if (revision) {
        const markup = String(revision.markup).replace(/[^a-z0-9]/gi, '');
        const styles = String(revision.styles).replace(/[^a-z0-9]/gi, '');
        body = body.toString().replace('</body>', `<script src="/__dev/reload.js" data-markup="${markup}" data-styles="${styles}"></script></body>`);
      }
      res.writeHead(200, { 'Content-Type': types[extname(file)] });
      res.end(req.method === 'HEAD' ? undefined : body);
    } catch (error) {
      res.writeHead(error.code === 'ENOENT' || error.code === 'EISDIR' ? 404 : 400).end('Not found');
    }
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const port = Number(process.env.PORT || 4173);
  const dev = process.argv.includes('--dev');
  const server = createAppServer({ dev });
  server.on('error', error => { console.error(`SafeWall: ${error.message}`); process.exitCode = 1; });
  server.listen(port, '127.0.0.1', () => {
    const url = `http://127.0.0.1:${server.address().port}`;
    console.log(`SafeWall · ${url}\nDane demonstracyjne. Docelowy adres na Pi: safewall.local`);
    if (dev) console.log('Live reload aktywny: CSS bez przeładowania, HTML/JS z odświeżeniem strony.');
    if (process.argv.includes('--open-safari') && process.platform === 'darwin') {
      const opener = spawn('/usr/bin/open', ['-a', 'Safari', url], { stdio: 'ignore' });
      opener.on('error', () => console.error(`Otwórz ręcznie w Safari: ${url}`));
      opener.on('exit', code => { if (code) console.error(`Otwórz ręcznie w Safari: ${url}`); });
    }
  });
}
