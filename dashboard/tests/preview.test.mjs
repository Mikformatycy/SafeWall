import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { Script } from 'node:vm';

test('the file preview contains executable JavaScript with no module imports or remote assets', async () => {
  const html = await readFile(new URL('../Podglad.html', import.meta.url), 'utf8');
  const script = html.match(/<script type="module">([\s\S]*?)<\/script>/)?.[1];
  assert.ok(script);
  assert.doesNotThrow(() => new Script(script));
  assert.doesNotMatch(script, /^import\s/m);
  assert.doesNotMatch(html, /(?:src|href)="https?:\/\//);
  assert.doesNotMatch(html, /(?:src|href)="\/(?:app\.js|styles\.css)/);
  assert.doesNotMatch(html, /(?:src|href)="\/(?:assets\/brand\/|favicon|apple-touch-icon)/);
  assert.match(html, /class="brand-mark"[^>]*><img src="data:image\/svg\+xml;base64,/);
});
