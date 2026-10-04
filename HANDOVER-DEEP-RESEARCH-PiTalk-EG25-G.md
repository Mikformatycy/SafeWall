# Handover do Deep Research: PiTalk / Quectel EG25-G — skrajnie wolne LTE

> Zapis historyczny testów prototypu z 3 października 2026. Opis połączeń i wdrożeń odnosi się do czasu próby. Aktualny stan projektu, dashboardu i deklaracji dotyczących Tora: [STATUS](docs/STATUS.md). Surowe logi oraz kopie są lokalne.

Stan wiedzy: 3 października 2026. Dokument diagnostyczny do osobnej analizy; nie jest materiałem promocyjnym SafeWall. Zawiera również problemy pominięte w krótkim zgłoszeniu hackathonowym. Nie zawiera haseł, PIN-u ani identyfikatorów abonenta.

## Zadanie dla ChatGPT Deep Research

Przeprowadź pogłębione badanie przyczyn skrajnie wolnej transmisji i timeoutów w modemie Quectel EG25-G na płytce PiTalk od SB Components. Szukaj przede wszystkim na forum i w dokumentacji Quectela, w materiałach SB Components / sbcshop oraz ich repozytoriach GitHub. Pomocniczo użyj dobrze udokumentowanych przypadków tego samego modułu u innych producentów.

Nie zakładaj z góry awarii sprzętu, błędu firmware, przeciążenia stadionu ani limitu UART. Porównaj hipotezy z poniższymi wynikami. Rozróżniaj obserwacje, relacje użytkownika i przypuszczenia. Odpowiedz po polsku, z bezpośrednimi linkami i datami źródeł. Gdy nie ma potwierdzonej naprawy, napisz to wprost.

Oczekiwany rezultat:

1. Krótki wniosek oraz ranking przyczyn: dowody za/przeciw, poziom pewności i brakujący pomiar.
2. Trafne zgłoszenia z Quectel/SB Components: dokładny model, firmware, objaw, próba naprawy i informacja, czy autor potwierdził jej skuteczność.
3. Minimalny plan testów zmieniających po jednym czynniku, z wynikiem rozstrzygającym każdą hipotezę.
4. Polecenia diagnostyczne dobrane do EG25-G: osobno odczyty, zmiany tymczasowe i trwałe; wymagania, skutki uboczne oraz sposób cofnięcia. Najpierw weryfikuj składnię w instrukcji właściwego modelu.
5. Dwa krótkie zgłoszenia po angielsku: do Quectela (moduł/firmware) i SB Components (płytka/zasilanie/antena). Przygotuj treść, ale niczego nie wysyłaj.

## 1. Najważniejsze fakty

- Ten sam PiTalk według użytkownika około rok wcześniej działał z normalną prędkością na T-Mobile i Play, przez USB na Windowsie. Nie znamy ówczesnego firmware, sterownika, miejsca, pasma ani konfiguracji zasilania.
- Obecnie występują bardzo wolne pobrania i timeouty na Raspberry Pi: zarówno UART/PPP, jak i USB/QMI. Po fizycznym odłączeniu GPIO problem pozostał.
- Problem niepełnego pobrania odtworzono również wewnętrznym klientem HTTP modemu, zapisując plik bezpośrednio w RAM modułu, bez transferu jego treści do hosta.
- Użytkownik zgłasza podobną powolność na Windowsie po instalacji sterowników. Nie zebrano logów Windows ani informacji o trybie połączenia.
- Ta sama SIM w iPhonie 16 w tym samym miejscu według użytkownika osiągnęła przez LTE 73,9 Mb/s pobierania i 55,1 Mb/s wysyłania. To relacja użytkownika, nie niezależny pomiar; pasmo, komórka i serwer testu telefonu są nieznane.

To nie jest problem Tora: Tor nie był zainstalowany ani używany podczas pomiarów. Strona check.torproject.org służyła jedynie jako test strony internetowej i pokazywała adres operatora.

