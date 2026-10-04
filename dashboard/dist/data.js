import { validateSnapshot, DataSourceError } from './contract.js';
import { dashboardConfig } from './config.js';

const periodHours = { '1h': 1, '6h': 6, '24h': 24 };
const sampleIntervalMs = 5000;
const retentionMs = 24 * 3600000;

// Timestamp-seeded traffic: brief downloads/uploads separated by quiet periods.
// A timestamp always has the same value, including after a range change.
function noise(seed) {
  let n = Math.imul(seed ^ (seed >>> 16), 0x45d9f3b);
  n = Math.imul(n ^ (n >>> 16), 0x45d9f3b);
  return ((n ^ (n >>> 16)) >>> 0) / 4294967296;
}

function burst(tick, blockSize, salt, peak) {
  const block = Math.floor(tick / blockSize);
  const seed = block + salt;
  const duration = 1 + Math.floor(noise(seed + 17) * 3);
  const offset = Math.floor(noise(seed + 31) * (blockSize - duration));
  const phase = tick - block * blockSize - offset;
  if (noise(seed + 53) < .15 || phase < 0 || phase >= duration) return 0;
  const shape = phase === 0 ? 1 : phase === 1 ? .35 + noise(seed + 71) * .6 : .12;
  return peak * (.4 + noise(seed + 97) * .6) * shape;
}

function trafficSample(at, connected) {
  const tick = Math.floor(at / sampleIntervalMs);
  const background = noise(tick + 7) > .9 ? noise(tick + 11) * 2 : noise(tick + 13) * .12;
  const download = connected ? burst(tick, 12, 101, 28) + background : 0;
  const upload = connected ? burst(tick, 17, 503, 8) + download * .018 + noise(tick + 19) * .06 : 0;
  return { at, download: +download.toFixed(2), upload: +upload.toFixed(2) };
}

const serializeSample = sample => ({ ...sample, at: new Date(sample.at).toISOString() });
const domains = [
  ['telemetry.example.com', 'Telemetria', 'blocked'],
  ['metrics.example.net', 'Analityka', 'blocked'],
  ['cdn.example.org', 'Treści', 'allowed'],
  ['ads.example.com', 'Reklamy', 'blocked'],
  ['docs.example.org', 'Treści', 'allowed'],
  ['tracking.example.net', 'Śledzenie', 'blocked'],
  ['static.example.com', 'Treści', 'allowed'],
  ['api.example.org', 'Treści', 'allowed'],
];

export class MockDataSource {
  kind = 'mock';
  samples = [];
  trafficConnected = true;
  lteConnected = true;
  lteDisconnects = [];

  sampleTraffic(now, connected, hours) {
    const end = Math.floor(now / sampleIntervalMs) * sampleIntervalMs;
    const earliest = end - retentionMs;
    const previous = this.samples.at(-1)?.at;
    // Bounded backfill also handles a sleeping tab or a clock adjustment.
    if (previous == null || previous > end) {
      this.samples = [];
      this.trafficConnected = true;
    }
    const from = Math.max(earliest, (this.samples.at(-1)?.at ?? earliest - sampleIntervalMs) + sampleIntervalMs);
    for (let at = from; at <= end; at += sampleIntervalMs) {
      this.samples.push(trafficSample(at, at === end ? connected : this.trafficConnected));
    }
    // A demo scenario change may update the current, unfinished 5-second slot.
    if (this.trafficConnected !== connected) this.samples[this.samples.length - 1] = trafficSample(end, connected);
    this.trafficConnected = connected;
    const first = this.samples.findIndex(point => point.at >= earliest);
    if (first > 0) this.samples.splice(0, first);
    const duration = hours * 3600000;
    const window = this.samples.filter(point => point.at >= end - duration);
    // Sample the longer view on a fixed clock grid, never a moving array index.
    const history = window.filter((point, i) => i === 0 || i === window.length - 1 || point.at % (duration / 48) === 0).map(serializeSample);
    const recentHistory = this.samples.slice(-61).map(serializeSample);
    const current = this.samples.at(-1);
    const total = key => Math.round(window.slice(0, -1).reduce((sum, point) => sum + point[key] * sampleIntervalMs * 125, 0));
    return { downloadMbps: current.download, uploadMbps: current.upload, downloadBytes: total('download'), uploadBytes: total('upload'), history, recentHistory };
  }

