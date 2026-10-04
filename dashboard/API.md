# Odczyty Raspberry Pi — umowa API v1

Stan: adapter przeglądarki i walidator istnieją; kolektor na Raspberry Pi **nie jest zaimplementowany**. API developerskie zwraca `503 DATA_SOURCE_NOT_CONFIGURED`. Zmiana źródła nie może uruchamiać ani konfigurować ochrony sieci.

## Żądanie

`GET /api/v1/dashboard?period=1h|6h|24h`, na tym samym origin co panel. Nagłówek `Accept: application/json`, brak cache. Odczyt co 5 sekund, timeout 8 sekund, anulowanie poprzedniego żądania przy zmianie okresu. Panel API nie przyjmuje danych starszych niż 30 sekund ani dat wyprzedzających jego zegar o ponad 10 sekund.

Odpowiedź `200`: pełna migawka o strukturze poniżej. `503`: kolektor niedostępny lub brak krytycznych danych. `401/403`: brak dostępu po wdrożeniu uwierzytelnienia. Nigdy nie zwracać danych demo jako `source: live`. Każdy błąd usuwa widoczne odczyty i status ochrony, zamiast utrzymywać poprzedni stan potwierdzający połączenie.

## Struktura

Kanoniczny wykonywalny przykład: wynik `new MockDataSource().getSnapshot()` w `dist/data.js`. Walidacja: `dist/contract.js`. Kolektor produkuje te same pola z `source: "live"`.

| Sekcja | Pola / jednostki |
| --- | --- |
| Główne | `schemaVersion: 1`, `source: "live"`, `collectedAt` ISO 8601 UTC, `period`, `state` |
| `traffic` | `downloadMbps`, `uploadMbps` (Mb/s), `downloadBytes`, `uploadBytes` (bajty w wybranym okresie), `history: [{at, download, upload}]` (Mb/s); opcjonalnie `recentHistory` w tym samym formacie: ostatnie 5 minut, próbki co 5 s, niezależnie od `period` |
| `lte` | `connected`, `operator`, `technology`, `model`, `band`, `rsrpDbm`, `rsrqDb`, `sinrDb`, `signalPercent`, `latencyMs`, `interface` |
| `tor` | `status`, `bootstrapPercent`, `exitCountry`, `exitIp`, `bridge`, `killSwitch`, `dnsProtected`, `ipv6Blocked`, `udpBlocked` |
| `connectivity` (opcjonalna) | `torReachable` boolean/null, `torResponseMs` ms/null, `checkedAt` ISO 8601 UTC/null, `lteDisconnectsLastHour` nieujemna liczba całkowita/null |
| `dns` | `total`, `blocked` (liczniki w okresie), `ruleCount`, `enabled`, `topBlocked: [{domain,category,count}]`, `queries: [{id,at,domain,category,status,client,responseMs}]` |
| `clients` | `[{id,name,address,connection,active}]` — lista klientów LAN |
| `interfaces` | `[{name,role,address}]` — rzeczywiste interfejsy LAN/USB |
| `system` | `name`, `model`, `hostname`, `version`, `cpuPercent`, `memoryUsedBytes`, `memoryTotalBytes`, `temperatureC`, `uptimeSeconds`, `diskUsedBytes`, `diskTotalBytes`, `batteryPercent`, `services: [{name,detail,status}]` |

Liczby niedostępne: `null`, nigdy sztuczne `0`. Stany logiczne niedostępne: `null`. Teksty niedostępne: `null`, z wyjątkiem domeny zapytania i wartości wyliczeniowych. Puste listy oznaczają znany brak rekordów. Gdy nie uda się odczytać krytycznej listy klientów lub sekcji ochrony, zwrócić 503 lub potwierdzony `state: unknown`; nie udawać pustego pomiaru. Każda próbka historii musi mieć datę; `null` oznacza przerwę w linii.

Widok „Na żywo · 5 min” korzysta z `recentHistory`. Bez tego pola zbiera faktyczne odczyty z kolejnych odpowiedzi (`collectedAt`, `downloadMbps`, `uploadMbps`) i dostępne próbki historii z tego okna. Nie uzupełnia braków mockami; odstępy dłuższe niż 7,5 s przerywają linię. Zachowuj oryginalne daty starszych próbek. Oś czasu przesuwa się dopiero po otrzymaniu nowszego pomiaru. Błąd API czyści także bufor widoku bieżącego.

Sekcja `connectivity` może nie istnieć lub być `null`; panel pokaże brak pomiaru dostępności. Jeśli istnieje, musi zawierać wszystkie cztery pola, z `null` dla nieznanych wartości. `torReachable` opisuje wynik ostatniego testu HTTPS wykonanego przez Tor do ustalonego celu, a `torResponseMs` czas od rozpoczęcia tego żądania do pierwszego bajtu odpowiedzi. Nie jest to ping LTE ani pomiar wszystkich obwodów. Kolektor musi określić cel, timeout i kryterium udanego testu. Panel nie uruchamia takich żądań z przeglądarki.