## 2. Sprzęt i środowisko

| Element | Dane |
|---|---|
| Płytka modemowa | PiTalk 4G HAT, SB Components; dokładna rewizja fizycznej PCB niepotwierdzona |
| Moduł | Quectel EG25-G; nie utożsamiać z EG25-GC ani EC25 |
| Pełny firmware | EG25GGBR07A08M2G_30.203.30.203 |
| USB | VID:PID 2c7c:0125; enumeracja USB 480 Mb/s, co nie jest prędkością LTE |
| Operator | T-Mobile Polska, MCC/MNC 26002, APN internet |
| Antena | Jedna antena z zestawu, podłączona do GSM ANT; model i sprawność niepotwierdzone |
| Host główny | Raspberry Pi 4 Model B Rev 1.4, 4 GB; Raspberry Pi OS Lite 64-bit, Debian Trixie |
| Oprogramowanie Pi | NetworkManager, ModemManager, qmi_wwan, nftables, dnsmasq |
| Inne hosty | MacBook/macOS, Windows (dokładne wersje i sterowniki niezanotowane) |
| Miejsce | Hackathon na stadionie; próbowano zmiany miejsca na skierowane ku antenie GSM |

Podczas części testów Pi było zasilane wyłącznie z USB-C MacBooka, a modem z USB-A Pi. W późniejszym teście modem był zasilany bezpośrednio z huba USB-A przy Macu, bez udziału Raspberry Pi. Waveshare UPS HAT nie został uruchomiony. Nie zmierzono oscyloskopem napięcia na module ani spadków pod obciążeniem. Zmiana hosta nie eliminuje wspólnego regulatora płytki PiTalk.

## 3. Topologie

Pierwotnie:

```text
Mac -- USB-C (zasilanie + SSH) --> Raspberry Pi
                                      |
                                  UART / GPIO
                                      |
                                   PiTalk LTE

Pi Ethernet --> adapter USB-C–Ethernet --> iPhone
```

Później:

```text
Mac -- USB-C --> Pi -- USB-A / USB-C, QMI --> PiTalk LTE
                         GPIO fizycznie odłączone
```

Test niezależny:

```text
Mac --> hub USB-A --> PiTalk LTE
                       |-- AT przez libusb / PyUSB
                       |-- chwilowo ECM
                       |-- wewnętrzny klient HTTP zapisujący do RAM
```

Na Pi prywatny Ethernet ma 192.168.76.1/24; iPhone wcześniej otrzymał 192.168.76.72 i otwierał strony. SSH Pi–Mac działa przez oddzielny USB gadget 10.12.194.1. Błędny początkowy adapter Ethernet telefonu wymieniono; przydział IP zaczął działać. Późniejsze testy modemu były wykonywane bez telefonu i nie zależą od tego adaptera.

## 4. Co próbowaliśmy i co z tego wynika

### UART oraz przejście na USB

UART działał przy 115200 baud. Teoretyczny limit 8N1 to około 11,52 kB/s przed narzutem PPP. Próby 230400 i 921600 nie dały oczekiwanej poprawy; przywrócono 115200. Skorygowano kontrolę przepływu, w tym AT+IFC=0,0 i ustawienia PPP bez RTS/CTS.

Następnie połączono modem przez USB/QMI (sterowanie cdc-wdm0, interfejs IP wwan0). Problem pozostał. Odłączono fizycznie modem od GPIO, pozostawiając tylko USB, i zrestartowano go: nadal bez poprawy. Niski baud rate nie tłumaczy więc całego problemu.

### Routing, DNS i TCP na Pi

Weryfikowano trasę przez wwan0, reguły nftables i liczniki interfejsu. Nie obserwowano przyrostu błędów interfejsu ani odrzuceń zapory wyjaśniających objaw. Pominięcie DNS nie rozwiązało problemu. W przechwyconym TCP widziano brakujące segmenty i oczekiwanie na retransmisje rzędu 0,7 s; brak odpowiedzi był widoczny już na WAN.

