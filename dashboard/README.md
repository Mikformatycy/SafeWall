# Dashboard SafeWall

Lokalny prototyp panelu, aktualizacja 4 października 2026. CAD i obudowa są opisane w oddzielnym katalogu. Dane i stany ochrony są obecnie **symulowane**. Panel nie łączy się z modemem ani Raspberry Pi i nie zmienia ich konfiguracji.

Na prośbę użytkownika wygląd został zaprojektowany na podstawie [RainbowKit](https://rainbowkit.com), obejrzanego w Playwright na komputerze i telefonie: ciemne tło, zaokrąglone elementy, systemowa typografia, niebiesko-fioletowe akcenty i krótkie opisy. Przegląd eksponuje stan ochrony i jakość połączenia; transfer oraz statystyki DNS są niżej, a szczegóły w zakładkach i rozwijanych sekcjach. Ikony SVG Lucide i style są lokalne, bez zależności od RainbowKit ani jego zasobów.

Po ponownym porównaniu z RainbowKit cały przegląd otrzymał czarne tło, mocniejsze zaokrąglone nagłówki, gradientowy przycisk. Po kolejnej korekcie ikony korzystają ze spójnego, liniowego zestawu Lucide z prostą oprawą. Ochrona i jakość połączenia są częściami jednego grafitowego panelu; drugi panel łączy statystyki z wykresem. Na telefonie sekcje układają się pionowo. Lokalne zrzuty odniesienia z Playwright są w `.artifacts/rainbowkit-*.png` (poza Gitem).

Na komputerze fragment od górnego paska do końca panelu ochrony zajmuje pierwszy viewport. Statystyki i wykres są poniżej. Wysokość uwzględnia rzeczywisty rozmiar paska; niższe okna otrzymują mniejsze odstępy. Na małych ekranach i przy powiększonym tekście sekcja może przekroczyć wysokość okna, zachowując wszystkie odczyty bez przycinania.

## Otwórz teraz

Otwórz `Podglad.html` dwuklikiem w przeglądarce. To samodzielna wersja demo: bez instalacji, serwera, CDN, zewnętrznych czcionek i internetu.

Tryb developerski wymaga Node.js 20 lub nowszego. Bez instalowania zależności:

```sh
cd dashboard
npm start
```

Następnie otwórz `http://127.0.0.1:4173`. Serwer nasłuchuje wyłącznie na localhost; zatrzymanie: Ctrl+C. Inny port: `PORT=4174 npm start`.

### Praca z automatycznym odświeżaniem

Uruchom `Uruchom.command` dwuklikiem: uruchamia serwer developerski i otwiera panel w Safari. Z Terminala: `npm run dev:safari` (z Safari) lub `npm run dev` (sam serwer).

W trybie developerskim strona sprawdza zmiany co sekundę. Zapis CSS podmienia arkusz bez przeładowania i utraty stanu. Zmiana HTML/JS odświeża stronę, zachowując adres otwartego widoku; scenariusz i filtry wracają wtedy do wartości początkowych. Nie trzeba przebudowywać plików przy każdej zmianie. Po zakończeniu zmian `npm run build` aktualizuje osobny podgląd `Podglad.html`, który nie ma live reloada. Zmiany samego `server.mjs` wymagają restartu serwera. Zwykłe `npm start` nie włącza live reloada.

`safewall.local` jest adresem docelowym na Raspberry Pi, **nie skonfigurowano go na Macu ani Pi**. Publikacja mDNS/DNS i portu 80 nastąpi przy osobnym wdrożeniu na urządzeniu. Nie zmieniano `/etc/hosts`, Avahi, zapory, DNS ani istniejącej makiety Tor Check.

## Co działa w prototypie

- Przegląd: stan ochrony (Tor, blokada poza Torem, DNS, czas odczytu) oraz jakość połączenia (czas odpowiedzi przez Tor, sygnał LTE z RSRP, liczba zerwań LTE z ostatniej godziny). Niżej bieżący transfer, blokady DNS i urządzenia. Wykres domyślnie pokazuje ostatnie 5 minut, dopisuje próbkę co 5 s i przesuwa poprzednie w lewo. Selektor wykresu przełącza na historię 1/6/24 h; zmiana ogólnego okresu statystyk otwiera tę historię. Tabela pokazuje odczyty z wybranego widoku. Braki pomiarów przerywają linię zamiast udawać zero.
- Połączenie: LTE, Tor, blokada wyjścia, interfejsy lokalne.
- Filtr DNS: statystyki, domeny, wyszukiwanie i filtrowanie zapytań.
- Urządzenie: procesor, pamięć, temperatura, usługi i źródło danych.
- Scenariusze demo: Tor połączony, słabe LTE, Tor łączy się, brak LTE. Odczyty co 5 s i natywna obsługa formularzy klawiaturą.

Przykładowe domeny `example.com/net/org` i adres wyjścia `198.51.100.24` służą wyłącznie demonstracji. Brak odczytu to `null`, wyświetlany jako kreska lub „brak danych”. Stan baterii nie jest wymyślany.

Status ochrony i dostępność internetu są niezależne. Nieudany test odpowiedzi przez Tor nie wyłącza potwierdzonej ochrony. Gotowy Tor bez aktualnego testu nie daje komunikatu „Internet odpowiada”; pomiary starsze niż 30 s są ukrywane. Obecne czasy odpowiedzi i sygnał LTE są symulowane, panel nie wykonuje testów sieciowych. Scenariusz słabego LTE zmniejsza sygnał i zwiększa czas odpowiedzi. Licznik zerwań demo zlicza przejścia do „Brak LTE” w bieżącej sesji z ostatnich 60 minut; samo ponowne łączenie Tora go nie zwiększa.

Kafelki ochrony i połączenia wykorzystują lokalne ikony Lucide. Tarcza pokazuje potwierdzoną ochronę, blokadę ruchu lub nieznany stan; wariant ikony sygnału odpowiada odczytowi LTE. Brak odczytu pozostaje opisany jako brak danych. Jedyny znacznik „Dane demo” znajduje się w nagłówku strony.

Mock transferu generuje krótkie, nieregularne piki pobierania i wysyłania z przerwami o niskim ruchu. Utrzymuje maksymalnie 24 h próbek co 5 s. Odczyty są przypisane do czasu: odświeżanie i przełączanie okresów nie losuje historii od nowa. Awaria dodaje zera od momentu jej wybrania, a ponowne połączenie zachowuje tę przerwę. Sumy bajtów wynikają z próbek w danym okresie. Ruch wykresu respektuje preferencję ograniczenia animacji.

## Pliki i dalsze zmiany

| Plik | Rola |
| --- | --- |
| `dist/index.html`, `dist/app.js` | Semantyczny HTML, widoki, wykres SVG i interakcje |
| `dist/styles.css` | Responsywny ciemny interfejs inspirowany RainbowKit |
| `dist/data.js` | Oddzielne adaptery demo oraz API Raspberry Pi |
| `dist/contract.js` | Walidacja danych i warunków pokazywania chronionego połączenia |
| `dist/config.js` | Wybór domyślnego źródła i częstotliwość odczytów |
| `server.mjs` | Lokalny serwer plików, `/health`, jawnie niedostępne API urządzenia |

Ikony interfejsu: lokalny wybór 25 SVG z [`lucide-static` 1.51.0](https://lucide.dev), bez bibliotek ładowanych z CDN i bez instalacji zależności. Geometria ikon pochodzi bez zmian z oficjalnego pakietu; aplikacja dobiera rozmiar, kolor i wariant stanu. Definicje oraz pełna licencja są w `dist/app.js`, kopia licencji i adres źródła w [licenses/lucide.txt](licenses/lucide.txt). Własny znak SafeWall pozostaje osobnym elementem marki.

Edytuj źródła w `dist/`. Po zmianach uruchom `npm run build`, aby odświeżyć samodzielny `Podglad.html`; nie edytuj go ręcznie. HTML/CSS/JS są celowo niezależne od usług chmurowych i bibliotek zewnętrznych. Te same pliki można później serwować z Pi, bez przebudowy interfejsu.

## Prawdziwe dane z Pi

Umowa API i mapowanie odczytów: [API.md](API.md). Tryb API można już sprawdzić pod `http://127.0.0.1:4173/?source=api`. Obecnie wyświetli informację o braku odczytów. Nie przełącza się wtedy na demo i nie zachowuje poprzedniego statusu ochrony.

Przed wdrożeniem: zbudować kolektor tylko do odczytu, potwierdzić jednostki i okresy, wdrożyć lokalne uwierzytelnienie oraz dostęp wyłącznie z prywatnego LAN/administracyjnego USB. Następnie ustawić `dataSource: 'api'` w `dist/config.js`. Sam interfejs nie wdraża Tora, blokady wycieku ani filtrów DNS. Obecna konfiguracja routera opisana w nadrzędnej dokumentacji nadal obowiązuje.

## Logo SafeWall

Wybrany znak to **4A**: dwukolorowy mur z trzema blankami i prostą podstawą. Wzorzec to [SVG w katalogu brand](../brand/svg/safewall-logo.svg); [podgląd i komplet eksportów](../brand/index.html) zawiera PNG od 16 do 2048 px, tła przezroczyste/białe/czarne/grafitowe, warianty monochromatyczne, ICO oraz ikony Apple i aplikacji. SVG zawiera dwie ścieżki wektorowe, bez bitmapy. Barwy zostały pobrane z zaakceptowanego PNG: `#7D67E9` i `#B39AFB`.

Nagłówek korzysta z przezroczystego SVG. Przeglądarka otrzymuje favicon SVG, ICO i PNG; Apple — nieprzezroczysty PNG 180 px. Ikona przypiętej karty Safari jest monochromatyczna. Logo marki nie zastępuje ikon Lucide oznaczających stan ochrony.

`npm run build` kopiuje eksporty z `../brand/` do `dist/` i osadza obrazy w `Podglad.html`, tak aby podgląd działał również po przeniesieniu samego pliku. Zmiany wdrożonych plików logo i faviconów są wykrywane przez live reload.

Po zmianie wektorowego wzorca eksporty odtwarza `node brand/build.mjs` uruchomione z katalogu głównego projektu. Skrypt wymaga lokalnego Playwrighta i Pythona z Pillow; opcjonalne `PLAYWRIGHT_MODULE` oraz `PYTHON` wskazują ich istniejące instalacje. Następnie uruchom `npm run build` w dashboardzie. Generowanie PDF projektu korzysta z tego samego SVG oraz bibliotek `reportlab` i `svglib`.

## Sprawdzenie

```sh
npm run check
npm run build
npm test
```

Testy obejmują umowę danych, stany awarii, brak fallbacku do demo, świeżość danych, samodzielny podgląd i obsługę żądań serwera bez otwierania portu. Opcjonalny `node tests/browser.mjs` wymaga lokalnego Playwrighta i uprawnienia do uruchomienia przeglądarki; zapisuje zrzuty do `.artifacts/`. `PLAYWRIGHT_MODULE` może wskazywać istniejący moduł `playwright/index.mjs`, `BROWSER=webkit` wybiera silnik Safari, a `DASHBOARD_URL=http://127.0.0.1:4173` sprawdza działający serwer oraz błędy API. Domyślnie testowany jest samodzielny podgląd w Chromium. Testy przeglądarkowe sprawdzają szerokości 320–1440 px, filtry, scenariusze, wykres, utrzymanie fokusu i otwartych szczegółów podczas odświeżania.

Po udostępnieniu pełnego dostępu uruchomiono serwer lokalny na `127.0.0.1:4173` i potwierdzono HTTP 200 dla strony oraz endpointów live reloada. Serwer musi pozostać uruchomiony podczas korzystania z tego adresu.
