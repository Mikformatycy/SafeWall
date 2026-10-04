/**
 * API v1 uses SI units: Mbps, bytes, Celsius, seconds, ISO-8601 UTC timestamps.
 * null means unavailable; a measurement of 0 is a real zero.
 * See API.md for the Pi collector integration and source-of-truth requirements.
 */
export class DataSourceError extends Error {}

export function validateSnapshot(data, expectedSource) {
  const bad = message => { throw new DataSourceError(`Nieprawidłowe dane panelu: ${message}.`); };
  const numeric = (value, name, nullable = false) => {
    if (nullable && value === null) return;
    if (!Number.isFinite(value)) bad(name);
  };
  if (!data || data.schemaVersion !== 1) bad('wersja API');
  if (data.source !== expectedSource) bad('źródło danych');
  if (!Number.isFinite(Date.parse(data.collectedAt))) bad('czas pomiaru');
  if (!['protected', 'reconnecting', 'offline', 'unknown'].includes(data.state)) bad('stan połączenia');
  if (!['1h', '6h', '24h'].includes(data.period)) bad('okres');
  if (!data.traffic || !data.dns || !data.lte || !data.tor || !data.system || !Array.isArray(data.clients) || !Array.isArray(data.interfaces)) bad('brak sekcji');
  for (const field of ['downloadMbps', 'uploadMbps', 'downloadBytes', 'uploadBytes']) numeric(data.traffic[field], field, true);
  for (const field of ['total', 'blocked']) numeric(data.dns[field], field, true);
  if (!Array.isArray(data.traffic.history) || !Array.isArray(data.dns.queries) || !Array.isArray(data.dns.topBlocked)) bad('brak historii');
  if (data.traffic.recentHistory !== undefined && !Array.isArray(data.traffic.recentHistory)) bad('historia bieżąca');
  for (const point of [...data.traffic.history, ...(data.traffic.recentHistory || [])]) {
    if (!Number.isFinite(Date.parse(point.at))) bad('czas próbki');
    numeric(point.download, 'pobieranie próbki', true);
    numeric(point.upload, 'wysyłanie próbki', true);
    if (point.download < 0 || point.upload < 0) bad('ujemny transfer próbki');
  }
  if (!Array.isArray(data.system.services)) bad('usługi');
  const flag = (value, name) => { if (value !== null && typeof value !== 'boolean') bad(name); };
  const text = (value, name) => { if (value !== null && typeof value !== 'string') bad(name); };
  const positive = (value, name, max = Infinity) => {
    numeric(value, name, true);
    if (value !== null && (value < 0 || value > max)) bad(name);
  };
  for (const field of ['downloadMbps', 'uploadMbps', 'downloadBytes', 'uploadBytes']) positive(data.traffic[field], field);
  for (const field of ['total', 'blocked', 'ruleCount']) positive(data.dns[field], field);
  if (data.dns.total !== null && data.dns.blocked !== null && data.dns.blocked > data.dns.total) bad('licznik blokad');
  flag(data.dns.enabled, 'filtr DNS');
  flag(data.lte.connected, 'połączenie LTE');
  for (const field of ['operator', 'technology', 'model', 'band', 'interface']) text(data.lte[field], field);
  for (const field of ['rsrpDbm', 'rsrqDb', 'sinrDb']) numeric(data.lte[field], field, true);
  positive(data.lte.signalPercent, 'sygnał', 100);
  positive(data.lte.latencyMs, 'opóźnienie');
  if (data.connectivity != null) {
    const check = data.connectivity;
    flag(check.torReachable, 'dostępność przez Tor');
    positive(check.torResponseMs, 'czas odpowiedzi przez Tor');
    positive(check.lteDisconnectsLastHour, 'zerwania LTE');
    if (check.lteDisconnectsLastHour !== null && !Number.isInteger(check.lteDisconnectsLastHour)) bad('licznik zerwań LTE');
    if (check.checkedAt !== null && (typeof check.checkedAt !== 'string' || !Number.isFinite(Date.parse(check.checkedAt)))) bad('czas testu połączenia');
    if (check.torReachable !== null && check.checkedAt === null) bad('brak czasu testu połączenia');
    if (check.torResponseMs !== null && check.torReachable !== true) bad('czas odpowiedzi bez udanego testu');
  }
  if (!['ready', 'connecting', 'offline', 'unknown'].includes(data.tor.status)) bad('stan Tora');
  positive(data.tor.bootstrapPercent, 'postęp Tora', 100);
  for (const field of ['bridge', 'killSwitch', 'dnsProtected', 'ipv6Blocked', 'udpBlocked']) flag(data.tor[field], field);
  for (const field of ['exitCountry', 'exitIp']) text(data.tor[field], field);
  if (data.state === 'protected' && (data.lte.connected !== true || data.tor.status !== 'ready' || ['killSwitch', 'dnsProtected', 'ipv6Blocked', 'udpBlocked'].some(key => data.tor[key] !== true))) bad('ochrona bez potwierdzenia');
  if (['reconnecting', 'offline'].includes(data.state) && data.tor.killSwitch !== true) bad('brak potwierdzenia blokady ruchu');
  for (const field of ['name', 'model', 'hostname', 'version']) text(data.system[field], field);
  for (const field of ['cpuPercent', 'batteryPercent']) positive(data.system[field], field, 100);
  for (const field of ['memoryUsedBytes', 'memoryTotalBytes', 'diskUsedBytes', 'diskTotalBytes', 'uptimeSeconds']) positive(data.system[field], field);
  numeric(data.system.temperatureC, 'temperatura', true);
  for (const service of data.system.services) {
    text(service.name, 'nazwa usługi'); text(service.detail, 'opis usługi');
    if (!['active', 'waiting', 'offline', 'unknown'].includes(service.status)) bad('stan usługi');
  }
  for (const client of data.clients) {
    for (const field of ['id', 'name', 'address', 'connection']) text(client[field], field);
    flag(client.active, 'stan klienta');
  }
  for (const net of data.interfaces) {
    for (const field of ['name', 'role', 'address']) text(net[field], field);
  }
  for (const row of data.dns.topBlocked) {
    text(row.domain, 'domena'); text(row.category, 'kategoria'); positive(row.count, 'licznik domeny');
  }
  for (const query of data.dns.queries) {
    if (typeof query.domain !== 'string') bad('domena zapytania');
    if (!Number.isFinite(Date.parse(query.at))) bad('czas zapytania');
    if (!['allowed', 'blocked'].includes(query.status)) bad('status zapytania');
    for (const field of ['id', 'category', 'client']) text(query[field], field);
    positive(query.responseMs, 'czas odpowiedzi');
  }
  return data;
}