Krótkie pingi potrafiły przechodzić poprawnie mimo bardzo wolnego HTTP. Brak strat w trzech pingach nie oznacza poprawnego transferu większego strumienia. Tymczasowe zmiany testowe zapory/MTU/trasy usunięto; nie mamy udokumentowanego rozstrzygającego testu PMTU, więc nie uznajemy tej hipotezy za wykluczoną.

### Radio, antena i lokalizacja

Obserwowano LTE B3 (EARFCN 1575), później B1 (EARFCN 225), szerokość 15 MHz. Próbki bywały bardzo dobre: RSRP około −51 do −59 dBm, RSRQ około −7 dB, SNR do 30 dB. To chwilowe odczyty, nie pełna rejestracja jakości podczas każdej retransmisji.

Użytkownik przeniósł sprzęt bliżej widoczności anteny stadionu. Nie stwierdzono poprawy. Przy okazji nastąpił restart Pi i nowa sesja danych, więc nie był to idealny test wyłącznie lokalizacji. Nie ustalono, czy restart wynikał z odpięcia kabla.

Krótki test ustawienia divctl=1 nie pomógł; przywrócono divctl=0. Nie zmieniano losowo blokady pasm. Jeden tor odbiorczy miał silniejszy sygnał, co jest zgodne z użyciem jednej anteny. Nie ustalono, czy antena/złącze są uszkodzone. Nie zakładaj, że druga antena jest obowiązkowa — sprawdź wymagania EG25-G i konstrukcję PiTalk.

### Zasilanie

Pi raportowało get_throttled=0x0. To nie jest pomiar zasilania modułu LTE. Próba HTTP wewnątrz modemu nie powiodła się także przy zasilaniu z huba Maca, ale nadal używano tej samej płytki modemowej i anteny. Jakość kabla i tor zasilania pod obciążeniem nie zostały całkowicie zweryfikowane.

## 5. Rzeczywiste pomiary i jednostki

**Około 1,4 kB/s oznacza kilobajty, nie kilobity na sekundę: to około 11,2 kb/s.** Nie jest to ukończony wynik Speedtest ani wiarygodny pomiar maksymalnej przepustowości modemu. To średnia dla małego pliku, uwzględniająca zestawienie połączenia i przestoje.

| Próba | Wynik |
|---|---|
| Pi po USB, pobranie HTTPS 16 KiB | 11,42 s, około 1435 B/s |
| Pi, HTTP http://httpbingo.org/bytes/16384 | 16 384 B w 8,316 s, około 1970 B/s |
| Ten sam HTTP po zmianie miejsca | 16 384 B w 11,734 s, około 1396 B/s |
| Ping 1.1.1.1 przy ostatniej próbie | 3/3 odpowiedzi, średnio 31,392 ms |
| Oficjalny Ookla CLI 1.2.0.84, Pi aarch64 | Nie ukończył pomiaru; brak końcowego download/upload |

Ookla uruchomiono ze wskazaniem wwan0 i sprawdzono trasę domyślną oraz metadane interfejsu/operatora. Wybrany serwer: T-Mobile Polska, Kraków, ID 23123, kra1.t-mobile.pl:8080. W pierwszej próbie postęp pokazywał 1086–1777 B/s, następnie błąd Cannot read po 11,59 s. Po zmianie miejsca jedna próbka 462 B/s i Cannot open socket po 12,46 s. Nie interpretować jako wyniku 0 Mb/s ani pełnego Speedtestu. Porównanie z wynikiem telefonu ma różne narzędzia i rozmiary prób.

## 6. Najważniejszy test: HTTP wewnątrz EG25-G