Wynik `true` lub `false` wymaga `checkedAt`; liczbowy czas odpowiedzi wymaga wyniku `true`. Nieudany test: `torReachable: false`, `torResponseMs: null`, czas wykonanego testu w `checkedAt`. Test niewykonany: wszystkie trzy pola `null`. Wynik starszy niż 30 s lub wyprzedzający zegar panelu o ponad 10 s nie potwierdza bieżącej dostępności. Dodatkowo wymagane są połączone LTE i gotowy Tor. Brak odpowiedzi nie zmienia samodzielnie stanu ochrony — zapora może nadal działać prawidłowo.

`lteDisconnectsLastHour` to liczba faktycznych przejść LTE z połączonego do rozłączonego w ruchomym oknie ostatnich 60 minut, niezależnym od wybranego okresu statystyk. Kolejne odczyty tej samej awarii ani przebudowa połączenia Tor nie zwiększają licznika. Jeśli kolektor nie ma pełnej historii tego okna (np. po restarcie), zwraca `null`, nie zero. Czas `checkedAt` dotyczy testu przez Tor; licznik zerwań jest aktualny na `collectedAt`.

Wyliczenia:

- `state`: `protected`, `reconnecting`, `offline`, `unknown`.
- `tor.status`: `ready`, `connecting`, `offline`, `unknown`.
- `dns.queries[].status`: `allowed`, `blocked`.
- `system.services[].status`: `active`, `waiting`, `offline`, `unknown`.

`protected` wymaga jednocześnie LTE, gotowego Tora oraz potwierdzonych `killSwitch`, `dnsProtected`, `ipv6Blocked` i `udpBlocked`. Uruchomiony proces Tor sam nie potwierdza ochrony. Wartości muszą wynikać z pomiarów i inspekcji aktywnych reguł, nie jedynie ustawień konfiguracyjnych. `reconnecting` i `offline` zakładają potwierdzoną blokadę ruchu; jeśli brak takiego dowodu, użyć `unknown`.

Nie wolno przemianować obecnej odpowiedzi mock na live. Backend ma osobno ustalić stan urządzenia i czas pomiaru. `exitIp` i `exitCountry` zwrócić jako null, dopóki nie ma sprawdzonego, prywatnościowego sposobu ich ustalenia; frontend niczego nie geolokalizuje.

Pojedyncze wyjście Tor nie reprezentuje całego ruchu routera. Wiele strumieni TCP może współdzielić obwód, a różne obwody mogą działać jednocześnie, zgodnie z [zasadami izolacji strumieni Tor](https://spec.torproject.org/path-spec/stream-isolation.html). Przed podłączeniem pól `exitIp` / `exitCountry` do kolektora należy określić, jakiego pomiaru dotyczą; bez takiego kontekstu pozostają `null`. Docelowa diagnostyka wymaga modelu wielu obwodów i przypisanych do nich strumieni.

## Plan kolektora

| Odczyt | Planowane źródło na Pi |
| --- | --- |
| LTE | ModemManager / NetworkManager, preferowane strukturalne API; bez SIM PIN, IMSI, ICCID i pełnych identyfikatorów modemu |
| Jakość połączenia | Osobny test HTTPS przez Tor z czasem i wynikiem; zdarzenia połączenia LTE do licznika zerwań. Częstotliwość i cel testu do ustalenia przy implementacji kolektora |
| Transfer | Różnice liczników właściwego interfejsu WAN podzielone przez rzeczywisty odstęp; bajty × 8 / sekundy / 1 000 000; reset interfejsu jako przerwa, nie ujemny transfer |
| Tor i zapora | Lokalny Tor ControlPort oraz inspekcja aktywnych reguł nftables; odrębne testy wycieków przed uznaniem reguł za poprawne |
| DNS / klienci | Faktycznie wdrożony filtr DNS i dzierżawy DHCP; samo dnsmasq nie dostarcza automatycznie statystyk blokowania |
| System | `/proc`, `/sys`, dane systemd i czujniki Pi; model UPS i źródło pomiaru baterii pozostają nieustalone |

Historię 1/6/24 h trzeba agregować lokalnie; nie wyprowadzać dobowych sum z chwilowej prędkości. Kolektor oznacza braki po restarcie, nie fabrykuje starszych punktów. Polityka retencji i widoczność domen do ustalenia przed użyciem prawdziwego ruchu; preferowane agregaty bez trwałej historii pełnych zapytań.

## Wdrożenie lokalne

Serwować `dist/` i API pod jednym origin. Docelowo `http://safewall.local` przez lokalny reverse proxy / serwer na Pi, publikacja nazwy mDNS bez nadpisywania obecnych nazw i usług. Dodać uwierzytelnienie oraz ograniczenie do LAN i administracyjnego USB. Node z tego katalogu jest wyłącznie serwerem developerskim na loopback. Panel nie powinien działać jako root; kolektor ma otrzymać tylko niezbędny odczyt.

Przed przełączeniem na API: sprawdzić zgodność wskazań z niezależnymi odczytami Pi, awarię LTE/Tora, utratę kolektora, stary pomiar, brak czujnika i restart liczników. DNS/Avahi, serwer i zapora muszą zostać wdrożone jako osobny, zweryfikowany etap.
