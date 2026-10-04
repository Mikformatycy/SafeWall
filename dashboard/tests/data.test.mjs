import test from 'node:test';
import assert from 'node:assert/strict';
import { MockDataSource, PiDataSource } from '../dist/data.js';
import { validateSnapshot } from '../dist/contract.js';

const mock = new MockDataSource();
async function liveSnapshot() { return { ...await mock.getSnapshot(), source: 'live' }; }

test('demo has explicit provenance, bounded time windows and coherent counters', async () => {
  for (const period of ['1h', '6h', '24h']) {
    const data = await mock.getSnapshot({ period });
    assert.equal(data.source, 'mock');
    assert.equal(data.period, period);
    assert.ok(data.dns.blocked <= data.dns.total);
    assert.ok(data.traffic.history.length >= 49 && data.traffic.history.length <= 50);
    const duration = Date.parse(data.traffic.history.at(-1).at) - Date.parse(data.traffic.history[0].at);
    assert.equal(duration, Number.parseInt(period) * 3600000);
    assert.ok(data.dns.queries.every(query => Date.parse(query.at) >= Date.parse(data.collectedAt) - duration));
  }
});

test('live demo traffic appends samples without rewriting past measurements', async t => {
  let now = Date.parse('2026-10-03T12:00:00Z');
  t.mock.method(Date, 'now', () => now);
  const source = new MockDataSource();
  const first = await source.getSnapshot();
  now += 5000;
  const next = await source.getSnapshot();
  assert.equal(first.traffic.recentHistory.length, 61);
  assert.deepEqual(next.traffic.recentHistory.slice(0, -1), first.traffic.recentHistory.slice(1));
  assert.equal(Date.parse(next.traffic.recentHistory.at(-1).at), now);
  assert.equal(next.traffic.recentHistory.at(-1).download, next.traffic.downloadMbps);
  assert.equal(next.traffic.recentHistory.at(-1).upload, next.traffic.uploadMbps);
  const previous = new Map(first.traffic.history.map(point => [point.at, point]));
  for (const point of next.traffic.history) {
    if (previous.has(point.at)) assert.deepEqual(point, previous.get(point.at));
  }
  const anotherRange = await source.getSnapshot({ period: '1h' });
  assert.deepEqual(anotherRange.traffic.recentHistory, next.traffic.recentHistory);
  assert.ok(anotherRange.traffic.downloadBytes < next.traffic.downloadBytes);
});

test('demo traffic has short bursts and quiet gaps instead of smooth oscillations', async t => {
  t.mock.method(Date, 'now', () => Date.parse('2026-10-03T12:00:00Z'));
  const { traffic } = await new MockDataSource().getSnapshot();
  const rates = traffic.recentHistory.map(point => point.download);
  assert.ok(rates.filter(value => value < 1).length > rates.length * .6);
  assert.ok(rates.filter(value => value > 10).length >= 3);
  assert.ok(rates.some((value, i) => i > 0 && Math.abs(value - rates[i - 1]) > 10));
  assert.ok(traffic.recentHistory.some(point => point.upload > 2));
});

test('outages stay in history after reconnection and long pauses keep memory bounded', async t => {
  let now = Date.parse('2026-10-03T12:00:00Z');
  t.mock.method(Date, 'now', () => now);
  const source = new MockDataSource();
  const before = await source.getSnapshot();
  now += 5000;
  await source.getSnapshot({ scenario: 'offline' });
  now += 15000;
  const after = await source.getSnapshot({ scenario: 'protected' });
  const outage = after.traffic.recentHistory.filter(point => Date.parse(point.at) > Date.parse(before.collectedAt) && Date.parse(point.at) < now);
  assert.equal(outage.length, 3);
  assert.ok(outage.every(point => point.download === 0 && point.upload === 0));
  now += 2 * 24 * 3600000;
  const resumed = await source.getSnapshot();
  assert.equal(resumed.traffic.recentHistory.length, 61);
  assert.equal(source.samples.length, 17281);
  assert.ok(source.samples.every(point => point.at >= now - 24 * 3600000));
});

test('optional recent API history validates samples and permits unavailable readings', async () => {
  const data = await liveSnapshot();
  data.traffic.recentHistory[0].download = null;
  assert.equal(validateSnapshot(data, 'live'), data);
  data.traffic.recentHistory[0].download = -1;
  assert.throws(() => validateSnapshot(data, 'live'), /ujemny/);
  delete data.traffic.recentHistory;
  assert.equal(validateSnapshot(data, 'live'), data);
});

test('Tor reconnect and LTE loss stop simulated traffic but preserve the local client', async () => {
  for (const scenario of ['reconnecting', 'offline']) {
    const data = await mock.getSnapshot({ scenario });
    assert.equal(data.state, scenario);
    assert.equal(data.traffic.downloadMbps, 0);
    assert.equal(data.traffic.uploadMbps, 0);
    assert.equal(data.tor.killSwitch, true);
    assert.equal(data.tor.exitIp, null);
    assert.equal(data.clients[0].active, true);
  }
});

test('unavailable measurements stay null instead of becoming healthy-looking readings', async () => {
  const data = await mock.getSnapshot({ scenario: 'offline' });
  assert.equal(data.lte.rsrpDbm, null);
  assert.equal(data.lte.latencyMs, null);
  assert.equal(data.system.batteryPercent, null);
});