Aby ominąć IP/sterownik/zaporę hosta, wykonano pobranie publicznego pliku 16 KiB wewnętrznym klientem HTTP modemu. Połączenie modemu z hostem przenosiło polecenia i odpowiedzi AT, nie treść pliku.

URL: http://httpbingo.org/bytes/16384

Użyto kontekstu danych APN internet, QHTTPGET i QHTTPREADFILE do pliku RAM. Rozmiar sprawdzono QFLST. W trakcie testu na Pi zatrzymano konkurujące sterowanie przez ModemManager.

| Host zasilający / sterujący | Odpowiedź GET | Zapis w RAM | Zakończenie odczytu |
|---|---|---|---|
| Raspberry Pi | HTTP 200, deklarowane 16 384 B; nagłówki po 0,338 s | 10 549 B | QHTTPREADFILE: 702 po 30,806 s |
| Mac przez hub USB-A | HTTP 200, deklarowane 16 384 B; nagłówki po 0,293 s | 10 737 B | QHTTPREADFILE: 702 po 31,686 s |

Kod 702 opisano jako timeout HTTP(S). Pliki testowe usunięto z RAM, zakończono HTTP, zdezaktywowano wewnętrzny kontekst i odtworzono ustawienia sprzed prób.

Wniosek: niepełny transfer występuje także bez stosu IP Raspberry Pi, jego nftables i fizycznego UART. Nie jest to dowód rozstrzygający między firmware, radiem, płytką, zasilaniem i operatorem. Sprawdź też, czy sposób użycia wewnętrznego HTTP, timeouty lub serwer testowy mogły wprowadzić niezależne ograniczenie — nie traktuj podobnych rozmiarów częściowych plików automatycznie jako dowodu znanego błędu bufora.

## 7. Osobny problem USB-C i próba ECM na Macu

Przy początkowym podłączeniu do Maca użytkownik zgłaszał brak diody i enumeracji USB. Po użyciu portu USB-A huba i kabla A–C modem pojawił się i odpowiadał na AT. W publicznym schemacie PiTalk V1.1 piny CC1/CC2 gniazda USB-C wyglądają na niepodłączone. Może to wyjaśniać brak zasilania C–C, lecz rewizja użytkownika i wcześniejszy kabel nie zostały potwierdzone. Nie utożsamiaj tego automatycznie z przyczyną wolnego LTE.

Na Macu w oryginalnym QMI nie było portów szeregowych ani karty sieciowej. AT obsłużono przez PyUSB/libusb, interfejs 2, bulk OUT 0x03 i IN 0x84.

Tymczasowo ustawiono usbnet=1 (ECM), IPv4 i APN internet w kontekście 1. Mac uzyskał DHCP 192.168.225.22, a po restarcie .24; brama 192.168.225.1. Modem był zarejestrowany w LTE, miał aktywny PDP i DNS operatora. Lokalny ping do bramy: 3/3, średnio 1,031 ms. Zewnętrzny ping otrzymywał od modemu Destination Net Unreachable, DNS modemu odpowiadał REFUSED, HTTP/HTTPS nie zestawiały połączenia. Restart AT+CFUN=1,1 nie rozwiązał problemu.

Testy przypisano do interfejsu ECM; zwykły internet Maca nie był używany do tych pomiarów. Nie wykonano pełnego Speedtestu na Macu. Objaw ECM może być osobnym problemem zarządzania połączeniem danych/NAT modemu.

Na zakończenie przywrócono usbnet=0 (QMI), oryginalny kontekst 1 IPv4v6 z pustym APN i danymi uwierzytelniającymi oraz włączone radio CFUN=1. Odczyt potwierdził ustawienia i powrót interfejsu vendor-specific. Później użytkownik testował Windows; obecny host i stan konfiguracji są nieznane.

## 8. Czego jeszcze nie zrobiliśmy

