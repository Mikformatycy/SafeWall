import { createDataSource } from './data.js';
import { dashboardConfig } from './config.js';

const $ = selector => document.querySelector(selector);
const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[char]));
const number = (value, decimals = 0) => value == null ? 'Brak danych' : new Intl.NumberFormat('pl-PL', {
  maximumFractionDigits: decimals, minimumFractionDigits: decimals,
}).format(value);
const measurement = (value, unit, decimals = 0) => value == null ? 'Brak danych' : `${number(value, decimals)} ${unit}`;
const bytes = value => {
  if (value == null) return 'Brak danych';
  const divisor = value >= 1e9 ? 1e9 : value >= 1e6 ? 1e6 : 1e3;
  return measurement(value / divisor, divisor === 1e9 ? 'GB' : divisor === 1e6 ? 'MB' : 'kB', 2);
};
const time = value => new Date(value).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' });
const sampleTime = value => new Date(value).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
const flag = (value, yes = 'Aktywne', no = 'Nieaktywne') => value == null ? 'Brak danych' : value ? yes : no;
const text = value => escape(value ?? 'Brak danych');
const periods = { '1h': 'Ostatnia godzina', '6h': 'Ostatnie 6 godzin', '24h': 'Ostatnie 24 godziny' };
const pages = {
  overview: ['Przegląd', 'Twoja sieć w jednym miejscu.'],
  network: ['Twoje połączenie.', 'Od modemu do sieci Tor.'],
  dns: ['Mniej niechcianego ruchu.', 'Twoje zapytania. Twój filtr DNS.'],
  system: ['Twój SafeWall.', 'Sprawdź, jak pracuje urządzenie.'],
};
const source = createDataSource();
const state = { page: 'overview', period: '24h', scenario: 'protected', dnsFilter: 'all', search: '', snapshot: null, busy: false, error: null, chartMode: 'live', recentTraffic: [], liveChartCeiling: 0 };
let requestId = 0;
let controller;

