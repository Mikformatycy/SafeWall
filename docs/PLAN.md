# SafeWall — wizja i zakres dalszego rozwoju

Stan: koncepcja uzgodniona z użytkownikiem 3 października 2026. Poniższe funkcje są planowane; nie opisują wdrożonej konfiguracji. Dokument dla komisji: [draft](PROJEKT.md), [PDF](SafeWall-draft.pdf).

## Cel i scenariusz
Telefon korzysta z internetu wyłącznie po kablu USB-C–Ethernet. Użytkownik włącza tryb samolotowy oraz wyłącza Wi-Fi i Bluetooth w ustawieniach. Własny modem routera zapewnia LTE. Osobny USB-C Pi–Mac służy do SSH, nie do dostarczania internetu klientowi. Docelowo zestaw ma własny akumulator.

Celem jest ograniczenie lokalnego śledzenia radiowego telefonu, filtrowanie wybranych domen telemetrycznych i chroniona ścieżka przez Tor. Nie deklarujemy niewykrywalności, anonimowości wobec operatora ani wyłączenia wszelkich emisji bez pomiarów. Modem pozostaje nadajnikiem identyfikowanym przez SIM i urządzenie; operator może go lokalizować. Adres MAC Ethernet pozostaje w lokalnym segmencie.

## Etapy i warunki odbioru
| Etap | Zakres | Dowód działania |
|---|---|---|
| 1. Łącze | Integracja modemu LTE z routerem | Testy połączenia i powtarzalny pomiar szybkości |
| 2. Tor | TCP i DNS, opcjonalne mosty, blokada bezpośredniego wyjścia | Wyjście Tor, brak wycieków DNS/IPv6/UDP, po zatrzymaniu Tora brak internetu |
| 3. Panel | Stan LTE/Tor, statystyki DNS, reguły, wyjątki | Zapytanie do testowej blokowanej domeny zwiększa właściwy licznik |
| 4. Komunikacja | SMS i rozmowy operatora; osobno szyfrowana komunikacja internetowa | Test SMS, toru audio i wsparcia operatora; oddzielna weryfikacja szyfrowania E2EE |
| 5. Sprzęt | PCB, bateria/UPS, CAD i dyskretna obudowa | Stabilne zasilanie pod obciążeniem, temperatura, antena, czas pracy |

## Tor i filtrowanie
Obecnie działa bezpośredni NAT do modemu, a nie Tor. Planowana zmiana wymaga odrębnego wdrożenia i testów. Tryb chroniony nie może automatycznie wracać do bezpośredniego LTE po awarii Tora. Panel lokalny i administracja USB powinny pozostać dostępne. Zwykły UDP/QUIC nie ma być przepuszczany poza Tor; część aplikacji może przestać działać. Ruch DNS z LAN ma przechodzić przez lokalny filtr i dalej przez chronioną ścieżkę. IPv6 blokujemy do czasu zaprojektowania i sprawdzenia obsługi.

Mosty (bridges), np. z obfs4, są opcją na blokowanie dostępu do Tora, nie gwarancją anonimowości ani przyspieszeniem. Zapora nie zastępuje zabezpieczeń Tor Browser; konta, odciski przeglądarki i aplikacje nadal mogą identyfikować użytkownika.

## Panel i dane
Panel dostępny z prywatnego LAN, zabezpieczony uwierzytelnieniem, bez wystawiania na WAN. Widoki: połączenie LTE i parametry radia; stan Tora i mostów; liczba zapytań DNS i blokad; lista reguł/wyjątków; SMS i ewentualnie rozmowy. Licznik blokad oznacza zablokowane zapytania, nie liczbę udaremnionych prób śledzenia. Filtr nie rozpoznaje całej zaszyfrowanej telemetrii; szyfrowany DNS aplikacji może omijać filtrowanie domen.

Preferowane są lokalne sumaryczne statystyki, krótka lub wyłączona historia domen, przycisk kasowania danych. Panel nie pokazuje PIN-u ani sekretów. Projekt panelu i jego implementacja są osobnymi zadaniami; obecnie panel nie istnieje.

## SMS i rozmowy
Zwykłe SMS-y i rozmowy komórkowe nie są przenoszone przez Tor i nie stają się E2EE dzięki panelowi. Ich obsługa wymaga sprawdzenia komend modemu, wsparcia VoLTE/operatora oraz fizycznego lub USB toru audio. Szyfrowana komunikacja ma stanowić oddzielną funkcję opartą na sprawdzonym protokole i zgodnym kliencie po obu stronach. Nie projektujemy własnej kryptografii. Rozmowy internetowe często potrzebują UDP; zgodność, opóźnienia i ewentualne ograniczenia w trybie Tor są otwartym zadaniem.

## Miniaturyzacja i forma
Użytkownik chce kompaktowego urządzenia o dyskretnym wyglądzie zwykłego akcesorium (np. powerbanku). Plan: PCB po sprawdzeniu architektury, obudowa CAD, mocowanie anteny i złączy, odciążenie kabli, chłodzenie i bezpieczne zasilanie. Obudowa nie oznacza maskowania emisji LTE. Model Waveshare UPS pozostaje nieustalony, zasilanie bateryjne nie jest uruchomione.

## Źródła
- Apple: https://support.apple.com/en-gb/108785 — tryb samolotowy może pozostawić Bluetooth aktywny.
- Tor Project: https://support.torproject.org/tor-browser/security/using-tb-safely/ — granice ochrony i HTTPS.
- Tor Project: https://support.torproject.org/relays/legal-and-abuse/ddos/ — brak transportu zwykłego UDP.
- Tor Project: https://support.torproject.org/tor-browser/circumvention/unblocking-tor/ — mosty i transporty maskujące.
