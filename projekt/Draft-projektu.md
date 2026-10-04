<img src="../brand/svg/safewall-logo.svg" width="96" alt="Logo SafeWall">

# SafeWall
## Kieszonkowa brama prywatności dla telefonu
Draft projektu • aktualizacja 4 października 2026

### Pomysł
Chcemy dać użytkownikowi internet w telefonie bez korzystania z jego Wi-Fi, Bluetooth i sieci komórkowej. Telefon łączy się przewodem z małym routerem wyposażonym we własny modem LTE. Router ma kierować ruch przez Tor, ograniczać połączenia z domenami telemetrycznymi i pokazywać w prostym panelu, co zostało zablokowane.

### Jak użytkownik z tego korzysta
Użytkownik włącza tryb samolotowy, sprawdza w ustawieniach wyłączenie Wi-Fi i Bluetooth, a następnie podłącza adapter USB-C–Ethernet. Adres sieciowy otrzymuje automatycznie. Lokalny panel pokazuje stan LTE, Tora i filtrów. W docelowym trybie chronionym awaria Tora zatrzymuje ruch do internetu zamiast przełączać go na bezpośrednie LTE.

### Schemat docelowy
Telefon → adapter USB-C–Ethernet → Raspberry Pi → modem LTE → sieć Tor → internet
Na Raspberry Pi: zapora, filtr DNS, klient Tor i lokalny panel. Opcjonalny most (bridge) ułatwia dostęp do Tora w sieciach, które go blokują. Mac służy wyłącznie do administracji przez osobne USB-C. Własne zasilanie jest planowane.

### Co już sprawdziliśmy
Prototyp opiera się na Raspberry Pi 4 i modemie PiTalk EG25-G. Sprawdzono SSH przez USB-C, DHCP, DNS i routing IPv4; iPhone otwierał strony przez Ethernet i LTE. Nowsze nagranie pokazuje pozytywny Tor Check, a użytkownik potwierdził Tora. Nie wykonano audytu całego ruchu ani testu odcięcia po awarii.

### Obecny etap
Mamy dashboard z danymi demo, koncepcję CAD oraz materiały prezentacyjne. Pliki routera w repo nadal opisują wcześniejszy NAT. Potrzebujemy aktualnej konfiguracji Pi, testów ochrony, wyjaśnienia timeoutów LTE oraz podłączenia panelu i filtra do prawdziwych danych.

---

### Co budujemy dalej
1. Integracja LTE i Tora. Kierowanie obsługiwanego ruchu TCP oraz DNS przez Tor, obsługa mostów i blokada wyjścia poza chronioną ścieżkę. Ruch nieobsługiwany, w tym zwykły UDP, ma być blokowany, nie przepuszczany bokiem.
2. Podłączenie istniejącego panelu do Pi. Rzeczywisty stan połączenia, statystyki DNS, reguły i wyjątki oraz czytelna informacja o ochronie. Statystyki lokalne, z możliwością kasowania i ograniczoną historią.
3. Komunikacja. SMS-y i obsługa rozmów z panelu, o ile pozwolą na to modem, operator i tor audio. Szyfrowane wiadomości i rozmowy wymagają osobnej usługi z szyfrowaniem od nadawcy do odbiorcy; zgodność rozmów z Torem i ich opóźnienia trzeba zbadać.
4. Miniaturyzacja. Własna płytka PCB, zasilanie bateryjne i obudowa zaprojektowana w CAD. Dyskretny wygląd zwykłego akcesorium, np. powerbanku, z miejscem na antenę, chłodzenie i bezpieczne prowadzenie przewodów.

### Jaką prywatność zapewnia ten pomysł
Wyłączenie radia telefonu ma ograniczać jego lokalną wykrywalność przez Wi-Fi i Bluetooth. Nie oznacza niewykrywalności całego zestawu: modem nadaje, a operator zna kartę SIM i może określać jego położenie. Ethernet także używa adresu MAC, ale w lokalnym połączeniu przewodowym.

Tor ma ukrywać adres LTE przed odwiedzaną usługą, lecz nie usuwa identyfikacji przez zalogowane konta ani cechy przeglądarki. Nadal potrzebne jest HTTPS. Filtr DNS blokuje wybrane domeny, nie całą telemetrię. Zwykłe SMS-y i połączenia operatora nie przechodzą przez Tor i nie zapewniają szyfrowania od nadawcy do odbiorcy.

### Jak pokażemy, że to działa
Demonstracja docelowa: telefon z wyłączonymi radiami otwiera stronę przez Ethernet; test potwierdza wyjście przez Tor; kontrolne zapytanie do zablokowanej domeny zwiększa licznik w panelu; zatrzymanie Tora odcina internet, pozostawiając dostęp do panelu. Sprawdzimy również brak obejścia ochrony przez DNS, IPv6 i UDP. To kryteria odbioru, nie wyniki już wykonanych testów.

### Podstawa techniczna
Dokumentacja Apple: tryb samolotowy i Bluetooth; Tor Project: ochrona ruchu, ograniczenia i mosty. Wyniki prototypu: rozdziały 01–07; aktualny stan i ograniczenia: docs/STATUS.md. Pełnej ochrony prywatności jeszcze nie zweryfikowano.
