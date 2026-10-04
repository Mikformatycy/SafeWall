import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createAppServer, readRevision } from '../server.mjs';

// Exercise the actual HTTP request listener without binding a socket.
async function request(url, method = 'GET', options = {}) {
  const server = createAppServer(options);
  const result = { headers: {}, status: null, body: '' };
  const response = {
    setHeader(name, value) { result.headers[name.toLowerCase()] = value; },
    writeHead(status, headers = {}) { result.status = status; for (const [name, value] of Object.entries(headers)) this.setHeader(name, value); return this; },
    end(body) { result.rawBody = Buffer.from(body || ''); result.body = result.rawBody.toString(); },
  };
  await server.listeners('request')[0]({ url, method }, response);
  server.close();
  return result;
}

test('the local server serves the dashboard and source modules', async () => {
  const home = await request('/');
  assert.equal(home.status, 200);
  assert.match(home.body, /SafeWall/);
  assert.match(home.headers['content-security-policy'], /connect-src 'self'/);
  for (const path of ['/styles.css', '/app.js', '/config.js', '/data.js', '/contract.js']) {
    assert.equal((await request(path)).status, 200, path);
  }
});

test('brand assets retain their bytes and have the correct media type', async () => {
  for (const [path, type] of [
    ['/assets/brand/safewall-logo.svg', 'image/svg+xml'],
    ['/favicon.svg', 'image/svg+xml'],
    ['/favicon.ico', 'image/x-icon'],
    ['/assets/brand/favicon-32.png', 'image/png'],
    ['/apple-touch-icon.png', 'image/png'],
  ]) {
    const response = await request(path);
    assert.equal(response.status, 200, path);
    assert.equal(response.headers['content-type'], type, path);
    assert.deepEqual(response.rawBody, await readFile(new URL(`../dist${path}`, import.meta.url)), path);
    const head = await request(path, 'HEAD');
    assert.equal(head.status, 200);
    assert.equal(head.body, '');
  }
});

test('the placeholder live endpoint fails explicitly with no fabricated data', async () => {
  const response = await request('/api/v1/dashboard?period=24h');
  assert.equal(response.status, 503);
  assert.equal(JSON.parse(response.body).error, 'DATA_SOURCE_NOT_CONFIGURED');
});

test('private files and traversal paths cannot be served', async () => {
  for (const path of ['/../package.json', '/%2e%2e%2fpackage.json', '/%2e%2e%2f%2e%2e%2fconfig/pi-router.conf', '/server.mjs', '/missing.js']) {
    assert.equal((await request(path)).status, 404, path);
  }
  assert.equal((await request('/%zz')).status, 400);
});

test('the server rejects writes and honours HEAD for static files', async () => {
  assert.equal((await request('/', 'POST')).status, 405);
  const head = await request('/', 'HEAD');
  assert.equal(head.status, 200);
  assert.equal(head.body, '');
});

test('live reload is injected only in development, and revision matches the served page', async () => {
  const revision = await readRevision();
  assert.match(revision.markup, /^[a-f0-9]{64}$/);
  assert.match(revision.styles, /^[a-f0-9]{64}$/);
  const home = await request('/', 'GET', { dev: true });
  assert.match(home.body, /src="\/__dev\/reload.js"/);
  assert.ok(home.body.includes(`data-markup="${revision.markup}"`));
  assert.ok(home.body.includes(`data-styles="${revision.styles}"`));
  const response = await request('/__dev/revision', 'GET', { dev: true });
  assert.deepEqual(JSON.parse(response.body), revision);
  assert.equal((await request('/__dev/reload.js', 'GET', { dev: true })).status, 200);
  assert.equal((await request('/__dev/revision')).status, 404);
  assert.equal((await request('/__dev/reload.js')).status, 404);
  assert.doesNotMatch((await request('/')).body, /__dev/);
});
