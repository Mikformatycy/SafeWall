// Optional real browser verification; requires Playwright installed locally.
// PLAYWRIGHT_MODULE may point to an existing playwright/index.mjs.
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { MockDataSource } from '../dist/data.js';
const playwright = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const engine = process.env.BROWSER || 'chromium';
const browser = await playwright[engine].launch({ headless: true });
const target = process.env.DASHBOARD_URL || new URL('../Podglad.html', import.meta.url).href;
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, reducedMotion: 'reduce' });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.clock.install({ time: new Date('2026-10-03T12:00:00Z') });
  await page.goto(target);
  await page.locator('#connection-state').waitFor();
  assert.equal(await page.locator('#connection-state').textContent(), 'Ochrona ruchu aktywna');
  assert.equal(await page.locator('#protection-firewall').textContent(), 'Aktywna');
  assert.equal(await page.locator('#protection-dns').textContent(), 'Przez Tor');
  assert.equal(await page.locator('#quality-state').textContent(), 'Internet odpowiada');
  assert.match(await page.locator('#tor-response').textContent(), /\d+ ms/);
  assert.equal(await page.getByRole('img', { name: /Transfer/ }).count(), 1);
  await mkdir(new URL('../.artifacts/', import.meta.url), { recursive: true });
  await page.screenshot({ path: new URL(`../.artifacts/${engine}-desktop.png`, import.meta.url).pathname, fullPage: true });
  await page.locator('#connection-link').focus();
  const initialEnd = Number(await page.locator('.traffic-chart').getAttribute('data-end'));
  const initialLine = await page.locator('.chart-line.download').getAttribute('d');
  const initialRows = await page.locator('#traffic-history tbody tr').evaluateAll(rows => rows.map(row => [row.dataset.at, row.textContent]));
  await page.clock.fastForward(5500);
  assert.equal(await page.evaluate(() => document.activeElement.id), 'connection-link');
  assert.equal(Number(await page.locator('.traffic-chart').getAttribute('data-end')), initialEnd + 5000);
  const nextLine = await page.locator('.chart-line.download').getAttribute('d');
  assert.notEqual(nextLine, initialLine, 'The live trace advances after a poll');
  const nextRows = await page.locator('#traffic-history tbody tr').evaluateAll(rows => rows.map(row => [row.dataset.at, row.textContent]));
  assert.deepEqual(nextRows.slice(0, -1), initialRows.slice(1), 'Old measurements keep their times and values while a new sample enters');
  const oldPoints = [...initialLine.matchAll(/[ML]([\d.]+),([\d.]+)/g)].map(match => [Number(match[1]), Number(match[2])]);
  const newPoints = [...nextLine.matchAll(/[ML]([\d.]+),([\d.]+)/g)].map(match => [Number(match[1]), Number(match[2])]);
  assert.ok(Math.abs(oldPoints[1][0] - newPoints[0][0] - 640 / 60) < .02, 'The same sample moves left on the chart');
  assert.equal(oldPoints[1][1], newPoints[0][1], 'A retained sample keeps its height');

  for (const scenario of ['reconnecting', 'offline']) {
    await page.selectOption('#scenario', scenario);
    await page.waitForFunction(expected => document.querySelector('#quality-state')?.textContent === expected,
      scenario === 'offline' ? 'Brak LTE' : 'Tor łączy się');
    assert.equal(await page.locator('#connection-state').textContent(), 'Ruch do internetu zablokowany');
    assert.equal(await page.locator('#protection-firewall').textContent(), 'Aktywna');
    assert.equal(await page.locator('#protection-dns').textContent(), 'Ruch wstrzymany');
    assert.equal(await page.locator('#tor-response').textContent(), 'Brak danych');
    assert.match(await page.locator('#download-speed').textContent(), /^0,0/);
  }
  assert.equal(await page.locator('#lte-disconnects').textContent(), '1');
  await page.selectOption('#scenario', 'weak-signal');
  await page.waitForFunction(() => document.querySelector('#lte-signal')?.textContent === '24 %');
  assert.equal(await page.locator('#connection-state').textContent(), 'Ochrona ruchu aktywna');
  assert.equal(await page.locator('#lte-disconnects').textContent(), '1');
  assert.match(await page.locator('#connection-quality').textContent(), /RSRP -112 dBm/);
  await page.selectOption('#scenario', 'protected');
  await page.waitForFunction(() => document.querySelector('#lte-signal')?.textContent === '76 %');
  await page.getByLabel('Okres statystyk').selectOption('1h');
  assert.equal(await page.getByLabel('Okres statystyk').inputValue(), '1h');
  await page.locator('#traffic-history summary').click();
  await page.clock.fastForward(5500);
  assert.equal(await page.locator('#traffic-history').evaluate(element => element.open), true);
  const historyCount = await page.locator('#traffic-history tbody tr').count();
  assert.ok(historyCount >= 49 && historyCount <= 50);
  await page.getByLabel('Widok wykresu').selectOption('live');
  assert.equal(await page.locator('#traffic-history tbody tr').count(), 61);
  await page.locator('#traffic-history summary').click();
  await page.locator('nav a[href="#dns"]').click();
  await page.getByLabel('Status zapytania').selectOption('blocked');
  await page.getByRole('searchbox').fill('telemetry');
  assert.ok(await page.locator('#query-rows tr').count() > 0);
  assert.ok((await page.locator('#query-rows tr td:nth-child(2)').allTextContents()).every(domain => domain.includes('telemetry')));
  await page.clock.fastForward(5500);
  assert.equal(await page.getByRole('searchbox').inputValue(), 'telemetry');
  assert.equal(await page.evaluate(() => document.activeElement.id), 'domain-search');
  await page.getByRole('searchbox').fill('no-such-domain');
  await page.getByRole('searchbox').press('Enter');
  assert.match(await page.locator('#query-rows').textContent(), /Brak zapytań/);
  await page.getByRole('searchbox').fill('');
  await page.getByLabel('Status zapytania').selectOption('all');

  for (const width of [1440, 1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    for (const route of ['overview', 'network', 'dns', 'system']) {
      await page.locator(`nav a[href="#${route}"]`).click();
      await page.waitForFunction(expected => document.body.dataset.page === expected, route);
      assert.ok(await page.locator('#content').textContent(), `${route} renders at ${width}px`);
      assert.equal(await page.locator('#error-notice').isVisible(), false);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `${route} must fit ${width}px without horizontal page scrolling`);
      assert.equal(await page.locator('nav [aria-current="page"]').count(), 1);
      if (width === 1440 || width === 390) {
        await page.mouse.move(0, 0);
        await page.screenshot({ path: new URL(`../.artifacts/${engine}-${route}-${width}.png`, import.meta.url).pathname, fullPage: true });
      }
    }
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator('nav a[href="#overview"]').click();
  await page.waitForFunction(() => document.body.dataset.page === 'overview');
  await page.mouse.move(0, 0);
  await page.screenshot({ path: new URL(`../.artifacts/${engine}-mobile.png`, import.meta.url).pathname, fullPage: true });

  if (process.env.DASHBOARD_URL) {
    const live = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
    live.on('pageerror', error => errors.push(error.message));
    const apiURL = new URL('?source=api', target).href;
    await live.goto(apiURL);
    await live.locator('#error-notice').waitFor();
    assert.match(await live.locator('#error-notice').textContent(), /nie dostarcza jeszcze odczytów/);
    assert.equal(await live.locator('#demo-notice').isVisible(), false);
    assert.equal(await live.locator('#connection-state').count(), 0);
    assert.equal(await live.locator('.metric-card').count(), 0);

    let payload = await new MockDataSource().getSnapshot();
    payload.source = 'live';
    payload.state = 'unknown';
    payload.lte.connected = null;
    payload.tor.status = 'unknown';
    payload.tor.killSwitch = null;
    payload.tor.dnsProtected = null;
    payload.traffic.downloadMbps = null;
    payload.traffic.uploadMbps = null;
    payload.traffic.history[24].download = null;
    payload.traffic.recentHistory[24].download = null;
    await live.route('**/api/v1/dashboard?**', route => route.fulfill({ json: { ...payload, collectedAt: new Date().toISOString() } }));
    await live.getByRole('button', { name: /Spróbuj ponownie/ }).click();
    await live.locator('#connection-state').waitFor();
    assert.equal(await live.locator('#connection-state').textContent(), 'Brak potwierdzenia ochrony');
    assert.equal(await live.locator('#protection-firewall').textContent(), 'Brak danych');
    assert.equal(await live.locator('#protection-dns').textContent(), 'Brak danych');
    assert.equal(await live.locator('#quality-state').textContent(), 'Brak pomiaru');
    assert.equal(await live.locator('#tor-response').textContent(), 'Brak danych');
    assert.equal(await live.locator('#lte-signal').textContent(), 'Brak danych');
    assert.equal(await live.locator('#download-speed').textContent(), 'Brak danych');
    assert.equal(await live.locator('.chart-line.download').count(), 2, 'Missing history splits the chart into separate lines');
    assert.doesNotMatch(await live.locator('.traffic-chart').innerHTML(), /NaN|Infinity/);
    payload = { ...await new MockDataSource().getSnapshot(), source: 'live' };
    delete payload.connectivity;
    await live.getByRole('button', { name: 'Odśwież dane' }).click();
    await live.waitForFunction(() => document.querySelector('#connection-state')?.textContent === 'Ochrona ruchu aktywna');
    assert.equal(await live.locator('#quality-state').textContent(), 'Brak pomiaru');
    assert.equal(await live.locator('#tor-response').textContent(), 'Brak danych');
    assert.equal(await live.locator('#lte-disconnects').textContent(), 'Brak danych');
    payload.connectivity = { torReachable: false, torResponseMs: null, checkedAt: new Date().toISOString(), lteDisconnectsLastHour: 2 };
    await live.getByRole('button', { name: 'Odśwież dane' }).click();
    await live.waitForFunction(() => document.querySelector('#quality-state')?.textContent === 'Brak odpowiedzi');
    assert.equal(await live.locator('#connection-state').textContent(), 'Ochrona ruchu aktywna', 'Availability and protection are separate');
    assert.equal(await live.locator('#tor-response').textContent(), 'Brak danych');
    payload.connectivity = { ...payload.connectivity, torReachable: true, torResponseMs: 380, checkedAt: new Date(Date.now() - 60000).toISOString() };
    await live.getByRole('button', { name: 'Odśwież dane' }).click();
    await live.waitForFunction(() => document.querySelector('#quality-state')?.textContent === 'Brak pomiaru');
    assert.equal(await live.locator('#tor-response').textContent(), 'Brak danych', 'A stale successful probe cannot confirm connectivity');
    assert.equal(await live.locator('#lte-disconnects').textContent(), '2');
    await live.route('**/api/v1/dashboard?**', route => route.fulfill({ status: 503, json: { error: 'unavailable' } }));
    await live.getByRole('button', { name: 'Odśwież dane' }).click();
    await live.locator('#error-notice').waitFor();
    assert.equal(await live.locator('#connection-state').count(), 0, 'An API failure clears the previous state');
    assert.equal(await live.locator('.metric-card').count(), 0, 'An API failure clears old metrics');
    assert.equal(await live.locator('.health-card').count(), 0, 'An API failure clears protection and connectivity');
    await live.screenshot({ path: new URL(`../.artifacts/${engine}-api-error.png`, import.meta.url).pathname, fullPage: true });
    await live.close();
  }
  assert.deepEqual(errors, []);
  console.log(`${engine}: views, scenarios, filters, chart, refresh, focus, 320–1440px layouts${process.env.DASHBOARD_URL ? ', API error and missing measurements' : ', standalone preview'} passed.`);
} finally {
  await browser.close();
}