test('weak LTE affects connection measurements without disabling confirmed protection', async () => {
  const source = new MockDataSource();
  const normal = await source.getSnapshot();
  const weak = await source.getSnapshot({ scenario: 'weak-signal' });
  assert.equal(weak.state, 'protected');
  assert.equal(weak.connectivity.torReachable, true);
  assert.ok(weak.connectivity.torResponseMs > normal.connectivity.torResponseMs);
  assert.ok(weak.lte.signalPercent < normal.lte.signalPercent);
  assert.equal(weak.connectivity.checkedAt, weak.collectedAt);
});

test('LTE disconnect counter records transitions once and expires events after one hour', async t => {
  let now = Date.parse('2026-10-04T12:00:00Z');
  t.mock.method(Date, 'now', () => now);
  const source = new MockDataSource();
  assert.equal((await source.getSnapshot()).connectivity.lteDisconnectsLastHour, 0);
  assert.equal((await source.getSnapshot({ scenario: 'reconnecting' })).connectivity.lteDisconnectsLastHour, 0);
  now += 5000;
  const offline = await source.getSnapshot({ scenario: 'offline' });
  assert.equal(offline.connectivity.lteDisconnectsLastHour, 1);
  assert.equal(offline.connectivity.torReachable, null);
  assert.equal(offline.connectivity.torResponseMs, null);
  assert.equal((await source.getSnapshot({ scenario: 'offline' })).connectivity.lteDisconnectsLastHour, 1);
  assert.equal((await source.getSnapshot()).connectivity.lteDisconnectsLastHour, 1);
  now += 3600000;
  assert.equal((await source.getSnapshot()).connectivity.lteDisconnectsLastHour, 0);
});

test('optional connectivity readings allow missing data and do not determine protection', async () => {
  const data = await liveSnapshot();
  delete data.connectivity;
  assert.equal(validateSnapshot(data, 'live'), data);
  data.connectivity = null;
  assert.equal(validateSnapshot(data, 'live'), data);
  data.connectivity = { torReachable: null, torResponseMs: null, checkedAt: null, lteDisconnectsLastHour: null };
  assert.equal(validateSnapshot(data, 'live'), data);
  data.connectivity.torReachable = false;
  data.connectivity.checkedAt = data.collectedAt;
  assert.equal(validateSnapshot(data, 'live'), data);
  assert.equal(data.state, 'protected');
});

test('invalid connectivity values and contradictory probe results are rejected', async () => {
  for (const patch of [
    { torResponseMs: -1 }, { lteDisconnectsLastHour: -1 }, { lteDisconnectsLastHour: 1.5 },
    { checkedAt: 'invalid' }, { checkedAt: null }, { torReachable: 'yes' },
    { torReachable: false, torResponseMs: 100 }, { torReachable: null, torResponseMs: 100 },
  ]) {
    const data = await liveSnapshot();
    Object.assign(data.connectivity, patch);
    assert.throws(() => validateSnapshot(data, 'live'), /Nieprawidłowe dane panelu/);
  }
});

test('the live contract rejects demo data and unsupported schemas', async () => {
  const data = await mock.getSnapshot();
  assert.throws(() => validateSnapshot(data, 'live'), /źródło/);
  assert.throws(() => validateSnapshot({ ...data, schemaVersion: 2 }, 'mock'), /wersja/);
});

test('protected state requires affirmative evidence for every essential protection', async () => {
  for (const field of ['killSwitch', 'dnsProtected', 'ipv6Blocked', 'udpBlocked']) {
    const data = await liveSnapshot();
    data.tor[field] = null;
    assert.throws(() => validateSnapshot(data, 'live'), /ochrona bez potwierdzenia/);
  }
});

test('invalid count and sensor values are rejected before rendering', async () => {
  const data = await liveSnapshot();
  data.system.cpuPercent = 170;
  assert.throws(() => validateSnapshot(data, 'live'), /cpuPercent/);
  data.system.cpuPercent = 17;
  data.dns.blocked = data.dns.total + 1;
  assert.throws(() => validateSnapshot(data, 'live'), /licznik blokad/);
});

test('live adapter accepts fresh validated data for the requested range', async t => {
  const data = await liveSnapshot();
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, '/api/v1/dashboard?period=24h');
    assert.equal(options.cache, 'no-store');
    return new Response(JSON.stringify(data));
  });
  assert.deepEqual(await new PiDataSource().getSnapshot(), data);
});

test('live adapter reports unavailable data without falling back to mocks', async t => {
  t.mock.method(globalThis, 'fetch', async () => new Response('{}', { status: 503 }));
  await assert.rejects(new PiDataSource().getSnapshot(), /nie dostarcza/);
});

test('live adapter rejects stale samples, wrong ranges and mock responses', async t => {
  const data = await liveSnapshot();
  const fetchMock = t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify({ ...data, collectedAt: new Date(Date.now() - 60000).toISOString() })));
  await assert.rejects(new PiDataSource().getSnapshot(), /nieaktualne/);
  fetchMock.mock.mockImplementation(async () => new Response(JSON.stringify({ ...data, period: '6h' })));
  await assert.rejects(new PiDataSource().getSnapshot(), /innego okresu/);
  fetchMock.mock.mockImplementation(async () => new Response(JSON.stringify({ ...data, source: 'mock' })));
  await assert.rejects(new PiDataSource().getSnapshot(), /źródło/);
});

test('demo reads respect cancellation', async () => {
  const controller = new AbortController();
  controller.abort();
  await assert.rejects(mock.getSnapshot({ signal: controller.signal }), { name: 'AbortError' });
});