/*
 * Local SVG subset from lucide-static 1.51.0 (https://lucide.dev).
 * The original icon geometry is unchanged.
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
const icons = {
  down: "<path d=\"M12 5v14\" /> <path d=\"m19 12-7 7-7-7\" />", // arrow-down
  up: "<path d=\"m5 12 7-7 7 7\" /> <path d=\"M12 19V5\" />", // arrow-up
  arrow: "<path d=\"M5 12h14\" /> <path d=\"m12 5 7 7-7 7\" />", // arrow-right
  shield: "<path d=\"M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z\" /> <path d=\"m9 12 2 2 4-4\" />", // shield-check
  shieldUnknown: "<path d=\"M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z\" /> <path d=\"M9.1 9a3 3 0 0 1 5.82 1c0 2-3 3-3 3\" /> <path d=\"M12 17h.01\" />", // shield-question-mark
  shieldLocked: "<path d=\"M20 9.807V6a1 1 0 00-1-1c-2 0-4.49-1.19-6.24-2.72a1.17 1.17 0 00-1.52 0C9.5 3.8 7 5 5 5a1 1 0 00-1 1v7c0 3.88 2.107 6.254 5 7.796\" /> <path d=\"M19 17v-2a2 2 0 00-4 0v2\" /> <rect x=\"13\" y=\"17\" width=\"8\" height=\"5\" rx=\"1\" />", // shield-lock
  signal: "<path d=\"M2 20h.01\" /> <path d=\"M7 20v-4\" /> <path d=\"M12 20v-8\" /> <path d=\"M17 20V8\" /> <path d=\"M22 4v16\" />", // signal
  signalHigh: "<path d=\"M2 20h.01\" /> <path d=\"M7 20v-4\" /> <path d=\"M12 20v-8\" /> <path d=\"M17 20V8\" />", // signal-high
  signalMedium: "<path d=\"M2 20h.01\" /> <path d=\"M7 20v-4\" /> <path d=\"M12 20v-8\" />", // signal-medium
  signalLow: "<path d=\"M2 20h.01\" /> <path d=\"M7 20v-4\" />", // signal-low
  signalZero: "<path d=\"M2 20h.01\" />", // signal-zero
  globe: "<circle cx=\"12\" cy=\"12\" r=\"10\" /> <path d=\"M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20\" /> <path d=\"M2 12h20\" />", // globe
  phone: "<rect width=\"14\" height=\"20\" x=\"5\" y=\"2\" rx=\"2\" ry=\"2\" /> <path d=\"M12 18h.01\" />", // smartphone
  cpu: "<path d=\"M12 20v2\" /> <path d=\"M12 2v2\" /> <path d=\"M17 20v2\" /> <path d=\"M17 2v2\" /> <path d=\"M2 12h2\" /> <path d=\"M2 17h2\" /> <path d=\"M2 7h2\" /> <path d=\"M20 12h2\" /> <path d=\"M20 17h2\" /> <path d=\"M20 7h2\" /> <path d=\"M7 20v2\" /> <path d=\"M7 2v2\" /> <rect x=\"4\" y=\"4\" width=\"16\" height=\"16\" rx=\"2\" /> <rect x=\"8\" y=\"8\" width=\"8\" height=\"8\" rx=\"1\" />", // cpu
  memory: "<path d=\"M12 12v-2\" /> <path d=\"M12 18v-2\" /> <path d=\"M16 12v-2\" /> <path d=\"M16 18v-2\" /> <path d=\"M2 11h1.5\" /> <path d=\"M20 18v-2\" /> <path d=\"M20.5 11H22\" /> <path d=\"M4 18v-2\" /> <path d=\"M8 12v-2\" /> <path d=\"M8 18v-2\" /> <rect x=\"2\" y=\"6\" width=\"20\" height=\"10\" rx=\"2\" />", // memory-stick
  temperature: "<path d=\"M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z\" />", // thermometer
  search: "<path d=\"m21 21-4.34-4.34\" /> <circle cx=\"11\" cy=\"11\" r=\"8\" />", // search
  check: "<path d=\"M20 6 9 17l-5-5\" />", // check
  lock: "<circle cx=\"12\" cy=\"16\" r=\"1\" /> <rect x=\"3\" y=\"10\" width=\"18\" height=\"12\" rx=\"2\" /> <path d=\"M7 10V7a5 5 0 0 1 10 0v3\" />", // lock-keyhole
  timer: "<line x1=\"10\" x2=\"14\" y1=\"2\" y2=\"2\" /> <line x1=\"12\" x2=\"15\" y1=\"14\" y2=\"11\" /> <circle cx=\"12\" cy=\"14\" r=\"8\" />", // timer
  clock: "<circle cx=\"12\" cy=\"12\" r=\"10\" /> <path d=\"M12 6v6l4 2\" />", // clock
  disconnect: "<path d=\"m19 5 3-3\" /> <path d=\"m2 22 3-3\" /> <path d=\"M6.3 20.3a2.4 2.4 0 0 0 3.4 0L12 18l-6-6-2.3 2.3a2.4 2.4 0 0 0 0 3.4Z\" /> <path d=\"M7.5 13.5 10 11\" /> <path d=\"M10.5 16.5 13 14\" /> <path d=\"m12 6 6 6 2.3-2.3a2.4 2.4 0 0 0 0-3.4l-2.6-2.6a2.4 2.4 0 0 0-3.4 0Z\" />", // unplug
  route: "<path d=\"m10.586 5.414-5.172 5.172\" /> <path d=\"m18.586 13.414-5.172 5.172\" /> <path d=\"M6 12h12\" /> <circle cx=\"12\" cy=\"20\" r=\"2\" /> <circle cx=\"12\" cy=\"4\" r=\"2\" /> <circle cx=\"20\" cy=\"12\" r=\"2\" /> <circle cx=\"4\" cy=\"12\" r=\"2\" />", // waypoints
  dns: "<rect width=\"20\" height=\"8\" x=\"2\" y=\"2\" rx=\"2\" ry=\"2\" /> <rect width=\"20\" height=\"8\" x=\"2\" y=\"14\" rx=\"2\" ry=\"2\" /> <line x1=\"6\" x2=\"6.01\" y1=\"6\" y2=\"6\" /> <line x1=\"6\" x2=\"6.01\" y1=\"18\" y2=\"18\" />", // server
  refresh: "<path d=\"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8\" /> <path d=\"M21 3v5h-5\" /> <path d=\"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16\" /> <path d=\"M8 16H3v5\" />", // refresh-cw
};
const icon = name => `<svg class="icon" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">${icons[name] || icons.shield}</svg>`;
const statusTag = (value, yes = 'Aktywne', no = 'Nieaktywne') => `<span class="status-tag ${value == null ? 'unknown' : value ? 'positive' : 'inactive'}"><span class="status-dot"></span>${flag(value, yes, no)}</span>`;
const ratio = (used, total) => used == null || total == null ? null : total ? used / total * 100 : 0;
const units = (value, unit, decimals = 0) => value == null ? '<span class="missing-value">Brak danych</span>' : `${number(value, decimals)} <span class="unit">${unit}</span>`;

// Values are formatted or escaped by the caller.
function definitions(rows) {
  return `<dl class="data-list">${rows.map(([label, value]) => `<div><dt>${escape(label)}</dt><dd>${value}</dd></div>`).join('')}</dl>`;
}

function periodControl(label = 'Aktywność sieci') {
  return `<div class="section-toolbar"><h2 id="activity-heading">${label}</h2><label class="period-control"><span class="sr-only">Okres statystyk</span><select id="period">${Object.entries(periods).map(([value, label]) => `<option value="${value}"${state.period === value ? ' selected' : ''}>${label}</option>`).join('')}</select></label></div>`;
}

function statusInfo(data) {
  if (data.state === 'protected') return { title: 'Ochrona ruchu aktywna', description: 'Tor połączony. Ruch poza Torem jest blokowany.', tone: 'positive' };
  if (data.state === 'reconnecting') return { title: 'Ruch do internetu zablokowany', description: 'Tor nawiązuje połączenie. Blokada wyjścia pozostaje aktywna.', tone: 'waiting' };
  if (data.state === 'offline') return { title: 'Ruch do internetu zablokowany', description: 'Brak LTE. Panel lokalny i blokada wyjścia nadal działają.', tone: 'inactive' };
  return { title: 'Brak potwierdzenia ochrony', description: 'Brakuje pomiarów potrzebnych do potwierdzenia ochrony ruchu.', tone: 'unknown' };
}

function metric({ label, value, detail, name, tone = 'blue', id = '' }) {
  return `<section class="metric-card ${tone}"><div class="metric-label"><span class="metric-icon">${icon(name)}</span><h3>${label}</h3></div><p class="metric-value"${id ? ` id="${id}"` : ''}>${value}</p><p class="metric-detail">${detail}</p></section>`;
}

function protection(data) {
  const status = statusInfo(data);
  return `<section class="card protection-card"><div class="card-heading"><h2 id="connection-state">${status.title}</h2>${statusTag(data.state === 'unknown' ? null : data.state === 'protected', 'Połączono', 'Wstrzymano')}</div><p class="muted">${status.description}</p>${connectionPath(data)}${definitions([
    ['Blokada wyjścia poza Tor', statusTag(data.tor.killSwitch)],
    ['Wyjście Tor', text(data.tor.exitCountry)],
    ['Adres IP wyjścia', `<span class="mono">${text(data.tor.exitIp)}</span>`],
  ])}</section>`;
}

function connectionPath(data) {
  const nodes = [
    ['signal', 'LTE', data.lte.connected],
    ['shield', 'Tor', data.tor.status === 'unknown' ? null : data.tor.status === 'ready'],
    ['globe', 'Internet', data.state === 'unknown' ? null : data.state === 'protected'],
  ];
  return `<div class="connection-path" aria-label="Ścieżka połączenia">${nodes.map(([name, label, active], i) => `${i ? '<span class="path-connector" aria-hidden="true"></span>' : ''}<div class="path-node ${active === true ? 'connected' : 'disconnected'}"><span class="path-icon">${icon(name)}</span><span>${label}</span><span class="sr-only">: ${flag(active, 'Połączono', 'Brak połączenia')}</span></div>`).join('')}</div>`;
}

function rememberTraffic(data) {
  const end = Date.parse(data.collectedAt);
  // A Pi without recentHistory builds the live view from actual received readings.
  const points = data.traffic.recentHistory ?? [
    ...state.recentTraffic, ...data.traffic.history,
    { at: data.collectedAt, download: data.traffic.downloadMbps, upload: data.traffic.uploadMbps },
  ];
  state.recentTraffic = [...new Map(points.filter(point => Date.parse(point.at) >= end - 305000 && Date.parse(point.at) <= end).map(point => [point.at, point])).values()].sort((a, b) => Date.parse(a.at) - Date.parse(b.at));
}

function trafficChart(history) {
  if (!history.some(point => point.download != null || point.upload != null)) return '<p class="empty-state">Brak historii transferu.</p>';
  const live = state.chartMode === 'live';
  const width = 640, height = 164, left = 35, top = 12;
  const values = history.flatMap(point => [point.download, point.upload]).filter(Number.isFinite);
  let max = Math.max(5, Math.ceil(Math.max(...values) / 5) * 5);
  if (live) max = state.liveChartCeiling = Math.max(state.liveChartCeiling, max);
  const end = Math.max(...history.map(p => Date.parse(p.at)));
  const start = live ? end - 300000 : Math.min(...history.map(p => Date.parse(p.at)));
  const x = point => left + (end === start ? 0.5 : (Date.parse(point.at) - start) / (end - start)) * width;
  const y = value => top + height * (1 - value / max);
  // Missing measurements split the path, so gaps never become a false zero.
  const paths = key => {
    const segments = [];
    let segment = [];
    let previousTime;
    for (const point of history) {
      const at = Date.parse(point.at);
      if (live && previousTime != null && at - previousTime > dashboardConfig.pollIntervalMs * 1.5) {
        if (segment.length) segments.push(segment);
        segment = [];
      }
      previousTime = at;
      if (point[key] == null) { if (segment.length) segments.push(segment); segment = []; }
      else segment.push([x(point), y(point[key])]);
    }
    if (segment.length) segments.push(segment);
    return segments.map(points => {
      const line = points.map(([px, py], i) => `${i ? 'L' : 'M'}${px.toFixed(2)},${py.toFixed(2)}`).join(' ');
      const area = `${line} L${points.at(-1)[0]},${top + height} L${points[0][0]},${top + height} Z`;
      return `${key === 'download' && points.length > 1 ? `<path d="${area}" fill="url(#traffic-fill)"/>` : ''}<path d="${line}" class="chart-line ${key}"/>${points.length === 1 ? `<circle cx="${points[0][0]}" cy="${points[0][1]}" r="3" class="chart-point ${key}"/>` : ''}`;
    }).join('');
  };
  return `<svg class="traffic-chart" data-mode="${state.chartMode}" data-start="${start}" data-end="${end}" viewBox="0 0 690 206" role="img" aria-labelledby="chart-title chart-description"><title id="chart-title">Transfer · ${live ? 'ostatnie 5 minut' : periods[state.period]}</title><desc id="chart-description">Pobieranie i wysyłanie w Mb/s. Dokładne odczyty w rozwijanej historii transferu.</desc><defs><linearGradient id="traffic-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#3898ff" stop-opacity=".22"/><stop offset="100%" stop-color="#3898ff" stop-opacity="0"/></linearGradient><clipPath id="traffic-clip"><rect x="${left}" y="${top - 4}" width="${width}" height="${height + 8}"/></clipPath></defs>${[max, max / 2, 0].map(value => `<line class="chart-grid" x1="${left}" y1="${y(value)}" x2="${left + width}" y2="${y(value)}"/><text class="chart-label" x="24" y="${y(value) + 4}" text-anchor="end">${number(value, Number.isInteger(value) ? 0 : 1)}</text>`).join('')}<g clip-path="url(#traffic-clip)"><g class="chart-series">${paths('download')}${paths('upload')}</g></g>${[0, .25, .5, .75, 1].map((fraction, i) => `<text class="chart-label" x="${left + width * fraction}" y="201" text-anchor="${i === 0 ? 'start' : i === 4 ? 'end' : 'middle'}">${live && i === 4 ? 'Teraz' : time(start + (end - start) * fraction)}</text>`).join('')}</svg>`;
}

function traffic(data) {
  const live = state.chartMode === 'live';
  const history = live ? state.recentTraffic : data.traffic.history;
  const chartPeriod = live ? 'Ostatnie 5 minut · próbki co 5 s' : periods[state.period];
  return `<section class="card traffic-card" aria-labelledby="traffic-heading">
    <div class="card-heading"><h2 id="traffic-heading">Transfer</h2><label class="chart-mode"><span class="sr-only">Widok wykresu</span><select id="traffic-view"><option value="live"${live ? ' selected' : ''}>Na żywo · 5 min</option><option value="history"${live ? '' : ' selected'}>${periods[state.period]}</option></select></label></div>
    <div class="chart-legend"><span><i class="legend-dot blue"></i>Pobieranie</span><span><i class="legend-dot purple"></i>Wysyłanie</span><span class="chart-units">Mb/s</span></div>
    ${trafficChart(history)}
    <div class="traffic-totals"><span>Pobrano <strong>${bytes(data.traffic.downloadBytes)}</strong></span><span>Wysłano <strong>${bytes(data.traffic.uploadBytes)}</strong></span><span>${periods[state.period]}</span></div>
    <details id="traffic-history" class="disclosure"><summary>Historia transferu</summary><div id="history-table" class="table-scroll" tabindex="0" role="region" aria-label="Historia transferu"><table><caption class="sr-only">${chartPeriod}</caption><thead><tr><th scope="col">Czas</th><th scope="col">Pobieranie (Mb/s)</th><th scope="col">Wysyłanie (Mb/s)</th></tr></thead><tbody>${history.length ? history.map(point => `<tr data-at="${escape(point.at)}"><td>${live ? sampleTime(point.at) : time(point.at)}</td><td>${number(point.download, 2)}</td><td>${number(point.upload, 2)}</td></tr>`).join('') : '<tr><td colspan="3">Brak historii dla tego okresu.</td></tr>'}</tbody></table></div></details>
  </section>`;
}

function healthTag(label, tone = 'unknown') {
  return `<span class="health-tag ${tone}"><span class="status-dot"></span>${escape(label)}</span>`;
}

function protectionIllustration(data) {
  const protectedState = data.state === 'protected';
  const blocked = ['reconnecting', 'offline'].includes(data.state);
  const tone = protectedState ? 'positive' : blocked ? 'waiting' : 'unknown';
  const name = protectedState ? 'shield' : blocked ? 'shieldLocked' : 'shieldUnknown';
  return `<span class="health-illustration ${tone}" aria-hidden="true">${icon(name)}</span>`;
}

function signalIllustration(signal) {
  const name = signal == null || signal === 0 ? 'signalZero' : signal <= 25 ? 'signalLow' : signal <= 50 ? 'signalMedium' : signal <= 75 ? 'signalHigh' : 'signal';
  return `<span class="signal-bars${signal == null ? ' unknown' : signal < 30 ? ' weak' : ''}">${icon(name)}</span>`;
}

function protectionOverview(data) {
  const blocked = ['reconnecting', 'offline'].includes(data.state);
  const status = data.state === 'protected' ? healthTag('Aktywna', 'positive') : blocked ? healthTag('Ruch zablokowany', 'waiting') : healthTag('Niepotwierdzona');
  const torState = {
    ready: healthTag('Gotowy', 'positive'), connecting: healthTag(`Łączenie${data.tor.bootstrapPercent == null ? '' : ` · ${number(data.tor.bootstrapPercent)}%`}`, 'waiting'),
    offline: healthTag('Rozłączony', 'inactive'), unknown: healthTag('Brak danych'),
  }[data.tor.status];
  const firewallState = data.tor.killSwitch === true ? healthTag('Aktywna', 'positive') : data.tor.killSwitch === false ? healthTag('Nieaktywna', 'negative') : healthTag('Brak danych');
  const dnsState = data.tor.dnsProtected === true ? healthTag('Przez Tor', 'positive') : data.tor.dnsProtected === null ? healthTag('Brak danych') : blocked ? healthTag('Ruch wstrzymany', 'waiting') : healthTag('Niechroniony', 'negative');
  return `<section id="protection-summary" class="card health-card" aria-labelledby="protection-title">
    <div class="health-heading">${protectionIllustration(data)}<div><h2 id="protection-title">Stan ochrony</h2>${status}</div></div>
    <dl class="protection-checks">
      <div><dt><span class="check-icon">${icon('route')}</span><span>Połączenie Tor</span></dt><dd id="protection-tor">${torState}</dd></div>
      <div><dt><span class="check-icon">${icon('lock')}</span><span>Blokada poza Torem</span></dt><dd id="protection-firewall">${firewallState}</dd></div>
      <div><dt><span class="check-icon">${icon('dns')}</span><span>Ochrona DNS</span></dt><dd id="protection-dns">${dnsState}</dd></div>
    </dl>
    <div class="health-footer"><span class="health-timestamp">${icon('clock')}<span>Odczyt <time id="protection-checked-at" datetime="${escape(data.collectedAt)}">${sampleTime(data.collectedAt)}</time></span></span><a id="protection-details" href="#network">Szczegóły ${icon('arrow')}</a></div>
  </section>`;
}

function connectionQuality(data) {
  const check = data.connectivity;
  const age = check?.checkedAt == null ? Infinity : Date.now() - Date.parse(check.checkedAt);
  const fresh = age >= -10000 && age <= 30000;
  const available = data.lte.connected === true && data.tor.status === 'ready';
  const tested = available && fresh && check?.torReachable != null;
  let status = healthTag('Brak pomiaru');
  if (data.lte.connected === false) status = healthTag('Brak LTE', 'negative');
  else if (data.tor.status === 'connecting') status = healthTag('Tor łączy się', 'waiting');
  else if (data.tor.status === 'offline') status = healthTag('Tor niedostępny', 'negative');
  else if (tested) status = check.torReachable ? healthTag('Internet odpowiada', 'positive') : healthTag('Brak odpowiedzi', 'negative');
  const response = tested && check.torReachable ? check.torResponseMs : null;
  const signal = data.lte.connected === true ? data.lte.signalPercent : null;
  const responseNote = data.lte.connected === false ? 'Brak połączenia LTE' : data.lte.connected == null ? 'Brak danych LTE' : !available ? 'Tor nie jest gotowy' : tested && !check.torReachable ? 'Test połączenia nieudany' : fresh && check?.torReachable === true ? 'Pomiar dostępności internetu' : 'Brak aktualnego testu';
  const signalNote = data.lte.connected === false ? 'Brak połączenia LTE' : data.lte.connected == null ? 'Brak danych LTE' : data.lte.rsrpDbm == null ? 'Brak pomiaru RSRP' : `RSRP ${measurement(data.lte.rsrpDbm, 'dBm')}`;
  const qualityTone = tested ? check.torReachable ? 'positive' : 'negative' : 'unknown';
  return `<section id="connection-quality" class="card health-card" aria-labelledby="quality-title">
    <div class="health-heading"><span class="health-illustration connection-illustration ${qualityTone}" aria-hidden="true">${icon('globe')}</span><div><h2 id="quality-title">Jakość połączenia</h2><span id="quality-state">${status}</span></div></div>
    <dl class="quality-metrics">
      <div><dt><span class="quality-symbol response-symbol">${icon('timer')}</span>Odpowiedź przez Tor</dt><dd id="tor-response">${units(response, 'ms')}</dd><dd class="quality-note">${responseNote}</dd></div>
      <div><dt><span class="quality-symbol">${signalIllustration(signal)}</span>Sygnał LTE</dt><dd id="lte-signal">${units(signal, '%')}</dd><dd class="quality-note">${signalNote}</dd></div>
    </dl>
    <div class="quality-bottom"><span>${icon('signal')}${text(data.lte.operator)} · ${text(data.lte.technology)}</span><span>${icon('disconnect')}Zerwania LTE · 1 h <strong id="lte-disconnects">${number(check?.lteDisconnectsLastHour)}</strong></span></div>
    <div class="health-footer"><span class="health-timestamp">${icon('clock')}<span id="quality-checked-at">${tested ? `Test ${sampleTime(check.checkedAt)}` : 'Oczekiwanie na test'}</span></span><a id="quality-details" href="#network">Szczegóły ${icon('arrow')}</a></div>
  </section>`;
}

function lte(data) {
  return `<section class="card"><div class="card-heading"><h2>Łącze komórkowe</h2>${statusTag(data.lte.connected, 'Połączono', 'Rozłączono')}</div>${definitions([
    ['Operator', text(data.lte.operator)], ['Technologia', text(data.lte.technology)],
    ['Sygnał', measurement(data.lte.signalPercent, '%')], ['Opóźnienie', measurement(data.lte.latencyMs, 'ms')],
  ])}<details id="lte-details" class="disclosure"><summary>Parametry modemu</summary>${definitions([
    ['Modem', text(data.lte.model)], ['Pasmo', text(data.lte.band)], ['RSRP', measurement(data.lte.rsrpDbm, 'dBm')],
    ['RSRQ', measurement(data.lte.rsrqDb, 'dB')], ['SINR', measurement(data.lte.sinrDb, 'dB')], ['Interfejs', text(data.lte.interface)],
  ])}</details></section>`;
}

function clients(data) {
  return `<section class="card clients-card" aria-labelledby="clients-heading"><div class="card-heading"><h2 id="clients-heading">Urządzenia w sieci <span class="count-badge">${data.clients.length}</span></h2><span class="small muted">Sieć lokalna</span></div><div class="client-list">${data.clients.length ? data.clients.map(client => `<div class="client-row"><span class="client-icon">${icon('phone')}</span><div class="client-name"><strong>${text(client.name)}</strong><span>${text(client.connection)}</span></div><span class="client-address mono">${text(client.address)}</span>${statusTag(client.active, 'Online', 'Offline')}</div>`).join('') : '<p class="empty-state">Brak podłączonych urządzeń.</p>'}</div></section>`;
}

function dnsStatistics(data) {
  return `<div class="metrics-grid">${metric({ label: 'Wszystkie zapytania', value: number(data.dns.total), detail: periods[state.period], name: 'globe' })}${metric({ label: 'Zablokowane DNS', value: number(data.dns.blocked), detail: `${measurement(ratio(data.dns.blocked, data.dns.total), '%', 1)} zapytań`, name: 'shield', tone: 'purple' })}${metric({ label: 'Domeny na liście', value: number(data.dns.ruleCount), detail: statusTag(data.dns.enabled, 'Filtr włączony', 'Filtr wyłączony'), name: 'lock', tone: 'teal' })}</div>`;
}

function dnsTop(data) {
  return `<section class="card" aria-labelledby="blocked-heading"><div class="card-heading"><h2 id="blocked-heading">Najczęściej blokowane</h2><span class="small muted">${periods[state.period]}</span></div><div class="blocked-list">${data.dns.topBlocked.length ? data.dns.topBlocked.map(row => `<div class="blocked-row"><div><strong>${text(row.domain)}</strong><span>${text(row.category)}</span></div><span class="blocked-count">${number(row.count)}</span></div>`).join('') : '<p class="empty-state">Brak zablokowanych domen.</p>'}</div></section>`;
}

function overview(data) {
  return `<section class="activity-section" aria-labelledby="activity-heading">
      ${periodControl()}
      <div class="activity-panel">
        <div class="metrics-grid">
          ${metric({ label: 'Pobieranie', value: units(data.traffic.downloadMbps, 'Mb/s', 1), detail: 'Teraz', name: 'down', id: 'download-speed' })}
          ${metric({ label: 'Wysyłanie', value: units(data.traffic.uploadMbps, 'Mb/s', 1), detail: 'Teraz', name: 'up', tone: 'purple' })}
          ${metric({ label: 'Zablokowane DNS', value: number(data.dns.blocked), detail: `${measurement(ratio(data.dns.blocked, data.dns.total), '%', 1)} zapytań · ${state.period === '1h' ? '1 godz.' : state.period === '6h' ? '6 godz.' : '24 godz.'}`, name: 'shield', tone: 'teal' })}
        </div>
        ${traffic(data)}
      </div>
    </section>${clients(data)}`;
}

function network(data) {
  return `<div class="two-column">${protection(data)}${lte(data)}<section class="card"><div class="card-heading"><h2>Ochrona ruchu</h2><span class="section-icon purple">${icon('shield')}</span></div>${definitions([
    ['Połączenie Tor', measurement(data.tor.bootstrapPercent, '%')], ['Mosty', flag(data.tor.bridge, 'Włączone', 'Wyłączone')],
    ['DNS przez Tor', statusTag(data.tor.dnsProtected)], ['Blokada IPv6', statusTag(data.tor.ipv6Blocked)], ['Blokada UDP / QUIC', statusTag(data.tor.udpBlocked)],
  ])}<p class="card-note">Tor nie ukrywa tożsamości podanej przy logowaniu.</p></section><section class="card"><div class="card-heading"><h2>Interfejsy lokalne</h2><span class="section-icon blue">${icon('globe')}</span></div>${data.interfaces.length ? data.interfaces.map(net => `<div class="interface-row"><strong>${text(net.name)}</strong><span class="muted small">${text(net.role)}</span><span class="mono">${text(net.address)}</span></div>`).join('') : '<p class="empty-state">Brak interfejsów.</p>'}</section></div>${clients(data)}`;
}

function dns(data) {
  return `${periodControl('Statystyki DNS')}${dnsStatistics(data)}${dnsTop(data)}<section class="card queries-card" aria-labelledby="queries-heading"><div class="card-heading"><h2 id="queries-heading">Ostatnie zapytania</h2><span id="query-count" class="small muted" role="status"></span></div><form id="query-filters" class="query-filters"><label class="search-field">${icon('search')}<span class="sr-only">Szukaj domeny</span><input id="domain-search" name="domain" type="search" placeholder="Szukaj domeny…" value="${escape(state.search)}" autocomplete="off"></label><label><span class="sr-only">Status zapytania</span><select id="dns-filter">${[['all', 'Wszystkie zapytania'], ['blocked', 'Zablokowane'], ['allowed', 'Dozwolone']].map(([value, label]) => `<option value="${value}"${state.dnsFilter === value ? ' selected' : ''}>${label}</option>`).join('')}</select></label><button type="submit" class="button secondary">Szukaj</button></form><div id="queries-table" class="table-scroll" tabindex="0" role="region" aria-label="Ostatnie zapytania DNS"><table><caption class="sr-only">${source.kind === 'mock' ? 'Przykładowe zapytania DNS' : 'Zapytania z urządzenia'}</caption><thead><tr><th scope="col">Czas</th><th scope="col">Domena</th><th scope="col">Urządzenie</th><th scope="col">Kategoria</th><th scope="col">Status</th></tr></thead><tbody id="query-rows"></tbody></table></div><details id="dns-info" class="disclosure"><summary>Co oznaczają te dane?</summary><p class="card-note">Licznik pokazuje zablokowane zapytania DNS. Nie oznacza liczby udaremnionych prób śledzenia. Filtr domen nie rozpoznaje całej zaszyfrowanej telemetrii.</p></details></section>`;
}

function renderQueries() {
  const rows = $('#query-rows');
  if (!rows || !state.snapshot) return;
  const filtered = state.snapshot.dns.queries.filter(query =>
    (state.dnsFilter === 'all' || query.status === state.dnsFilter) && query.domain.toLowerCase().includes(state.search.toLowerCase()),
  );
  rows.innerHTML = filtered.length ? filtered.map(query => `<tr><td class="muted">${time(query.at)}</td><td class="domain-cell">${escape(query.domain)}</td><td>${text(query.client)}</td><td class="muted">${text(query.category)}</td><td><span class="query-status ${query.status}">${query.status === 'blocked' ? 'Zablokowano' : 'Dozwolono'}</span></td></tr>`).join('') : '<tr><td colspan="5" class="empty-state">Brak zapytań pasujących do filtrów.</td></tr>';
  $('#query-count').textContent = `${filtered.length} z ${state.snapshot.dns.queries.length}`;
}

function system(data) {
  const sys = data.system;
  const uptime = sys.uptimeSeconds == null ? 'Brak danych' : `${Math.floor(sys.uptimeSeconds / 3600)} h ${Math.floor(sys.uptimeSeconds % 3600 / 60)} min`;
  const serviceStates = { active: 'Działa', waiting: 'Łączenie', offline: 'Nie działa', unknown: 'Brak danych' };
  return `<div class="metrics-grid">${metric({ label: 'Procesor', value: units(sys.cpuPercent, '%'), detail: text(sys.model), name: 'cpu' })}${metric({ label: 'Pamięć RAM', value: units(ratio(sys.memoryUsedBytes, sys.memoryTotalBytes), '%', 1), detail: `${bytes(sys.memoryUsedBytes)} z ${bytes(sys.memoryTotalBytes)}`, name: 'memory', tone: 'purple' })}${metric({ label: 'Temperatura', value: units(sys.temperatureC, '°C', 1), detail: 'Procesor', name: 'temperature', tone: 'teal' })}</div><div class="two-column"><section class="card"><div class="card-heading"><h2>${text(sys.name)}</h2><span class="section-icon blue">${icon('cpu')}</span></div>${definitions([
    ['Model', text(sys.model)], ['Host', `<span class="mono">${text(sys.hostname)}</span>`], ['Czas działania', uptime],
    ['Nośnik', `${bytes(sys.diskUsedBytes)} / ${bytes(sys.diskTotalBytes)}`], ['Bateria / UPS', measurement(sys.batteryPercent, '%')], ['Wersja panelu', text(sys.version)],
  ])}</section><section class="card"><div class="card-heading"><h2>Usługi</h2><span class="small muted">Stan systemu</span></div><div class="services-list">${sys.services.length ? sys.services.map(service => `<div class="service-row"><div><strong>${text(service.name)}</strong><span>${text(service.detail)}</span></div><span class="status-tag ${service.status === 'active' ? 'positive' : service.status === 'waiting' ? 'waiting' : 'inactive'}"><span class="status-dot"></span>${serviceStates[service.status] || 'Brak danych'}</span></div>`).join('') : '<p class="empty-state">Brak usług.</p>'}</div></section></div><div class="source-note">${icon('globe')}<p>${source.kind === 'mock' ? 'Panel nie zmienia konfiguracji routera.' : '<strong>Raspberry Pi.</strong> Odczyty z urządzenia.'} Aktualizacja co ${dashboardConfig.pollIntervalMs / 1000} s.</p></div>`;
}

function render() {
  const previousChart = $('.traffic-chart');
  const previousEnd = previousChart?.dataset.mode === 'live' ? Number(previousChart.dataset.end) : null;
  const focusedId = document.activeElement?.id;
  const focusedLink = $('#content').contains(document.activeElement) ? document.activeElement?.getAttribute('href') : null;
  const selection = focusedId === 'domain-search' ? [document.activeElement.selectionStart, document.activeElement.selectionEnd] : null;
  const openDetails = [...document.querySelectorAll('#content details[open]')].map(element => element.id);
  const focusedSummary = document.activeElement?.matches('summary') ? document.activeElement.parentElement.id : null;
  const scrollPositions = [...document.querySelectorAll('#content .table-scroll')].map(element => [element.scrollLeft, element.scrollTop]);
  const [title, description] = pages[state.page];
  $('#page-title').textContent = title;
  $('#page-description').textContent = description;
  $('#page-kicker').textContent = state.page === 'overview' ? 'SafeWall One' : ({ network: 'Połączenie', dns: 'Filtr DNS', system: 'Urządzenie' })[state.page];
  $('#hero-state').innerHTML = '';
  document.body.dataset.page = state.page;
  document.title = `SafeWall — ${state.page === 'overview' ? 'Przegląd' : $('#page-kicker').textContent}`;
  document.querySelectorAll('[data-page]').forEach(link => {
    if (link.dataset.page === state.page) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
  const errorEl = $('#error-notice');
  errorEl.hidden = !state.error;
  const health = $('#overview-health');
  health.hidden = state.page !== 'overview' || !state.snapshot || !!state.error;
  health.innerHTML = '';
  if (state.error) {
    $('#page-title').textContent = 'Czekamy na urządzenie.';
    $('#page-description').textContent = 'Nie można potwierdzić stanu połączenia.';
    errorEl.innerHTML = `${icon('signal')}<h2>Brak aktualnych danych</h2><p>${escape(state.error)}</p><button type="button" class="button" data-action="retry">Spróbuj ponownie ${icon('arrow')}</button>`;
    $('#content').innerHTML = '';
    $('#updated-at').textContent = 'Odczyty niedostępne';
    return;
  }
  if (!state.snapshot) return;
  if (state.page === 'overview') {
    const status = statusInfo(state.snapshot);
    health.innerHTML = `<div class="health-grid">${protectionOverview(state.snapshot)}${connectionQuality(state.snapshot)}</div>`;
    $('#page-title').innerHTML = `<span id="connection-state">${status.title}</span>`;
    $('#page-description').textContent = status.description;
    $('#hero-state').innerHTML = `<a id="connection-link" class="connection-pill ${status.tone}" href="#network">${icon('shield')}Szczegóły ochrony ${icon('arrow')}</a>`;
  }

  $('#content').innerHTML = ({ overview, network, dns, system })[state.page](state.snapshot);
  const chart = $('.traffic-chart');
  const advance = chart && previousEnd != null ? Number(chart.dataset.end) - previousEnd : 0;
  if (chart?.dataset.mode === 'live' && advance > 0 && advance <= 15000 && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    chart.querySelector('.chart-series')?.animate([
      { transform: `translateX(${advance / 300000 * 640}px)` }, { transform: 'translateX(0px)' },
    ], { duration: 450, easing: 'ease-out' });
  }
  $('#updated-at').textContent = `Odczyt ${new Date(state.snapshot.collectedAt).toLocaleTimeString('pl-PL')}`;
  if (state.page === 'dns') renderQueries();
  document.querySelectorAll('#content .table-scroll').forEach((element, i) => {
    if (scrollPositions[i]) [element.scrollLeft, element.scrollTop] = scrollPositions[i];
  });
  for (const id of openDetails) {
    const detail = document.getElementById(id);
    if (detail) detail.open = true;
  }
  if (focusedId && document.getElementById(focusedId)) {
    const element = document.getElementById(focusedId);
    element.focus({ preventScroll: true });
    if (selection) element.setSelectionRange(...selection);
  } else if (focusedSummary) {
    document.getElementById(focusedSummary)?.querySelector('summary')?.focus({ preventScroll: true });
  } else if (focusedLink) {
    [...document.querySelectorAll('#content a')].find(link => link.getAttribute('href') === focusedLink)?.focus({ preventScroll: true });
  }
}

async function refresh(announce = false) {
  const id = ++requestId;
  controller?.abort();
  controller = new AbortController();
  state.busy = true;
  $('#refresh').disabled = true;
  $('#content').setAttribute('aria-busy', 'true');
  $('#overview-health').setAttribute('aria-busy', 'true');
  try {
    const data = await source.getSnapshot({ period: state.period, scenario: state.scenario, signal: controller.signal });
    if (id !== requestId) return;
    state.snapshot = data;
    rememberTraffic(data);
    state.error = null;
    render();
    if (announce) $('#announcer').textContent = `Odświeżono dane. ${statusInfo(data).title}.`;
  } catch (error) {
    if (id !== requestId || error.name === 'AbortError') return;
    state.error = error.name === 'TimeoutError' ? 'Urządzenie nie odpowiedziało w ciągu 8 sekund.' : error.message || 'Nie udało się odczytać danych.';
    state.snapshot = null;
    state.recentTraffic = [];
    render();
  } finally {
    if (id === requestId) {
      state.busy = false;
      $('#refresh').disabled = false;
      $('#content').setAttribute('aria-busy', 'false');
      $('#overview-health').setAttribute('aria-busy', 'false');
    }
  }
}

function navigate() {
  const requested = window.location.hash.slice(1) || 'overview';
  state.page = Object.hasOwn(pages, requested) ? requested : 'overview';
  render();
  window.scrollTo({ top: 0, behavior: 'instant' });
}

// Account for the real header height, including wrapping and browser zoom.
const header = $('.site-header');
const sizeIntro = () => document.documentElement.style.setProperty('--site-header-height', `${header.getBoundingClientRect().height}px`);
new ResizeObserver(sizeIntro).observe(header);
sizeIntro();

window.addEventListener('hashchange', navigate);
$('#refresh').addEventListener('click', () => refresh(true));
$('#scenario').addEventListener('change', event => { state.scenario = event.target.value; refresh(true); });
document.addEventListener('change', event => {
  if (event.target.id === 'period') { state.period = event.target.value; state.chartMode = 'history'; refresh(true); }
  if (event.target.id === 'traffic-view') { state.chartMode = event.target.value; render(); }
  if (event.target.id === 'dns-filter') { state.dnsFilter = event.target.value; renderQueries(); }
});
document.addEventListener('click', event => {
  if (event.target.closest('[data-action="retry"]')) refresh(true);
});
document.addEventListener('input', event => {
  if (event.target.id === 'domain-search') { state.search = event.target.value; renderQueries(); }
});
document.addEventListener('submit', event => {
  if (event.target.id === 'query-filters') { event.preventDefault(); renderQueries(); }
});
document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
if (source.kind === 'api') {
  $('#demo-notice').hidden = true;
  $('#source-name').textContent = 'Raspberry Pi';
  $('#footer-mode').textContent = `Źródło: Raspberry Pi · odświeżanie co ${dashboardConfig.pollIntervalMs / 1000} s`;
}
navigate();
refresh();
setInterval(() => { if (!document.hidden && !state.busy) refresh(); }, dashboardConfig.pollIntervalMs);