  async getSnapshot({ period = '24h', scenario = 'protected', signal } = {}) {
    if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');
    const now = Date.now();
    const hours = periodHours[period] || 24;
    const connected = scenario !== 'offline';
    const weakSignal = scenario === 'weak-signal';
    const protectedState = scenario === 'protected' || weakSignal;
    if (this.lteConnected && !connected) this.lteDisconnects.push(now);
    this.lteConnected = connected;
    this.lteDisconnects = this.lteDisconnects.filter(at => at > now - 3600000 && at <= now);
    const total = Math.round(18462 * hours / 24);
    const blocked = Math.round(3284 * hours / 24);
    const queries = Array.from({ length: 32 }, (_, i) => {
      const [domain, category, status] = domains[(i * 3) % domains.length];
      return { id: `demo-query-${i}`, at: new Date(now - i * hours * 34000).toISOString(), domain, category, status, client: 'iPhone', responseMs: status === 'blocked' ? 0 : 24 + i % 17 };
    });
    const data = {
      schemaVersion: 1, source: 'mock', collectedAt: new Date(now).toISOString(), period, state: protectedState ? 'protected' : scenario,
      traffic: this.sampleTraffic(now, protectedState, hours),
      lte: { connected, operator: 'T-Mobile', technology: 'LTE', model: 'Quectel EG25-G', band: 'B3 · 1800 MHz', rsrpDbm: connected ? weakSignal ? -112 : -87 : null, rsrqDb: connected ? weakSignal ? -17 : -9 : null, sinrDb: connected ? weakSignal ? 2 : 18 : null, signalPercent: connected ? weakSignal ? 24 : 76 : 0, latencyMs: connected ? weakSignal ? 165 : 42 : null, interface: 'wwan0' },
      connectivity: {
        torReachable: protectedState ? true : null,
        torResponseMs: protectedState ? Math.round((weakSignal ? 1250 : 340) + noise(Math.floor(now / 5000) + 991) * (weakSignal ? 400 : 140)) : null,
        checkedAt: protectedState ? new Date(now).toISOString() : null,
        lteDisconnectsLastHour: this.lteDisconnects.length,
      },
      tor: {
        status: protectedState ? 'ready' : connected ? 'connecting' : 'offline', bootstrapPercent: protectedState ? 100 : connected ? 42 : 0,
        exitCountry: protectedState ? 'Holandia' : null, exitIp: protectedState ? '198.51.100.24' : null,
        bridge: false, killSwitch: true, dnsProtected: protectedState, ipv6Blocked: true, udpBlocked: true,
      },
      dns: { total, blocked, ruleCount: 128450, enabled: true, topBlocked: [
        { domain: 'telemetry.example.com', category: 'Telemetria', count: Math.round(blocked * .39) },
        { domain: 'metrics.example.net', category: 'Analityka', count: Math.round(blocked * .28) },
        { domain: 'ads.example.com', category: 'Reklamy', count: Math.round(blocked * .18) },
        { domain: 'tracking.example.net', category: 'Śledzenie', count: Math.round(blocked * .10) },
      ], queries },
      clients: [{ id: 'demo-phone', name: 'iPhone', address: '192.168.76.72', connection: 'Ethernet', active: true }],
      interfaces: [
        { name: 'Telefon / Ethernet', role: 'LAN · brama i DNS', address: '192.168.76.1' },
        { name: 'Administracja / USB-C', role: 'Połączenie z komputerem', address: '10.12.194.1' },
      ],
      system: { name: 'SafeWall One', model: 'Raspberry Pi 4', hostname: 'safewall.local', cpuPercent: 17, memoryUsedBytes: 482000000, memoryTotalBytes: 2000000000, temperatureC: 46.2, uptimeSeconds: 15432, diskUsedBytes: 4200000000, diskTotalBytes: 32000000000, batteryPercent: null, version: '0.1.0', services: [
        { name: 'Tor', detail: 'Chronione połączenie', status: protectedState ? 'active' : 'waiting' },
        { name: 'Filtr DNS', detail: 'Reguły i lokalne zapytania', status: 'active' },
        { name: 'Zapora', detail: 'Blokada ruchu poza Torem', status: 'active' },
        { name: 'Modem LTE', detail: 'Połączenie komórkowe', status: connected ? 'active' : 'offline' },
      ] },
    };
    return validateSnapshot(data, 'mock');
  }
}

export class PiDataSource {
  kind = 'api';

  async getSnapshot({ period = '24h', signal } = {}) {
    const response = await fetch(`/api/v1/dashboard?period=${encodeURIComponent(period)}`, {
      signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(8000)]) : AbortSignal.timeout(8000),
      cache: 'no-store', headers: { Accept: 'application/json' },
    });
    if (!response.ok) {
      if (response.status === 503) throw new DataSourceError('Raspberry Pi nie dostarcza jeszcze odczytów.');
      throw new DataSourceError(`Nie udało się pobrać danych z urządzenia (HTTP ${response.status}).`);
    }
    const data = validateSnapshot(await response.json(), 'live');
    if (data.period !== period) throw new DataSourceError('Urządzenie zwróciło dane dla innego okresu.');
    const age = Date.now() - Date.parse(data.collectedAt);
    if (age > 30000 || age < -10000) throw new DataSourceError('Odczyty są nieaktualne lub zegar urządzenia jest niezgodny.');
    return data;
  }
}

export function createDataSource() {
  const useApi = dashboardConfig.dataSource === 'api' || new URLSearchParams(window.location.search).get('source') === 'api';
  return useApi ? new PiDataSource() : new MockDataSource();
}
