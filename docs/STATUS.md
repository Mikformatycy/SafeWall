# Aktualny stan SafeWall

Stan dokumentacji: **4 października 2026**. Ten dokument rozstrzyga status projektu; rozdziały 01–07 są zapisem wcześniejszych testów, nie bieżącym odczytem urządzenia.

## Router i Tor

Na Raspberry Pi 4 uruchomiono administrację przez USB, prywatny Ethernet, DHCP/DNS, nftables oraz modem PiTalk EG25-G przez USB/QMI. iPhone otrzymał adres i otwierał strony przez LTE. W późniejszych testach modem miał niski transfer i timeouty na Pi oraz Macu; użytkownik zgłosił też timeouty na Windowsie. Nie mamy udokumentowanego potwierdzenia trwałego rozwiązania tego problemu.

Nowszy materiał `IMG_4626` pokazuje zmianę wyniku Tor Check po podłączeniu przewodu i odświeżeniu strony. Użytkownik potwierdził aktywnego Tora. Jest to relacja i nagranie demonstracji, a nie niezależny audyt wdrożenia. Zachowane pliki `config/nftables.conf` oraz `scripts/pi-router-wan` nadal implementują wcześniejszy bezpośredni NAT do modemu. W repo nie ma aktualnego `torrc`, kompletnej konfiguracji przekierowań ani sprawdzonej blokady wyjścia poza Tor.

Z tego powodu nie określamy Tora wyłącznie jako pomysłu, ale też nie przedstawiamy repo jako gotowego instalatora chronionej bramy. Następny etap to pozyskanie konfiguracji z urządzenia, usunięcie sekretów i testy DNS, IPv6, UDP, restartów oraz odcięcia ruchu po awarii Tora. Synchronizacja GitHuba nie zmienia konfiguracji Pi.

Makieta w [mock-check-tor/](../mock-check-tor/README.md) jest oddzielnym narzędziem prezentacyjnym. Jej zielony komunikat jest statyczny. HTTPS tej makiety potwierdza jedynie połączenie z lokalnym serwerem.

## Dashboard

Panel istnieje i działa lokalnie: przegląd ochrony i jakości połączenia, transfer, filtr DNS oraz urządzenie. Ma logo 4A, lokalne ikony Lucide, podgląd offline i automatyczne odświeżanie podczas edycji. Dane, statusy i wyniki filtrowania są symulowane; brak odczytu z API nie przełącza aplikacji na demo.

Kontrakt rzeczywistych danych opisuje [dashboard/API.md](../dashboard/API.md). Kolektor, uwierzytelnienie, wdrożenie na Pi i nazwa `safewall.local` pozostają do wykonania. Stan baterii nie jest wymyślany. „Ochrona aktywna” w scenariuszu demo nie opisuje podłączonego sprzętu.

## Konstrukcja

Powstały warianty CAD A i B, źródła skryptów, eksporty koncepcyjne i rendery. Preferowany wariant B ma obwiednię 110 × 70 × 24 mm. To geometria studium, nie zatwierdzone wymiary produktu. Płytki w wizualizacji częściowo reprezentują zarezerwowane miejsce; nie są gotowym projektem PCB.

Czas pracy 2 h jest celem. Nie zmierzono poboru energii, czasu pracy ani masy całego urządzenia. Dobór baterii, elektroniki zasilania, LTE, anten i mocowania magnetycznego wymaga dalszych prac. [Zakres CAD](../physical-design/README.md).

## Materiały projektu

Obowiązuje logo 4A i hasło „Bo za każdą historią stoi człowiek.”. Dostępne są cover 4:3, prezentacja 8 slajdów, aktualizowany draft 2 strony i źródło poziomego outro 1920 × 1080 / 60 fps / 6,2 s.

Najnowszy lokalny montaż filmu to v22: 69,917 s, 960 × 540, 24 fps. Sceny Blendera są podglądem Workbench; materiały premium v04 są osobnym etapem. Demo w v22 jest przycięte i odtwarzane 1,35×, a jego obraz przeglądarki nie był retuszowany. Te parametry pochodzą z zapisanego raportu montażu, nie z nowego testu urządzenia.

Link i QR filmu w prezentacji nadal prowadzą do roboczego `https://youtube.com/`. Nie znamy adresu opublikowanego filmu; nie przedstawiamy tego linku jako gotowej publikacji. [Materiały i ich źródła](../marketing/README.md).