Nie wykonano testu SIM Plusa, chociaż użytkownik może ją zdobyć. Nie porównano drugiego sprawnego modemu na tej samej SIM, nie podmieniono kontrolnie sprawdzonej anteny, nie zmierzono zasilania modułu pod obciążeniem. Nie ustalono aktualnego profilu MBN. Nie znamy trybu USB, firmware/sterownika z zeszłorocznego działającego Windows ani obecnych logów Windows. Nie wykonano aktualizacji firmware, downgrade, resetu fabrycznego ani zmiany IMEI. Nie wyłączano i nie zmieniano PIN-u SIM.

## 9. Hipotezy i testy do opracowania

| Hipoteza | Co pomaga ją sprawdzić |
|---|---|
| Zasilanie lub regulator PiTalk | Pomiar na punktach wskazanych przez producenta podczas transmisji; sprawdzony pojedynczy tor zasilania |
| Antena, złącze lub tor RF | Kontrolna antena zgodna z pasmami i złączem; oględziny; porównanie parametrów obu torów |
| Współpraca modemu z T-Mobile / profil MBN | SIM Plusa w tym samym zestawie; odczyt MBN bez zmiany; porównanie APN i typu PDP |
| Firmware lub usterka modułu | Drugi modem na tej samej SIM; potwierdzenie dokładnego wariantu i poprawki przez Quectel |
| Parametry sesji / TCP / sieć | Porównanie kilku hostów testowych, rozmiarów plików i protokołów; kontrolny PMTU/MSS, jeśli źródła i pomiary to uzasadniają |

Priorytet: mała liczba rozstrzygających prób, zamiast kolejnych restartów i powtarzania speedtestów. Lepszy wynik Plusa nie dowodzi awarii T-Mobile; gorszy nie dowodzi uszkodzenia samego modułu. Potrzebny jest kontrolowany kontekst porównania.

Odczyty proponowane do zebrania po potwierdzeniu hosta i wyłączności portu AT:

```text
AT+QGMR
AT+QMBNCFG="List"
AT+QENG="servingcell"
AT+QCFG="band"
AT+QCFG="usbnet"
AT+CGDCONT?
AT+CGACT?
AT+CPIN?
```

Zweryfikuj dokładną składnię w dokumentacji EG25-G. Nie wysyłaj wszystkich poleceń bez sprawdzenia zajętości portu. servingcell może ujawniać lokalizację przez identyfikator komórki — anonimizuj przed publikacją.

## 10. Źródła znalezione wcześniej — zweryfikuj i rozszerz

### Quectel

- https://forums.quectel.com/t/eg25-frequent-disconnects-dropped-packets/18433 — podobna niezależność od hosta; pierwotny firmware 01.003.01.003, inny niż nasz. Sugestie firmware i innego operatora, bez potwierdzonej naprawy naszego przypadku.
- https://forums.quectel.com/t/eg25-poor-rsrq-with-excellent-rssi-rsrp/19049 — dobry RSRP nie wyklucza problemów RF; tam RSRQ bywało dużo gorsze niż nasze próbki.
- https://forums.quectel.com/t/eg25-g-firmware-update/21217 — zgłoszenia wolnej transmisji i ostrzeżenia dotyczące ścieżek aktualizacji/cofania wersji.
- https://forums.quectel.com/t/how-to-get-and-parse-content-of-mbn-file/43384 — dokładnie 30.203.30.203, lecz objaw IMS/VoLTE, nie potwierdzony błąd szybkości danych.
- https://forums.quectel.com/t/ec25-usb-interfaces-crash/23356 — potwierdzony problem zasilania w pokrewnym EC25; inny moduł i objaw, nie bezpośrednia diagnoza.

Dodatkowe materiały:

- https://forums.quectel.com/t/eg25-frequently-disconnects/57324 — PinePhone/suspend, słabsze dopasowanie do aktywnego pobierania.
- https://quectel.com/content/uploads/2021/03/Quectel_EG25-G_Hardware_Design_V1.4.pdf — zasilanie i anteny.
- https://forums.quectel.com/uploads/short-url/kxS3asnEWfTxweAAYcLiomJakDE.pdf — instrukcja HTTP(S), m.in. kod 702.

