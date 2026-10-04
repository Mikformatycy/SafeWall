import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { runInNewContext } from 'node:vm';

const source = await readFile(new URL('../scripts/live-reload.js', import.meta.url), 'utf8');
function setup() {
  const timers = [];
  const result = { reloads: 0, replacements: 0, removed: 0, cssHref: null, failCss: false, response: { markup: 'initial', styles: 'initial' } };
  const stylesheet = {
    cloneNode: () => ({ remove() {} }),
    remove() { result.removed++; },
    after(next) {
      result.replacements++;
      result.cssHref = next.href;
      queueMicrotask(() => result.failCss ? next.onerror() : next.onload());
    },
  };
  runInNewContext(source, {
    document: { hidden: false, currentScript: { dataset: { markup: 'initial', styles: 'initial' } }, querySelector: () => stylesheet },
    window: { location: { reload() { result.reloads++; } } },
    AbortSignal,
    setTimeout(fn, delay) { if (delay === 1000) timers.push(fn); return 1; },
    clearTimeout() {},
    fetch: async () => ({ ok: true, json: async () => result.response }),
  });
  return { result, tick: async () => { await timers.shift()(); } };
}

test('CSS edits replace styles without reloading or duplicating a successful update', async () => {
  const { result, tick } = setup();
  await tick();
  assert.equal(result.replacements, 0);
  result.response = { markup: 'initial', styles: 'changed' };
  await tick();
  assert.equal(result.cssHref, '/styles.css?v=changed');
  assert.equal(result.removed, 1);
  assert.equal(result.reloads, 0);
  await tick();
  assert.equal(result.replacements, 1);
});

test('HTML or JavaScript edits reload the page', async () => {
  const { result, tick } = setup();
  result.response = { markup: 'changed', styles: 'initial' };
  await tick();
  assert.equal(result.reloads, 1);
});

test('a failed CSS load retains the old stylesheet and retries', async () => {
  const { result, tick } = setup();
  result.response = { markup: 'initial', styles: 'changed' };
  result.failCss = true;
  await tick();
  assert.equal(result.removed, 0);
  result.failCss = false;
  await tick();
  assert.equal(result.replacements, 2);
  assert.equal(result.removed, 1);
  assert.equal(result.reloads, 0);
});
