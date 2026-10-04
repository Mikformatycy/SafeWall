# Historia konfiguracji i wyniki testów

> Zapis historyczny testów prototypu z 3 października 2026. Opis połączeń i wdrożeń odnosi się do czasu próby. Aktualny stan projektu, dashboardu i deklaracji dotyczących Tora: [STATUS](docs/STATUS.md). Surowe logi oraz kopie są lokalne.

## Przygotowanie karty

3 października 2026 przygotowano kartę 63,2 GB wykrytą na Macu jako `/dev/disk8`. Oznaczenie dysku było poprawne wtedy; nie wolno zakładać, że będzie takie samo po ponownym włożeniu.

Obraz: `2026-09-15-raspios-trixie-arm64-lite.img.xz`, oficjalny Raspberry Pi OS Lite 64-bit. Suma SHA-256 rozpakowanego obrazu:

```text
49fafba626ec00e0f9800349b9edae6caf8cfc223f673b875b72ac2797ed9576
```

Rozmiar obrazu wynosił 3 061 841 920 bajtów. Pobrany obraz i pełny odczyt z karty po zapisie miały zgodną sumę.

CLI Raspberry Pi Imager 2.0.11.1 zatrzymało się podczas odmontowania na tym Macu. Kartę zapisano bezpośrednio, korzystając z systemowego `authopen` po zatwierdzeniu dostępu przez użytkownika. Konfigurację pierwszego uruchomienia zapisano i odczytano kontrolnie z partycji `bootfs`.

Cloud-init ustawił użytkownika `piotr`, nazwę `piotr4mmc-raspberrypi`, strefę `Europe/Warsaw`, SSH, hasło podane przez użytkownika, tryb USB gadget i dane hotspotu. W późniejszej konfiguracji routera Wi-Fi wyłączono; nie usunięto zapisanych danych hotspotu.

## Pierwszy dostęp po USB

Mac wykrył `Raspberry Pi USB Gadget`. Potwierdzono trasę do `10.12.194.1` przez ten interfejs oraz zalogowano się hasłem. W jednej z prób `SSH_CONNECTION` wskazywało `10.12.194.6 → 10.12.194.1:22`.

Ping: 3/3 odpowiedzi, bez utraty pakietów, średnio około 0,62 ms. Potwierdzono architekturę `aarch64`, właściwą nazwę hosta i `sudo` jako root. Wyniki zasilania dotyczyły małego obciążenia.

## Konfiguracja routera

1. Utworzono osobny klucz SSH na Macu i alias `pi-usb`; zachowano istniejącą konfigurację SSH.
2. Zainstalowano ModemManager, narzędzia QMI/MBIM, `tcpdump` i DNS. Nftables oraz dnsmasq-base były już obecne.
3. Pakiety pobrano przez tymczasowy SOCKS w tunelu SSH USB z Maca. Tunel zamknięto po instalacji; nie zapisano stałego proxy APT.
4. Wdrożono własną tabelę nftables, statyczny LAN, DHCP/DNS oraz automatyczne wykrywanie aktywnego WAN komórkowego.
5. Przed aktywacją utworzono kopię i timer cofnięcia; anulowano go dopiero po sprawdzeniu nowego połączenia SSH i usług.