### SB Components / PiTalk i materiały pomocnicze

- https://github.com/sbcshop/Pitalk_4G_HAT_Hardware — repozytorium sprzętu; sprawdź schematy, rewizje, issues i dokumentację producenta.
- https://github.com/sbcshop/Pitalk_4G_HAT_Hardware/blob/main/Design%20Data/Schematic_PiTalk_4G.pdf — schemat PiTalk; hipoteza CC1/CC2 i zasilania C–C.
- https://docs.sixfab.com/page/cellular-internet-connection-in-ecm-mode — procedura ECM, jako źródło pomocnicze; nie zakładać identycznej płytki.
- https://www.ti.com/lit/SLYY228 — wymagania wykrywania odbiornika USB-C przez CC.

Znajdź oficjalne materiały SB Components dotyczące konkretnego PiTalk 4G HAT: wymagania zasilania USB vs GPIO, rewizje PCB, regulator, antena GSM ANT/ANT_DIV, sterowniki Windows i zalecane firmware. Nie zakładaj istnienia forum SB Components pod zgadywanym adresem — odnajdź rzeczywisty kanał wsparcia i publiczne zgłoszenia.

Przykładowe frazy: `EG25GGBR07A08M2G_30.203.30.203 slow throughput`, `EG25-G QHTTPREADFILE 702 partial download`, `PiTalk 4G HAT slow internet`, `SB Components PiTalk USB power CC1 CC2`, `EG25-G T-Mobile Poland MBN packet loss`, `EG25-G ECM destination net unreachable`.

## 11. Ograniczenia i bezpieczeństwo proponowanych działań

SIM jest prywatna. Nie zmieniać ani nie wyłączać jej zabezpieczeń; nie zgadywać PIN-u, nie używać PIN-u starej karty przy nowej SIM. Przed wymianą SIM poprawnie zakończyć sesję i wyłączyć modem. Nie podłączać przypadkowo kilku źródeł 5 V równolegle.

Nie zalecać niezweryfikowanej paczki firmware, downgrade, factory reset, zmiany MBN ani ustawień pasm bez dokumentacji, uzasadnienia i planu powrotu. T-Mobile Polska to nie T-Mobile USA. Genericzny opis EC25 w narzędziu USB nie oznacza, że można użyć firmware EC25.

Nie publikować PIN-u, IMSI, ICCID, IMEI, numeru telefonu ani dokładnych identyfikatorów komórki. Raport badawczy powinien wskazywać, jakie dane zebrać prywatnie dla wsparcia, zamiast prosić o pełny niezredagowany dump.

## 12. Lokalne materiały dowodowe

Ten handover jest samodzielny: ChatGPT w przeglądarce nie ma dostępu do poniższych plików. Jeśli analiza potrzebuje surowych logów, wskaż konkretny zakres, a użytkownik może dostarczyć zanonimizowany wyciąg.

Folder lokalny: `Desktop/RaspberryPi-Hackathon`.

- Rozdziały 03 i 04: modem, pomiary i diagnostyka; rozdział 05: historia prób.
- Rozdział 06: test Maca/ECM i przywrócenie QMI; rozdział 07: poprzedni przegląd forum.
- Logi 47 oraz 54: Ookla i porównanie lokalizacji; logi 50 i 65: HTTP do RAM modemu.
- Logi 66–67: przywrócone ustawienia i końcowy stan; log 68: zgłoszenie użytkownika o Windowsie.

Nie mamy jeszcze ustalonej przyczyny. Celem badania jest wskazanie najlepszego następnego pomiaru i ścieżki naprawy, a nie potwierdzenie za wszelką cenę jednej hipotezy.