Źródło sposobu użycia proxy APT: [podręcznik Debiana](https://manpages.debian.org/trixie/apt/apt-transport-http.1.en.html).

## Wyniki testów lokalnych

Test `scripts/test-router-isolated.py` uruchamia tymczasowe przestrzenie sieciowe Linux, prawdziwy nftables i dnsmasq. Używa wdrożonej konfiguracji oraz kopii tabeli USB NetworkManagera. Nie korzysta z SIM, wspólnej sieci hackathonu ani telefonu.

| Test dostępu | Wynik |
|---|---|
| SSH z USB do routera | PASS |
| SSH z Ethernetu do routera | Blokada potwierdzona |
| SSH z WAN do routera | Blokada potwierdzona |
| Dostęp do dodatkowej, nieudostępnionej usługi | Blokada potwierdzona |

| Test routingu | Wynik |
|---|---|
| LAN → WAN z translacją źródła i ruchem powrotnym | PASS; serwer widział adres WAN routera |
| USB → WAN mimo reguł „shared” NetworkManagera | Blokada potwierdzona |
| Nowe połączenie WAN → LAN | Blokada potwierdzona |
| LAN → administracyjna sieć USB | Blokada potwierdzona |
| Ruch bez aktywnego interfejsu modemu | Blokada potwierdzona |

| Test usług LAN | Wynik |
|---|---|
| Lokalny DNS `router.pi.home.arpa` | `192.168.76.1` |
| DHCP DISCOVER/OFFER/REQUEST/ACK | PASS; przydzielony adres z puli oraz poprawna brama i DNS |

**Wszystkie 11 testów zakończyło się powodzeniem.** Log: `logs/04-isolated-tests.txt`.

Wcześniejsze przebiegi ujawniły ograniczenia klienta testowego: należało dopuścić zarówno odrzucenie, jak i upłynięcie czasu połączenia oraz wydłużyć oczekiwanie DHCP z 3 do 10 sekund. W tych iteracjach nie otwierano dodatkowych portów w działającym firewallu. Zachowano logi wcześniejszych prób.

## Test po restarcie

Kontrola 3 października 2026 o 13:28 CEST potwierdziła nowy start systemu i niezależne logowanie SSH przez USB. Usługi `ssh`, `nftables`, `pi-lan-dnsmasq` i `ModemManager` były aktywne oraz włączone do startu automatycznego.

| Sprawdzenie po restarcie | Wynik |
|---|---|
| Adresy Pi | USB `10.12.194.1/28`, LAN `192.168.76.1/24` |
| DHCP USB na Macu | `10.12.194.13` na `en11`; odpowiedź bez opcji bramy i DNS |
| Trasy Maca | Pi przez `en11`; dotychczasowa brama Internetu przez `en9` |
| Lokalny DNS i firewall | `router.pi.home.arpa` → `192.168.76.1`; własna tabela i tabela USB NetworkManagera obecne |
| Tryb offline i zasilanie | Pusty `wan_ifaces`, Wi-Fi wyłączone, `get_throttled=0x0`, temperatura 47,2°C |

Potwierdzono brak testowych przestrzeni sieciowych, tunelu SOCKS na porcie 18080 i aktywnych timerów cofnięcia. Wszystkie 13 wdrożonych plików miało sumy SHA-256 zgodne z kopiami w tym folderze. Wyniki: `logs/05-after-reboot.txt`, `logs/05-mac-usb-after-reboot.txt`, `logs/06-deployed-checksums.txt`.

Przy pierwszym restarcie tymczasowy timer awaryjny wykonał cofnięcie po 180 sekundach bez anulowania. Dziennik potwierdził, że usługi wcześniej wystartowały poprawnie. Przywrócono te same sprawdzone pliki, usunięto tymczasowy timer i wykonano powyższy, udany test kolejnego restartu. Kopia stanu sprzed wdrożenia pozostała nienaruszona.

## Granice wykonanej weryfikacji

- Modem PiTalk został później rozpoznany jako EG25; działające połączenie LTE opisano w końcowym wpisie poniżej.
- Po późniejszym odblokowaniu SIM potwierdzono Internet T-Mobile na APN `internet`; nie wykonano speedtestu ani długiego testu stabilności.
- Fizyczne połączenie iPhone’a przetestowano później po wymianie adaptera; szczegóły w końcowym wpisie.
- Nie uruchomiono Waveshare UPS HAT ani nie sprawdzono jego współpracy z USB-C Maca.
- Nie wykonano testu poboru mocy ani wydajności pod obciążeniem LTE.

Router IPv4 sprawdzono lokalnie, a następnie uzyskano Internet komórkowy na Pi. Fizyczny iPhone i UPS wymagają osobnego testu.

## Sprawdzenie po włożeniu prywatnej SIM T-Mobile

3 października 2026 około 13:35 CEST sprawdzono stan przez USB po informacji użytkownika o włożeniu prywatnej karty z Internetem. ModemManager zgłosił `No modems were found`; lista USB nie zawierała modemu, nie było portów `ttyUSB`, `ttyACM` ani `cdc-wdm`. Pi miało wyłącznie lokalne trasy USB i Ethernet, a `ip -4 route get 1.1.1.1` zwróciło `Network is unreachable`.

Wynik: brak dostępu do Internetu na Pi w chwili sprawdzenia; stan samej SIM i rejestracja T-Mobile pozostają niezweryfikowane. Nie próbowano PIN-u/PUK ani nie wykonywano zapisów na karcie SIM. Kontrola była odczytem stanu systemu; nie przesłano danych przez sieć komórkową. Potrzebne są oznaczenie modelu PiTalk i potwierdzenie połączenia danych modem–Pi. Log: `logs/07-tmobile-discovery.txt`.

## Działające T-Mobile przez GPIO — test zakończony

Po potwierdzeniu przez użytkownika połączenia GPIO, anten i użycia przycisku Power włączono UART oraz wyłączono konsolę szeregową. Po restarcie modem odpowiedział jako Quectel EG25. Reguła udev włączyła wykrywanie tego konkretnego portu przez ModemManager.

SIM wymagała PIN-u. Wykonano jedną udaną próbę z wartością podaną przez użytkownika. Nie zmieniono zabezpieczenia ani nie zapisano PIN-u w profilu; sprawdzono `gsm.pin-flags=2` i brak wartości `gsm.pin`. Modem zarejestrował się w sieci macierzystej `26002` (T-Mobile Polska), w technologii LTE.

Pierwsza próba PPP nie powiodła się z powodu ustawień sterowania portem. Po dodaniu `local` i `nocrtscts` wyłącznie dla `ttyS0` uzyskano działający interfejs `ppp0`. W skrypcie WAN poprawiono parsowanie listy DNS zwracanej przez NetworkManager na jednej linii. Wszystkie reguły izolacji USB pozostały w mocy.

Test końcowy: ping `1.1.1.1` 3/3, DNS przez `192.168.76.1`, HTTPS `example.com` przez `ppp0` z odpowiedzią 200 OK; brak flag ograniczania zasilania/temperatury (`0x0`). O 13:57 CEST profil pozostawał połączony. Zapisano kopię profilu bez PIN-u, nowe pliki UART/udev/PPP i instrukcję ponownego łączenia. Logi: `08-uart-*`, `09-tmobile-first-connect.txt`, `10-tmobile-connected.txt`, `10-internet-test.txt`.

## Pierwsza fizyczna próba iPhone’a przez Ethernet

Około 14:13–14:16 CEST po podłączeniu telefonu Pi zgłaszało `eth0` administracyjnie UP, ale `NO-CARRIER`, `carrier=0`. Liczniki nadanych i odebranych pakietów były zerowe; brak wpisów DHCP i sąsiadów ARP. Czterdziestosekundowy podgląd nie odebrał pakietów ARP/DHCP. iPhone według użytkownika widział adapter w ustawieniach Ethernet, ale nie pokazywał adresu IP.

Równoległe sprawdzenie Internetu na Pi: ping przez `ppp0` 2/2 i poprawna odpowiedź DNS przez `192.168.76.1`. Odczyt ustawień sterownika przez ioctl potwierdził autonegocjację włączoną (`autoneg=1`) i brak trybów zgłaszanych przez partnera (`lp_advertising=0`). Pole `auto-negotiate=no` w domyślnym profilu NetworkManagera nie wyłączało jej w sterowniku: przy braku speed/duplex oznacza pozostawienie dotychczasowych ustawień. Potwierdza to [dokumentacja NetworkManagera](https://networkmanager.dev/docs/api/latest/settings-802-3-ethernet.html).

Odświeżono wyłącznie profil `pi-iphone-lan` poleceniami down/up; USB i LTE pozostały aktywne. Bezpośrednio po tym nadal brak fizycznego linku. Dalszy krok: ponowne podłączenie adaptera przy odblokowanym telefonie i próba innego kabla RJ45. Na tym etapie nie można było wskazać adresu telefonu ani wykonać miarodajnego pingu do niego. Logi: `logs/12-iphone-ethernet-discovery.txt`, `logs/12-iphone-after-link-refresh.txt`.

## Wymiana adaptera i pierwszy działający link iPhone’a

Po wymianie adaptera USB-C–Ethernet przez użytkownika fizyczny link podniósł się (`carrier=1`). Telefon otrzymał z DHCP `192.168.76.72`. Ping z Pi do telefonu: 3/3 odpowiedzi, średnio 0,528 ms. Sąsiad ARP był osiągalny.

Liczniki nftables i krótki podgląd nagłówków potwierdziły rzeczywisty ruch telefonu przez modem w obie strony. Nie stwierdzono ogólnej blokady forward/NAT; nie otwierano dodatkowych portów. Pierwsze próby HTTPS z Pi do check.torproject.org i example.com przekroczyły limit czasu, mimo działającego ICMP. Kolejne próby do tych samych serwisów, z adresami z DNS wskazanymi przez `curl --resolve`, zakończyły się 200 OK w około 3,4 i 5,6 s, z weryfikacją TLS. Widoczne były retransmisje TCP; w kolejce wyjściowej PPP odnotowano wcześniejsze odrzucenia pakietów. To wskazuje na problem wydajności/jakości ścieżki, nie na brak fizycznego połączenia iPhone’a. Nie potwierdzono jeszcze ostatecznej przyczyny timeoutów w Safari.

UART pozostaje przy 115200 bit/s. Nie ma konfiguracji Tora; check.torproject.org służyło tutaj jako wskazany przez użytkownika cel testu HTTPS. Logi: `14-iphone-connected-baseline.txt`, `14-upstream-web-tests.txt`, `14-iphone-traffic.txt`, `14-upstream-tcp-trace.txt` w folderze logs.

## Potwierdzone strony WWW na iPhonie i ograniczenie UART

Użytkownik potwierdził, że na iPhonie otworzyły się zarówno example.com, jak i check.torproject.org. Druga strona pokazała adres operatora T-Mobile. Oznacza to zakończony test całego toru Ethernet–router–modem–Internet; konfiguracja nie zawiera Tora. Obie strony ładowały się bardzo długo.

Połączenie danych EG25–Pi nadal używa UART 115200 bit/s, 8N1. Matematyczny limit danych UART wynosi 115200/10 = 11520 bajtów/s, przed dodatkowymi nagłówkami i retransmisjami. W podglądzie ruchu potwierdzono retransmisje; nie wykonano speedtestu ani nie ustalono pełnej wydajności radiowej LTE. Zaproponowano połączenie USB-A Raspberry Pi → USB-C modemu PiTalk jako następny test, bez odłączania kabla administracyjnego Pi–Mac. Samo przełączenie na USB nie zostało jeszcze wykonane.

## Próby UART i strat pakietów — 3 października 2026

Na prośbę użytkownika zbadano możliwość pozostania przy kompaktowym połączeniu GPIO. `AT+IPR=?` potwierdziło wyższe prędkości. Wykonano kontrolowane próby 921600 oraz 230400 bit/s, za każdym razem dopasowując modem, udev, `serial.baud` i `ppp.baud`. Dostęp SSH po USB działał przez cały czas.

- 921600: ping mały 3/3, pełny HTTPS example.com 2,77 s, Tor Check 8,32 s. Dalsze pobierania timeoutowały; użytkownik nie widział wyraźnego przyspieszenia.
- Pomiar bez ruchu telefonu: 13 721 B z 32 KiB w 12 s, timeout. Tymczasowa tabela blokująca forward została usunięta w `finally`; sprawdzono jej brak.
- Testy rozmiaru pakietów i ślad TCP wykazały luki i retransmisje. Tymczasowa trasa MTU 576 dała 16 KiB w 11,83 s; trasę usunięto.
- 230400: brak poprawy, straty również dla większego ICMP. Powrót do 115200, ponowne PPP i ping 3/3. Pozostawiono poprawkę `ID_MM_TTY_FLOW_CONTROL="none"`, zgodną z TX/RX bez RTS/CTS.
- Nie wykonywano `AT&W`, resetu modemu, zmian SIM ani ponownego wysyłania PIN-u. Przygotowano porównanie z USB; jego wyniku na tym etapie jeszcze nie ma.

Szczegóły i ograniczenia pomiarów: rozdział 03, logi `15`–`23`. Kopie wdrożonej reguły i profilu uaktualniono w `config/`; stan sprzed prób zachowano w `backups/uart-before-speed-tests/`.

## Pierwszy kabel USB-A → USB-C PiTalk — 3 października 2026, 15:40

Po zgłoszeniu podłączenia kabla Pi nie wykryło nowego urządzenia USB. `lsusb`, `lsusb -t` i sysfs pokazały tylko kontrolery Pi i hub VIA; brak modemu USB i jego portów. W dzienniku kernela nie było zdarzeń USB z ostatnich 15 minut. Modem nadal działał przez `ttyS0`/PPP, a `get_throttled=0x0`.

Nie potwierdzono transmisji danych przez ten kabel. Sam brak wykrycia nie dowodzi, że kabel jest tylko do ładowania — należy sprawdzić osadzenie wtyczek i inny port USB-A, następnie znany kabel danych. Nie zmieniano profilu modemu ani ustawień SIM. Log: `logs/24-modem-usb-cable-check.txt`.

## Drugi kabel: USB/QMI działa, straty pozostają — 3 października 2026

Nowy kabel wykrył EG25-G (`2c7c:0125`) przez USB 480 Mb/s, sterownik `qmi_wwan`, `cdc-wdm0` i `wwan0`. Dodano profil `tmobile-pitalk-usb` z APN `internet`, IPv4, bez roamingu, bez zapisanego PIN-u i bez autopołączenia. Rozłączono profil UART, aktywowano USB. Router automatycznie odświeżył WAN i DNS.

Mały ping 5/5; HTTPS example.com około 3,15 s i check.torproject.org 7,63 s. Pobieranie 64 KiB zakończyło się timeoutem po 20 s i odebraniu 30 052 B. Dla większego ICMP straty potwierdzono na dwóch celach. Ślad pakietów oraz zerowe przyrosty liczników odrzuceń `input` wykluczają tę zaporę jako miejsce odrzucenia konkretnych brakujących odpowiedzi w tej próbie. Nie ustalono dokładnej przyczyny w modemie lub dalszej sieci. Kolejny wolniej wysyłany test dużego ICMP: 0/6, więc nie potwierdzono prostego limitu transferu.

`get_throttled=0x0`, brak błędów interfejsu USB. Na czas testu Ethernet do iPhone’a był bez fizycznego linku (`carrier=0`), zatem testowano Internet na samym Pi. Nie wykonywano restartu/resetu modemu, ponownego wysyłania PIN-u ani zmian zabezpieczeń SIM. Obecnie pozostaje aktywny profil USB; UART jest zapasowy. Dokumentację i kopię nowego profilu zaktualizowano. Logi 25–28.

## Radio LTE na stadionie — odczyty 3 października 2026, około 16:01–16:07

Po sugestii użytkownika o zakłóceniach na zatłoczonym stadionie sprawdzono odbiór LTE przez USB. Trzy próbki ModemManagera: RSRP −59/−58/−59 dBm, RSRQ −7 dB, SNR 16,4/30/30 dB. Po próbie przywrócono wyłączone okresowe odczyty (`signal-setup=0`).

Odczyty QMI przez istniejący `qmi-proxy`: LTE band 3, kanał 1575, szerokość 15 MHz; kolejny sygnał RSRP −58 dBm, RSRQ −7 dB, SNR 30 dB. MTU sesji 1500, zgodne z `wwan0`; liczniki modemowe TX/RX dropped = 0. Dane nie wykazały słabego odbioru w tych próbkach, ale nie diagnozują obciążenia stacji ani całego toru radiowego. Przeciążenie nadal jest hipotezą.

Nie zmieniano pasm, SIM, PIN-u, APN ani firmware i nie restartowano modemu. Profil USB pozostał aktywny. W dokumentacji dodano polecenia odczytu jakości sygnału. Otwarte pozostaje kontrolowane porównanie z telefonem: to samo miejsce/czas, ta sama SIM, wyłączone Wi-Fi i znana technologia LTE/5G. Logi 29–31.

## Porównanie z telefonem i dwa tory odbiorcze — 3 października 2026, około 16:10

Użytkownik potwierdził sprawne działanie tej samej SIM na tym stadionie w telefonie przez LTE, przy wyłączonym Wi-Fi. To zamyka wcześniejsze pytanie o LTE/5G; pasmo i komórka telefonu pozostają nieznane. Nie uznajemy tłoku na stadionie za wystarczające wyjaśnienie.

Odczyty QMI RX0/RX1 pokazały około 25 dB różnicy mocy między torami. W dwóch próbkach aktywnego TX odnotowano −28 i −21 dBm. Mały ping: 16/16; firmware bazowe `EG25GGBR07A08M2G`. Wyniki nie wyjaśniają jeszcze wcześniejszych strat dużych pakietów. Zapisano ostrożną interpretację pól QMI w rozdziale 03 i zapytano o liczbę oraz oznaczenia podłączonych anten. Log 32. Nie zmieniano konfiguracji modemu ani SIM.

## Pojedyncza antena i odświeżenie połączenia — 3 października 2026, 16:27–16:30

Użytkownik potwierdził jedną antenę z zestawu w GSM ANT. Nie zmieniono jej podłączenia ani ustawień diversity. Wykonano porównanie przed i po rozłączeniu profilu USB, wyłączeniu/włączeniu modemu przez ModemManager i ponownym połączeniu tego samego profilu. Duży ping 4/4 w obu próbach; pobranie 16 KiB odpowiednio 11,07 s i 11,39 s. Brak poprawy transferu.

Po odświeżeniu profil USB, WAN nftables i DNS działały. Nie wysyłano PIN-u ani nie zmieniano zabezpieczeń; licznik prób PIN bez zmian. Odczyt QMI potwierdził APN aktywnego przyłączenia internet i IPv4. Ustawienia domyślne modemu z innym APN pozostawiono bez zmian. Logi 33–35; szczegóły i ograniczenia w rozdziale 03.

## Ślad TCP, odczyty AT i próba jednego toru odbiorczego — 3 października 2026

Potwierdzono luki w strumieniu TCP i oczekiwanie około 0,7 s na kolejne brakujące dane. Nie wykazano odrzuceń w kolejce wwan0 ani regułach input podczas próby. Pobranie 16 KiB z pominięciem wyszukiwania DNS nadal trwało 11,10 s.

Przy rozłączonym USB i zatrzymanym ModemManagerze odczytano divctl=0, konteksty internet/IMS i pełny firmware EG25GGBR07A08M2G_30.203.30.203. Odczyt parametrów QoS nie zwrócił danych. Usługę i profil przywrócono.

W osobnej próbie ustawiono divctl=1, potwierdzono odczytem i połączono USB: 16 KiB w 11,50 s. W bloku finally przywrócono 0, ponownie połączono USB: 16 KiB w 11,28 s. QMI nadal raportował oba tory jako tuned, co ogranicza interpretację skutku fizycznego. Nie pozostawiono zmienionego ustawienia. Router odświeżył WAN do wwan0, PIN nie był wysyłany. Zapytano użytkownika o możliwość porównania aktualnej szybkości tej samej SIM w telefonie przed planowaniem kolejnych zmian. Logi 36–38.

## Fizycznie tylko USB, restart modemu i przygotowanie testu w telefonie

Przed przeniesieniem SIM użytkownik odłączył GPIO i zrestartował modem, pozostawiając go podłączonego do Pi wyłącznie po USB. Wykonano żądany ostatni test: po jednej udanej operacji odblokowania znanym PIN-em (3 próby nadal dostępne) połączono profil USB. Pingi 3/3 i 4/4; 16 KiB HTTPS w 11,42 s (1435 B/s), example.com 3,46 s. Brak poprawy. Nowa adresacja WAN 100.69.238.211, get_throttled=0x0, eth0 carrier=0. Log 39.

Następnie przygotowano wcześniej uzgodniony test SIM w telefonie: rozłączono profil, zatrzymano ModemManager, wykonano AT+QPOWD=1. Modem odpowiedział OK i POWERED DOWN, zniknął z USB i nie pojawił się ponownie w obserwacji. Przywrócono usługę ModemManager; WAN nftables celowo pusty, brak trasy domyślnej, Pi i SSH nadal działają. Log 40. SIM można przenieść do telefonu; wyniku porównania jeszcze nie ma.

## Porównanie tej samej SIM w iPhonie 16 — 3 października 2026

Po wyłączeniu modemu i przełożeniu tej samej prywatnej SIM użytkownik zgłosił wynik na iPhonie 16 przez LTE: **73,9 Mb/s pobierania i 55,1 Mb/s wysyłania**. To pomiar podany przez użytkownika, bez niezależnego odczytu aplikacji, identyfikatora komórki/pasma i serwera testowego. Poprzedzająca próba PiTalka wyłącznie po USB dała 1435 B/s przy pobraniu 16 KiB w 11,42 s. Różne narzędzia i wielkości próbek nie pozwalają wyliczyć porównywalnego wyniku speedtestu Pi, ale różnica wyklucza uznanie obecnego wyniku PiTalka za normalne ograniczenie tej SIM do około 1,4 kB/s.

Karta ma dostęp do szybkiego LTE w telefonie. Nie potwierdza to sprawności modemu, jego toru radiowego, zasilania ani identycznego pasma i ścieżki operatora. Nie ma podstaw, by przypisywać cały problem ogólnemu przeciążeniu stadionu albo niskiemu baud rate. Następny test powinien rozdzielić modem/sieć komórkową od sterownika i stosu IP Raspberry Pi, zamiast powtarzać te same pomiary szybkości. SIM pozostaje w telefonie, PiTalk został wcześniej prawidłowo wyłączony.

## Ookla Speedtest CLI — próby po powrocie SIM

Zainstalowano oficjalny Speedtest CLI 1.2.0.84 aarch64. Po jednej udanej operacji odblokowania znanym PIN-em połączono USB/QMI; liczba dostępnych prób PIN pozostała 3. Modem automatycznie wybrał LTE B1, EARFCN 225, szerokość 15 MHz. Zmierzono RSRP −51 dBm, RSRQ −7 dB i SNR 18,4 dB. To inne pasmo niż wcześniejsze B3, co ogranicza bezpośrednie porównywanie prób sprzed restartu.

Pierwsze uruchomienie miało sprzeczne opcje --interface i --ip; zostało odrzucone przed transmisją. Poprawne próby z samym --interface=wwan0 i osobno z samym adresem IPv4 kończyły się po około 19 s błędami odczytu. Sprawdzenie DNS zwracało prawidłowe rekordy, a example.com nadal odpowiadało przez modem. Lista serwerów Ookla została pobrana poprawnie.

Następnie wybrano konkretny serwer T-Mobile Polska S.A. w Krakowie, ID 23123, kra1.t-mobile.pl:8080. Przed testem sprawdzono, że jedyną trasą domyślną jest wwan0; metadane klienta również potwierdziły wwan0 i T-Mobile Polska. Próbki postępu pobierania: 1086, 1196, 1162 i 1777 B/s, czyli około 0,0087–0,0142 Mb/s. Po 11,59 s klient zakończył działanie z błędem Cannot read. **Brak końcowego wyniku download i upload.** Nie przedstawiamy tych wartości jako ukończonego Speedtestu ani jako 0 Mb/s.

Łączny przyrost liczników wwan0 w trzech sieciowych próbach klienta wyniósł około 0,231 MB (RX+TX). To liczniki interfejsu, nie rozliczenie operatora. Błędy interfejsu i get_throttled pozostały zerowe. Wyniki uzasadniają dalszą diagnozę wolnej/niestabilnej transmisji; nie ustalają jeszcze przyczyny. Wcześniejsze 1,4 kB/s pochodziło z curl i oznaczało kilobajty, nie kilobity, na sekundę. Metodę, przeliczenia i ograniczenia opisuje rozdział 04.

Logi: 42 (instalacja), 43 (nieprawidłowe połączenie opcji i stan radia), 44–45 (próby przypisania interfejsu/adresu), 46 (lista serwerów), 47 (test T-Mobile i osobny plik summary.json).

## HTTP w pamięci modemu i przywrócenie połączenia — 3 października 2026, do 17:40

Po nieudanych próbach Ookla zbadano klient HTTP samego EG25-G. Odczytano jego konfigurację przy rozłączonym profilu USB i zatrzymanym ModemManagerze (log 48). Kontrolny curl na Pi pobrał 16 KiB HTTP w 8,316 s. Pierwsza próba wewnętrznego HTTPGET otrzymała HTTP 200 i deklarowaną długość 16 384 B, ale odczyt ciała nie zakończył się potwierdzonym sukcesem; szczegółowego kodu tego błędu nie zapisano (log 49).

Powtórzono pobranie przez QHTTPREADFILE do własnego pliku RAM modemu. Nagłówki przyszły po 0,338 s. Po 30,806 s otrzymano kod 702 (timeout HTTP); QFLST pokazał rzeczywisty rozmiar 10 549 z oczekiwanych 16 384 B. Plik nie był przesyłany do Pi (log 50). Tym samym niepełne pobranie wystąpiło również bez stosu IP, qmi_wwan, nftables Pi i bez fizycznego UART. Nie ustalono, czy przyczyna leży w firmware, radiu, zasilaniu czy obsłudze modemu przez operatora.

Po obu próbach wykonano cleanup: zakończenie HTTP, dezaktywacja wewnętrznego kontekstu i przywrócenie jego oryginalnego typu/APN/pustych danych uwierzytelniających, potwierdzone odczytem. Własny plik z RAM usunięto. ModemManager, profil tmobile-pitalk-usb i pi-router-wan uruchomiono ponownie. Nie było operacji na SIM/PIN-ie ani zmian firmware, pasm i IMS.

Końcowa kontrola (log 51): aktywny profil USB i SSH, jedyna trasa domyślna przez wwan0, zbiór WAN nftables zawiera wwan0, LTE B1 / kanał 225 / 15 MHz, ping 2/2 do 1.1.1.1, get_throttled=0x0. Zakończono z przywróconym połączeniem; poprawy prędkości ani aktualnego pełnego toru do iPhone’a nie potwierdzono. Następny test wymaga przeniesienia zestawu do innego dostępnego miejsca bez jednoczesnej zmiany kabli, anteny i zasilania.

## Zmiana miejsca na stadionie — pomiar 3 października 2026, 17:57–17:58

**Nie potwierdzono poprawy.** Użytkownik przeniósł zestaw do miejsca skierowanego bezpośrednio ku antenie GSM. Przed testem modem był wykryty, ale profil LTE pozostawał rozłączony. Następnie chwilowo zniknęło SSH, a po jego powrocie uptime Pi wynosił mniej niż minutę. Potwierdza to restart Pi; nie ustalono, czy użytkownik odłączał kabel, czy restart był niezamierzony.

Modem wymagał ponownie SIM PIN. Wykonano jedną udaną próbę z wcześniej podanym PIN-em; nadal dostępne są 3 próby. Nie zapisano PIN-u ani nie zmieniono zabezpieczeń. Zegar Pi po starcie nie był zsynchronizowany; ustawiono go z Maca. Połączono istniejący profil tmobile-pitalk-usb i odświeżono WAN routera do wwan0.

| Pomiar | Poprzednie miejsce | Nowe miejsce |
|---|---|---|
| Ookla, T-Mobile Kraków ID 23123 | Próbki postępu 1086–1777 B/s, błąd Cannot read | Jedna próbka 462 B/s, błąd Cannot open socket po 12,46 s |
| Końcowy download/upload Ookla | Brak pełnego wyniku | Brak pełnego wyniku |
| curl, HTTP httpbingo.org/bytes/16384 | 16 384 B w 8,316 s, około 1970 B/s (log 49) | 16 384 B w 11,734 s, 1396 B/s (log 54) |
| Ping do 1.1.1.1, nowa próba | — | 3/3 odpowiedzi, średnio 31,392 ms |

Próbki postępu Ookla nie są ukończonym wynikiem Speedtestu. Obie próby użyły tego samego serwera i interfejsu wwan0; przed nową próbą zweryfikowano jedyną trasę domyślną przez modem, a metadane Ookla potwierdziły operatora i interfejs. Przyrost liczników podczas samego Speedtestu: RX 20 523 B, TX 35 047 B; łącznie 55 570 B. Nie jest to rozliczenie operatora.

Radio nadal LTE B1 / EARFCN 225 / 15 MHz. Po ponownym połączeniu RSRP −56 dBm, RSRQ −10 dB, SNR 9,8 dB. Bezpośrednio przed Speedtestem: −57 dBm, −7 dB, 30 dB; po pomiarach: −54 dBm, −7 dB, 13,8 dB. Wstępny odczyt SNR 9,8 dB nie opisuje całego pomiaru. Nawet przy chwilowym odczycie SNR 30 dB problem pobierania pozostał.

Liczniki błędów i odrzuceń wwan0 nie wzrosły; get_throttled=0x0. To nie dowodzi stabilności zasilania modemu ani nie wyjaśnia wcześniejszego restartu. Nowy test nie izoluje wyłącznie miejsca: przed nim nastąpił restart, ponowne odblokowanie SIM i nowa sesja danych z innym adresem WAN. Nie stwierdzamy na tej podstawie, że przeniesienie pogorszyło transfer; stwierdzamy brak oczekiwanej poprawy.

Po teście Pi, SSH i profil USB/QMI pozostały aktywne, z trasą domyślną przez wwan0. Przed pomiarem Ethernet miał carrier=0, więc nie był to test całej ścieżki do iPhone’a. Logi: `52-location-comparison-baseline.txt`, `53-location-reconnect.txt`, `54-location-speedtest.txt`, `54-location-summary.json`. Do wyjaśnienia przed kolejną zmianą konfiguracji: czy restart podczas przenoszenia był zamierzony.


## PiTalk bezpośrednio do MacBooka — brak zasilania, 3 października 2026

Użytkownik przełączył modem z Pi do MacBooka i zgłosił brak diody zasilania. macOS wykrywa huby GenesysLogic i adapter Ethernet ASIX, ale nie Quectel (VID 0x2c7c); brak nowych portów szeregowych modemu. Nie potwierdzono napięcia pomiarem elektrycznym, dlatego brak enumeracji USB sam nie dowodzi braku 5 V. Zgłoszenie braku świecenia pochodzi od użytkownika. Log: `logs/55-modem-direct-mac-detection.json`.

W [schemacie producenta PiTalk V1.1, strona 2](https://github.com/sbcshop/Pitalk_4G_HAT_Hardware/blob/main/Design%20Data/Schematic_PiTalk_4G.pdf) piny CC1/A5 i CC2/B5 gniazda J1 są niepodłączone. Brak zaznaczonych rezystorów Rd do masy. Według [TI — USB Type-C](https://www.ti.com/lit/SLYY228) odbiornik 5 V wymaga sygnalizacji na CC (np. osobnych Rd 5,1 kΩ). To uzasadnia hipotezę, że taki wariant płytki nie uruchamia zasilania z połączenia C–C. Nie potwierdzono rewizji fizycznej płytki użytkownika ani jeszcze typu użytego kabla. Nie przypisujemy tej hipotezie wcześniejszego wolnego LTE zasilanego przez USB-A Raspberry Pi.

Następna próba: Mac → hub/adapter z USB-A → wcześniej sprawdzony kabel danych USB-A–USB-C → PiTalk, bez dodatkowego zasilania GPIO. Najpierw sprawdzić diodę zasilania; dopiero po jej zapaleniu uruchomić moduł przyciskiem PWRKEY przez 3–4 sekundy, zgodnie z [instrukcją PiTalk](https://github.com/sbcshop/Pitalk_4G_HAT_Software). Następnie ponownie sprawdzić enumerację USB. Nie instalowano sterowników, nie zmieniano ustawień modemu, sieci Maca ani SIM. Bez wykrytego urządzenia nie ma portu sterującego do programowego uruchomienia modemu. Internet bezpośrednio przez modem na macOS nie został jeszcze uruchomiony ani przetestowany.

Kopia schematu: `references/Schematic_PiTalk_4G.pdf`. Status: oczekiwanie na wynik fizycznego podłączenia przez USB-A.

## Test PiTalk bezpośrednio na MacBooku — 18:07–18:25

Po podłączeniu przez hub USB-A modem został wykryty i odpowiadał przez bezpośredni USB AT. Zapisano stan wyjściowy, przetestowano ECM i APN internet dla kontekstu 1. macOS utworzył en12, DHCP i ping do modemu działały, ale modem zwracał Destination Net Unreachable dla Internetu, również po restarcie. Główna trasa Maca pozostała przez en9. Wewnętrzny HTTP do RAM zakończył się timeoutem z 10 737 z 16 384 B. Pełna procedura i ograniczenia w rozdziale 06; logi 55–67.

## Wynik końcowy i powrót do konfiguracji Raspberry Pi

Próba HTTP z wewnętrznego klienta EG25-G, przy zasilaniu i sterowaniu z MacBooka, również nie zakończyła się pełnym pobraniem: nagłówki HTTP 200 po 0,293 s, a po 31,686 s błąd 702 (timeout HTTP). Plik w RAM modemu miał 10 737 z deklarowanych 16 384 B. Treść pliku nie była przesyłana przez USB do Maca. Wynik reprodukuje niepełne pobranie bez Raspberry Pi i jego zasilania; nie potwierdza pełnej sprawności kabla jako źródła zasilania ani nie izoluje firmware od radia i sieci operatora. Nie jest to Speedtest na Macu ani pomiar maksymalnej przepustowości. Kod 702 opisuje [instrukcja Quectel HTTP(S), rozdział 5](https://forums.quectel.com/uploads/short-url/kxS3asnEWfTxweAAYcLiomJakDE.pdf).

Po teście zakończono HTTP, usunięto własny plik z RAM i zdezaktywowano wewnętrzny kontekst. Następnie czasowo wyłączono radio przez CFUN=0, odtworzono oryginalny kontekst 1 (IPV4V6, pusty APN i dane uwierzytelniające), ustawiono usbnet=0 i ponownie włączono radio (CFUN=1). Odczyt potwierdził oba ustawienia. Ponowny odczyt deskryptorów USB potwierdził powrót interfejsu 4 do klasy vendor-specific QMI; nie pozostawiono modemu w ECM.

**Stan końcowy, 18:25:** modem nadal fizycznie podłączony do Maca przez hub USB-A, wykryty i odpowiada na AT; QMI przywrócone. Brak aktywnego wewnętrznego kontekstu danych. SIM po ponownym włączeniu radia wymaga PIN-u, ma 3 dostępne próby; nie wysyłano PIN-u ponownie na końcu. W trakcie testu Maca były dwie udane operacje odblokowania (przed i po restarcie), razem sześć udanych operacji w całej dotychczasowej sesji. Zabezpieczenia SIM pozostały włączone, PIN nie jest zapisany.

Internet Maca pozostał przez pierwotny Ethernet en9. Usługa sieciowa EG25-G, utworzona automatycznie przez macOS podczas ECM, może pozostać na liście jako nieaktywna; nie jest potwierdzeniem obecnego połączenia danych. W tej sesji nie zainstalowano ani nie uruchomiono Speedtestu na Macu, ponieważ ECM nie zapewnił połączenia do Internetu.

Do powrotu do routera należy fizycznie podłączyć modem z powrotem do USB-A Raspberry Pi, zapewnić osobne połączenie USB-C Pi–Mac do zasilania/SSH i uruchomić na Pi istniejący profil `sudo nmcli --ask connection up tmobile-pitalk-usb`. Po odłączeniu zasilania modemu może być potrzebne użycie przycisku Power i PIN-u. Konfiguracja Raspberry Pi nie była modyfikowana podczas testu na Macu.

Logi końcowe: `65-mac-internal-http.txt`, `66-mac-restore-qmi.txt`, `67-mac-final-state.txt`. Transport PyUSB używa tymczasowego venv zapisanego w `/tmp/pitalk-mac-usb-venv`; jego dostępność po restarcie Maca nie jest gwarantowana. Do powtórzenia tej zaawansowanej diagnostyki potrzebne są Python, PyUSB i libusb; nie jest wymagana do codziennej obsługi Pi przez SSH.

## Zgłoszenie problemu na Windowsie i analiza forum

Użytkownik potwierdził podobne timeouty/skrajnie wolną pracę również na Windowsie z zainstalowanymi sterownikami. Nie zebrano logów ani trybu połączenia Windows. Zapisano relację w logs/68-windows-user-report.json. Przeszukano forum Quectela, porównano wersje firmware i typy objawów; nie znaleziono potwierdzonej poprawki dla dokładnego 30.203.30.203 i naszych objawów. W rozdziale 07 zapisano źródła, rozróżnienie od różnic klas LTE oraz plan kontrolowanego testu innego operatora i szkic zgłoszenia. Nie wykonywano zmian sprzętu/ustawień ani nie wysłano wiadomości na zewnątrz.


## Zakres projektu — draft do komisji

[Wizja i plan rozwoju](08-WIZJA-I-PLAN-PROJEKTU.md) opisuje telefon po kablu z wyłączonymi radiami, planowany Tor z mostami, panel filtrów i komunikacji oraz miniaturyzację (PCB i CAD). To pierwotny zakres projektu; późniejszy stan panelu, CAD i demonstracji Tora opisuje [STATUS](docs/STATUS.md). [Krótki draft PDF](projekt/Draft-projektu.pdf).

3 października: użytkownik podał, że ten sam modem działał prawidłowo około roku temu na T-Mobile i Play przez USB na Windowsie. Test Plusa nadal niewykonany. Prace przeniesiono na draft projektu do komisji; nie zmieniano konfiguracji routera ani modemu.
