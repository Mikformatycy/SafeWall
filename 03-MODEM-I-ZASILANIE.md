# PiTalk, T-Mobile i zasilanie

> Zapis historyczny testów prototypu z 3 października 2026. Opis połączeń i wdrożeń odnosi się do czasu próby. Aktualny stan projektu, dashboardu i deklaracji dotyczących Tora: [STATUS](docs/STATUS.md). Surowe logi oraz kopie są lokalne.

## Stan potwierdzony

**Stan historyczny po teście Maca (3 października, 18:25): modem zasilany przez USB-A huba przy MacBooku, QMI przywrócone; nie jest obecnie połączony z Raspberry Pi.** USB i AT działają. ECM na Macu uzyskał DHCP, lecz nie przekazywał Internetu. Wewnętrzny HTTP modemu także zakończył się timeoutem. SIM wymaga PIN-u przy kolejnym uruchomieniu połączenia, licznik prób wynosi 3. Szczegóły: [test modemu na Macu](06-MODEM-NA-MACU.md).

PiTalk potwierdzono jako **Quectel EG25-G**. Skonfigurowany wariant danych to **USB/QMI** z profilem `tmobile-pitalk-usb`; wcześniejsze GPIO/UART/PPP zostało rozłączone i zachowane jako wariant zapasowy. Użytkownik następnie odłączył fizycznie GPIO i pozostawił sam USB do danych i zasilania modemu. W obu wariantach uzyskano Internet T-Mobile, ale nadal występują straty pakietów. Anteny i fizyczny przycisk Power zostały obsłużone przez użytkownika. Dokładna rewizja płytki HAT nadal nie jest odczytana; rodzinę modułu potwierdzono komendą `AT+CGMM`.

| Element | Aktualna konfiguracja |
|---|---|
| Port komunikacji | USB-C PiTalk → USB-A Pi; sterowanie `cdc-wdm0` |
| Transmisja | USB/QMI, sterownik `qmi_wwan`, interfejs IP `wwan0` |
| Operator | T-Mobile Polska, kod sieci `26002`, rejestracja w sieci macierzystej |
| Profil i APN | `tmobile-pitalk-usb`, APN `internet`, IPv4 |
| Karta prywatna | PIN wymagany; sześć udanych operacji odblokowania w całej sesji; ostatnia podczas testu Maca; po końcowym ponownym włączeniu radia SIM znów wymaga PIN-u; PIN niezapisany w profilu |

APN `internet` potwierdza [T-Mobile Polska](https://www.t-mobile.pl/c/jak-korzystac-z-internetu-w-telefonie). Połączenie oznaczono jako taryfowe (`connection.metered=yes`), z wyłączonym autopołączeniem i z `gsm.home-only=yes`. Oznaczenie taryfowe jest wskazówką dla aplikacji; nie stanowi limitu transferu ani blokady pobierania danych.

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

## Ponowne połączenie

1. Zapewnij anteny, zasilanie i kabel danych USB-C PiTalk → USB-A Pi. Jeśli modem jest wyłączony, uruchom go przyciskiem Power.
2. Z Maca otwórz `ssh pi-usb`.
3. Na Pi sprawdź `mmcli -L`, następnie uruchom:

   ```bash
   sudo nmcli --ask connection up tmobile-pitalk-usb
   ```

   Po utracie zasilania modemu może być potrzebny PIN. Wpisz poprawny PIN w interaktywnym pytaniu, bez umieszczania go w komendzie lub pliku. `gsm.pin-flags=2` oznacza, że sekret nie ma być trwale zapisany. Jeśli poprawnego PIN-u nie znasz, przerwij próbę; nie zgaduj.

4. Sprawdź połączenie:

   ```bash
   sudo pi-status
   dig @192.168.76.1 example.com +short +time=3 +tries=1
   curl -4 --interface wwan0 --head --max-time 25 https://example.com/
   ```

5. Aby zakończyć korzystanie z pakietu tej SIM:

   ```bash
   sudo nmcli connection down tmobile-pitalk-usb
   ```

Autopołączenie pozostaje wyłączone: profil nie ma sam inicjować połączenia na prywatnej SIM po kolejnym starcie. Nie wyłączano blokady PIN ani nie zmieniano PIN-u/PUK-u. Podczas poprawnego testu licznik prób PIN nadal wskazywał trzy dostępne próby.

## Bieżący wariant USB i wynik porównania

Drugi przewód USB-A → USB-C okazał się kablem danych: system wykrył urządzenie `2c7c:0125`, opis produktu `EG25-G`, porty `ttyUSB0–3`, sterowanie `cdc-wdm0` i interfejs `wwan0`. `lsusb` może nazywać ten współdzielony identyfikator „EC25”; nie oznacza to zmiany modelu potwierdzonego przez modem. Łącze USB zgłasza 480 Mb/s — to prędkość magistrali, nie test Internetu.

Profil `tmobile-pitalk-usb`, UUID `03f980ca-d08e-41f3-ac8a-5645d4562bda`, ma APN `internet`, `gsm.home-only=yes`, `gsm.pin-flags=2`, `connection.autoconnect=no`, `connection.metered=yes`, IPv4 z metryką 50 oraz wyłączone IPv6. Nie wpisywano ponownie PIN-u i nie zmieniano zabezpieczeń SIM. Profil UART `tmobile-pitalk` jest nieaktywny. ModemManager może pokazywać dwa wpisy tego samego fizycznego modemu: przez UART i USB; nie uruchamiaj obu profili naraz.

Router automatycznie zmienił zbiór `wan_ifaces` na `wwan0` oraz źródło DNS na połączenie USB. Adres WAN, brama i DNS są dynamiczne. Nie zmieniano reguł filtrowania ani dostępu SSH z Maca.

| Próba przez USB/QMI | Wynik |
|---|---|
| Mały ping do 1.1.1.1 | 5/5 odpowiedzi |
| Ping z 1252 B danych | 3/5 do 1.1.1.1 i 2/5 do 8.8.8.8 w próbie ze śladem pakietów |
| HTTPS example.com, pełna odpowiedź | 577 B, HTTP 200, około 3,15 s |
| HTTPS check.torproject.org, pełna odpowiedź | 7900 B, HTTP 200, około 7,63 s |
| Próba pobrania 64 KiB | 30 052 B w 20 s, timeout; około 1,5 kB/s licząc całe żądanie |

Straty występują także po ominięciu UART. W śladzie na `wwan0` brakujące odpowiedzi ICMP nie pojawiły się, a liczniki reguł `input` nie wzrosły. To wskazuje, że zapora Pi nie odrzuciła tych konkretnych odpowiedzi. Interfejs USB nie wykazał błędów ani porzuceń; `get_throttled=0x0`. Dalsza próba wolniej wysyłanego dużego ICMP również się nie powiodła, więc nie ustalono prostego, stabilnego limitu szybkości.

**Nie ustalono dokładnej przyczyny:** niski baud rate ograniczał UART, lecz nie wyjaśnia strat widocznych również przez USB. Wciąż trzeba rozdzielić zachowanie modemu/toru radiowego od operatora i warunków pakietu SIM. Nie uznano samej siły sygnału ani `get_throttled=0x0` za dowód pełnej sprawności modemu.

W czasie pomiarów USB port Ethernet miał `carrier=0`, więc były to testy z samego Pi. Wcześniejszy test iPhone’a przez UART nie jest potwierdzeniem pełnego połączenia iPhone’a przez nowy WAN USB. Po ponownym podłączeniu adaptera telefonu należy sprawdzić DHCP oraz stronę HTTPS z iPhone’a.

Powrót do wariantu UART bez usuwania konfiguracji USB, na Pi — dopiero po ponownym zapewnieniu właściwego połączenia GPIO przy wyłączonym sprzęcie:

```bash
sudo nmcli connection down tmobile-pitalk-usb
sudo nmcli --ask connection up tmobile-pitalk
```

Powrót do USB wykonaj odwrotnie: rozłącz `tmobile-pitalk`, następnie uruchom `sudo nmcli --ask connection up tmobile-pitalk-usb`. Dla testu całkowicie bez USB odłącz przewód modemu po rozłączeniu jego profilu, pozostawiając zasilanie Pi z Maca. Nie zmieniaj przy tym PIN-u ani baudrate.

Logi: `24-modem-usb-cable-check.txt` (pierwszy kabel bez wykrycia), `25-usb-qmi-comparison.txt`, `26-usb-errors-firewall.txt`, `27-usb-packet-loss-location.txt`, `28-usb-paced-packets.txt`. Kopia nowego profilu bez sekretów znajduje się w `config/tmobile-pitalk-usb.nmconnection`. Kopie sprzed dodania USB zapisano na Pi w `/root/pi-usb-modem-backup-20261003/`.

## Jakość odbioru LTE i hipoteza przeciążenia stadionu

3 października 2026, około 16:01–16:07, wykonano odczyty diagnostyczne przez USB/QMI. Użytkownik potwierdził następnie, że ta sama SIM działała sprawnie tego dnia na tym stadionie w telefonie, przy wyłączonym Wi-Fi, przez LTE. To obserwacja użytkownika, nie jednoczesny pomiar obu urządzeń. Nie ustalono pasma ani komórki używanej wtedy przez telefon. Ogólny tłok na stadionie nie wystarcza więc jako wyjaśnienie problemu PiTalka.

| Parametr | Odczyt | Znaczenie |
|---|---|---|
| Technologia/pasmo | LTE, `eutran-3`, kanał 1575, szerokość 15 MHz | Aktualnie używane pasmo modemu; bez ręcznej blokady pasma |
| RSRP | −59 do −58 dBm | Bardzo mocny odbierany sygnał LTE |
| RSRQ | −7 dB | Dobry parametr jakości odbioru |
| SNR według ModemManager/QMI | 16,4 do 30 dB | W próbkach dobry stosunek sygnału do szumu |
| RSSI | −35 do −32 dBm | Silny całkowity odbierany sygnał; sam RSSI nie wystarcza do diagnozy |

Są to trzy próbki ModemManagera oraz dodatkowy odczyt QMI, nie długoterminowy test radia. **Nie wskazują na słaby odbiór ani silne, ciągłe zakłócenia w zmierzonym torze odbiorczym.** Nie obejmują pełnej jakości nadawania modemu i nie pokazują obciążenia stacji bazowej. Dobry odbiór nie gwarantuje dużej przepustowości. Przeciążenie sieci na stadionie pozostaje możliwą przyczyną, lecz nie zostało potwierdzone. Nie uznano lokalnego tłoku Wi-Fi za dowód zakłócania używanego pasma LTE.

Interpretacja parametrów i ograniczeń: [Teltonika — siła i jakość sygnału komórkowego](https://wiki.teltonika-networks.com/view/Mobile_Signal_Strength_Recommendations). EG25-G jest modemem [LTE Cat 4](https://www.quectel.com/product/lte-eg25-g/); według użytkownika telefon również korzystał z LTE. Jego pasmo, komórka i ewentualna agregacja pasm nie zostały ustalone.

Odczyt QMI potwierdził MTU 1500, zgodne z interfejsem `wwan0`, oraz te same adresy bramy/DNS co NetworkManager. Liczniki QMI zgłaszały 0 pakietów TX/RX dropped. Nie jest to dowód braku strat w sieci operatora — wcześniejsze testy wykazały brakujące odpowiedzi. Raportowane maksima kanału 150/50 Mb/s są wartościami możliwości, a nie zmierzonym transferem ani potwierdzeniem przydziału tej przepustowości. Odczyt chwilowy 0 b/s nie oznacza sam w sobie awarii bez aktywnego transferu.

Do pomiarów użyto wyłącznie odczytów QMI przez działający `qmi-proxy`. ModemManagerowi włączono na kilkanaście sekund odświeżanie sygnału co 5 s, po czym przywrócono wcześniejszą wartość 0. Nie zmieniano pasm, APN, parametrów SIM, PIN-u ani firmware; nie resetowano modemu. Aktywny profil nadal to `tmobile-pitalk-usb`.

Logi: `logs/29-usb-lte-radio-quality.txt`, `logs/30-usb-qmi-radio-and-channel.txt`, `logs/31-usb-bearer-settings.txt`. Później potwierdzono pojedynczą antenę w GSM ANT i ponowiono sesję LTE; wynik opisano poniżej. Nie uznajemy przeciążenia za ustalony fakt.

## Tory antenowe i wersja firmware — odczyt 16:10

Trzy odczyty `qmicli --device=/dev/cdc-wdm0 --device-open-proxy --nas-get-tx-rx-info=lte` wykazały moc w torze RX0 od −37,8 do −32,2 dBm, a w RX1 od −62,6 do −58,0 dBm: około 25 dB różnicy. Może to wynikać z anten, ich ułożenia lub warunków odbioru; samo w sobie nie dowodzi uszkodzenia ani przyczyny wolnego transferu. Użytkownik potwierdził jedną antenę z zestawu w gnieździe `GSM ANT`, bez anteny dodatkowej. Jest to zgodne z podstawowym sposobem uruchamiania PiTalka z anteną 4G opisanym przez [producenta HAT-a](https://github.com/sbcshop/Pitalk_4G_HAT_Software#setup-pitalk-4g-via-usb). Brak drugiej anteny jest możliwym wyjaśnieniem asymetrii torów, ale nie potwierdzoną przyczyną transferu około 1,4 kB/s. Producent rozróżnia antenę główną, dodatkowy odbiór oraz GNSS w [EG25-G Hardware Design](https://quectel.com/content/uploads/2021/03/Quectel_EG25-G_Hardware_Design_V1.4.pdf). Podczas tych odczytów nie przepinano anten ani nie wyłączano diversity komendami. Późniejszą krótką próbę ustawienia toru głównego opisano niżej.

Pole `RSRP` w tym konkretnym odczycie QMI zostało wydrukowane bez minusa, w przeciwieństwie do poprawnie ujemnego RSRP w `--nas-get-signal-info`. Nie interpretujemy tych dodatnich liczb jako rzeczywistej dodatniej mocy RSRP. Porównanie powyżej używa jawnego pola `Power`.

Dwie próbki z aktywnym nadawaniem pokazały −28 i −21 dBm, więc w tych chwilach modem nie nadawał z maksymalną mocą. Mały ping z danymi 64 B uzyskał 16/16 odpowiedzi; po pierwszej odpowiedzi 225 ms kolejne trwały 24–39 ms. Nie jest to test przepustowości ani dowód usunięcia wcześniej wykrytych strat większych pakietów.

Odczyt `--dms-get-revision` zwrócił bazowe `EG25GGBR07A08M2G`. Późniejszy odczyt AT potwierdził pełną wersję `EG25GGBR07A08M2G_30.203.30.203` (log 37); jest inna niż podwersja 01.003 ze wspomnianego niżej zgłoszenia. Na [forum producenta](https://forums.quectel.com/t/eg25-frequent-disconnects-dropped-packets/18433) występuje zgłoszenie strat pakietów z tą samą bazową wersją, lecz nie dowodzi ono wspólnej przyczyny ani skuteczności aktualizacji w naszym zestawie. Firmware nie zmieniano.

Log: `logs/32-usb-radio-chains.txt`. PIN i ustawienia SIM pozostały bez zmian; aktywny profil to nadal USB/QMI.

## Jedna antena i ponowienie sesji — około 16:27–16:30

Użytkownik ma jedną dołączoną antenę w `GSM ANT`. Podczas pierwszego odświeżenia sesji nie przepinano jej do GNSS ani nie zmieniano ustawień diversity. Dokumentacja Quectela dopuszcza pozostawienie nieużywanego ANT_DIV bez połączenia; sam brak drugiej anteny nie rozstrzyga przyczyny timeoutów.

Przed zmianą mały ping uzyskał 3/3, duży (1252 B danych) 4/4 odpowiedzi. Pobranie 16 KiB przez HTTPS zajęło 11,07 s (1480 B/s). Następnie rozłączono wyłącznie profil `tmobile-pitalk-usb`, wykonano `mmcli --disable` i `--enable` dla obiektu USB oraz ponownie połączono ten sam profil. Nie wykonywano resetu fabrycznego ani aktualizacji firmware. SSH przez USB gadget działało przez całą próbę.

Po ponowieniu sesji: mały ping 3/3, duży 4/4, 16 KiB w 11,39 s (1438 B/s). Odświeżenie nie usunęło problemu szybkości. Krótkie próbki dużego pingu tym razem nie wykazały strat, w przeciwieństwie do wcześniejszych pomiarów. Nie należy więc traktować wcześniejszego procentu strat jako stałej wartości.

Połączenie USB zostało przywrócone. Bezpośrednio po `nmcli up` zbiór WAN był jeszcze pusty; kolejny odczyt po obsłudze zdarzeń NetworkManagera potwierdził `wan_ifaces = { wwan0 }`, poprawne DNS i działające usługi routera. Ethernet telefonu nadal miał `carrier=0`.

PIN nie był ponownie wysyłany, liczba dostępnych prób pozostała bez zmian. Widoczne w odczycie ModemManagera `sim-pin2` nie blokowało połączenia danych; nie podejmowano prób PIN2. Profil zachował brak autopołączenia, brak zapisanego PIN-u, tryb taryfowy i ograniczenie do sieci macierzystej.

Odczyt QMI potwierdził faktyczny APN przyłączenia `internet`, IPv4 i wykonaną rejestrację. Odczyt ustawień domyślnych modemu zawierał inne APN `INTERNET.TELEKOM`; nie utożsamiamy go z aktywną sesją i nie zmieniano go. QMI zgłosił brak obsługi odczytywanego interfejsu QoS w sieci; nie dowodzi to braku ograniczania szybkości przez operatora.

Logi: `33-before-session-refresh.txt`, `34-usb-session-refresh.txt`, `35-usb-lte-attach-settings.txt`. Dokładna przyczyna pozostaje nieustalona.

## Opóźnienia TCP i próba ustawienia odbiornika z jedną anteną

Ślad TCP podczas pobrania 16 KiB pokazał brakujące zakresy sekwencji, odpowiedzi SACK i kolejne brakujące dane dostarczane po około 0,7 s. Pełne żądanie trwało 11,10 s: zestawienie TCP 0,035 s, zakończenie TLS 0,879 s, pierwszy bajt HTTP 1,938 s. Test używał znanego adresu przez `curl --resolve`, więc nie czekał na zapytanie DNS. To wskazuje na straty lub opóźnienia danych na ścieżce, ale ślad z samego Pi nie wskazuje, czy przyczyna jest w modemie, radiu czy dalszej sieci. Kolejka `fq_codel` na `wwan0` nie zgłaszała odrzuceń; liczniki odrzuceń input nftables nie wzrosły. Log 36 zawiera wyłącznie nagłówki pakietów, bez treści strony.

Przy zatrzymanym ModemManagerze i rozłączonym profilu USB odczytano przez port AT `ttyUSB2` ustawienie `AT+QCFG="divctl","lte"`: wartość 0. `AT+CGEQOSRDP` zwróciło samo OK bez parametrów — nie ustalono na tej podstawie przyznanego limitu szybkości. Odczyt kontekstów potwierdził APN internet i osobny kontekst IMS; żadnego nie modyfikowano. Odczytano pełną wersję firmware, przywrócono ModemManager i profil USB. Numer obiektu modemu zmienił się po ponownym wykryciu: identyfikuj urządzenie przez `mmcli -L` i port `cdc-wdm0`, nie zakładaj stałego numeru 0/1.

Następnie wykonano porównanie opisanej przez [Quectela komendy divctl, sekcja 3.11](https://forums.quectel.com/uploads/short-url/3lWW1QdfI21dJ7b4lqgIKrUDLro.pdf):

| Ustawienie LTE | Potwierdzenie AT przed połączeniem | Pobranie 16 KiB HTTPS |
|---|---|---|
| Sam tor główny, `divctl=1` | Odczyt zwrócił 1 | 11,50 s, 1424 B/s |
| Oryginalne oba tory, `divctl=0` | Odczyt po cofnięciu zwrócił 0 | 11,28 s, 1452 B/s |

**Stan końcowy: przywrócono oryginalne `divctl=0`; nie pozostawiono eksperymentalnego ustawienia.** Przy każdej operacji AT ModemManager był zatrzymany, a później uruchomiony i profil USB ponownie połączony. Modem przyjął ustawienie 1, lecz QMI nadal pokazywał `Radio tuned: yes` dla obu torów; odczyt ten nie potwierdza fizycznego wyłączenia toru dodatkowego. Próba nie wykazała poprawy; nie wyklucza to wszystkich problemów antenowych. Nie ma podstaw, by obiecywać naprawę przez zakup drugiej anteny.

Nie wykonywano `AT&W`, aktualizacji firmware, zmiany pasm ani zabezpieczeń SIM. WAN nftables po zakończeniu: `wwan0`. Logi: `36-usb-tcp-timing.txt`, `37-modem-antennas-eps-readonly.txt`, `38-single-antenna-comparison.txt`.

Następny miarodajny test wymaga porównania tej samej SIM w telefonie teraz, z wyłączonym Wi-Fi, a nie tylko wcześniejszej obserwacji z tego dnia. Najpierw trzeba zakończyć pracę modemu przed fizycznym wyjęciem SIM; nie inicjowano tej operacji bez uzgodnienia momentu z użytkownikiem.

## Ostatni test: fizycznie odłączone GPIO, tylko USB, po restarcie

Użytkownik odłączył PiTalk od GPIO, pozostawił USB-A Pi → USB-C modemu i zrestartował modem. Test wykonano przed przeniesieniem SIM do telefonu. USB wykryło EG25-G, lecz SIM ponownie wymagała PIN-u. Wykonano jedną udaną próbę z wcześniej podanym PIN-em; licznik dostępnych prób pozostał 3. To druga udana operacja odblokowania w całej konfiguracji, nie ponawianie błędnego PIN-u. Sekret nie trafił do dokumentacji ani profilu.

Połączono `tmobile-pitalk-usb`; operator przydzielił nowy prywatny adres WAN `100.69.238.211` i bramę `100.69.238.212`. Są dynamiczne. Pomiary:

| Próba | Wynik |
|---|---|
| Ping 64 B danych | 3/3, średnio 26,7 ms |
| Ping 1252 B danych | 4/4, średnio 35,8 ms |
| Pobranie 16 KiB HTTPS | HTTP 200, 11,42 s, 1435 B/s |
| example.com | HTTP 200, 577 B, 3,46 s |
| Zasilanie Pi / Ethernet telefonu | get_throttled=0x0; eth0 carrier=0 |

Brak zauważalnej poprawy względem 1,4–1,5 kB/s przed zmianą. Połączony profil oraz WAN nftables działały. Próbka sygnału: RSRP −61 dBm, RSRQ −7 dB, SNR 4,4 dB — SNR był niższy od wcześniejszych próbek; pojedynczy odczyt nie wystarcza do przypisania przyczyny. Samo fizyczne odłączenie GPIO i restart nie usunęły objawu. Ponieważ obie czynności wykonano razem, test nie rozdziela ich wpływu. Log: `39-usb-only-after-hardware-restart.txt`.

Po ostatnim teście powrócono do wcześniej uzgodnionego porównania SIM w telefonie. Rozłączono profil, zatrzymano ModemManager na czas dostępu do portu AT i wysłano normalne wyłączenie `AT+QPOWD=1`. Otrzymano `OK` oraz `POWERED DOWN`, a urządzenie modemu zniknęło z USB. Następnie uruchomiono ModemManager ponownie. Nie odłączano zasilania Raspberry Pi. Zbiór WAN nftables jest celowo pusty, brak trasy domyślnej; USB administracyjne i SSH działają. Log: `40-modem-off-for-phone-sim-test.txt`.

Karta może teraz zostać przełożona do telefonu. Do porównania użyj danych komórkowych tej SIM w LTE, przy wyłączonym Wi-Fi i odłączonym adapterze Ethernet. Później użytkownik potwierdził szybkie LTE w iPhonie 16: 73,9 Mb/s pobierania i 55,1 Mb/s wysyłania; szczegóły poniżej. Poprzedni plan wyłączenia został wstrzymany na prośbę użytkownika; wyłączenie wykonano dopiero po opisanym ostatnim teście USB.


## Porównanie tej samej SIM w iPhonie 16 — 3 października 2026

Po wyłączeniu modemu i przełożeniu tej samej prywatnej SIM użytkownik zgłosił wynik na iPhonie 16 przez LTE: **73,9 Mb/s pobierania i 55,1 Mb/s wysyłania**. To pomiar podany przez użytkownika, bez niezależnego odczytu aplikacji, identyfikatora komórki/pasma i serwera testowego. Poprzedzająca próba PiTalka wyłącznie po USB dała 1435 B/s przy pobraniu 16 KiB w 11,42 s. Różne narzędzia i wielkości próbek nie pozwalają wyliczyć porównywalnego wyniku speedtestu Pi, ale różnica wyklucza uznanie obecnego wyniku PiTalka za normalne ograniczenie tej SIM do około 1,4 kB/s.

Karta ma dostęp do szybkiego LTE w telefonie. Nie potwierdza to sprawności modemu, jego toru radiowego, zasilania ani identycznego pasma i ścieżki operatora. Nie ma podstaw, by przypisywać cały problem ogólnemu przeciążeniu stadionu albo niskiemu baud rate. Następny test powinien rozdzielić modem/sieć komórkową od sterownika i stosu IP Raspberry Pi, zamiast powtarzać te same pomiary szybkości. Na etapie porównania SIM była w telefonie, a PiTalk pozostawał wyłączony. Następnie użytkownik zwrócił kartę do modemu; dalsze pomiary opisano poniżej.

## Test klienta HTTP wewnątrz modemu — wykonany

**Niepełny transfer wystąpił również w samym EG25-G.** Modem pobierał publiczny plik 16 KiB z `http://httpbingo.org/bytes/16384` bezpośrednio do własnej pamięci RAM. Ruch TCP/IP tej próby nie przechodził przez sterownik qmi_wwan, stos sieciowy ani nftables Raspberry Pi. Port AT przez USB służył do sterowania; ciało odpowiedzi nie było przesyłane do Pi. Nie używano fizycznego GPIO/UART.

| Próba | Wynik |
|---|---|
| curl na Pi przez wwan0, ten sam adres | HTTP 200, pełne 16 384 B w 8,316 s, około 1970 B/s |
| Pierwszy wewnętrzny HTTPGET/HTTPREAD | HTTPGET zgłosił 200 i długość 16 384 B; odczyt ciała nie zakończył się potwierdzonym sukcesem; ta próba nie zapisała szczegółowego kodu błędu ani liczby odebranych bajtów |
| Powtórzenie HTTPGET/HTTPREADFILE do RAM modemu | Nagłówki po 0,338 s; po 30,806 s błąd 702; plik w RAM miał tylko 10 549 z 16 384 B |

Kod 702 oznacza timeout HTTP(S), zgodnie z [instrukcją Quectel HTTP(S), rozdział 5](https://forums.quectel.com/uploads/short-url/kxS3asnEWfTxweAAYcLiomJakDE.pdf). Sam komunikat HTTP 200 z HTTPGET nie dowodzi pobrania całego ciała; sprawdzono rzeczywisty rozmiar pliku w RAM. Dostępność pełnego pliku potwierdzono też osobno z Maca, ale nie traktujemy połączenia Maca jako pomiaru tej SIM.

**Wniosek:** problemu nie wystarcza tłumaczyć samym baud rate, sterownikiem lub firewallem Pi. Niepełne pobranie występuje również przy ominięciu całego tego toru. Próba nie rozstrzyga między firmware modemu, jego torem radiowym, zasilaniem i obsługą urządzenia przez sieć operatora; nie dowodzi też, że każdy wcześniejszy timeout miał dokładnie tę samą przyczynę. Następny kontrolowany test to zmiana miejsca przy zachowaniu tego samego sprzętu i zasilania.

Przed bezpośrednim AT rozłączono profil USB i zatrzymano ModemManager. Odczytano istniejące ustawienia; wewnętrzny kontekst 1 był nieaktywny i miał konfigurację `3,"","","",0`. Na czas prób ustawiono IPv4/APN internet, bez loginu i hasła. Po każdej próbie zakończono HTTP, zdezaktywowano kontekst, przywrócono dokładnie oryginalną konfigurację i potwierdzono odczytem. Własny plik diagnostyczny usunięto z RAM modemu. Następnie uruchomiono ModemManager, profil USB i odświeżono WAN routera. Nie zmieniano SIM/PIN-u, firmware, pasm ani IMS.

**Stan po testach, 17:40:** aktywne USB/QMI, trasa domyślna przez wwan0, zbiór WAN nftables zawiera wwan0, LTE B1 / EARFCN 225 / 15 MHz. Ping do 1.1.1.1 odpowiedział 2/2; `get_throttled=0x0`. SSH przez USB-C działa. To potwierdza przywrócenie dostępu, nie poprawę przepustowości ani aktualny test iPhone’a przez Ethernet.

Logi: `48-internal-http-capabilities.txt`, `49-internal-http-comparison.txt`, `50-modem-internal-http-ram.txt`, `51-restored-after-speedtest-http.txt`. To opis wykonanego eksperymentu; nie wysyłaj samodzielnie komend AT na port zajęty przez ModemManager.

## Ookla Speedtest CLI — próby po powrocie SIM

Zainstalowano oficjalny Speedtest CLI 1.2.0.84 aarch64. Po jednej udanej operacji odblokowania znanym PIN-em połączono USB/QMI; liczba dostępnych prób PIN pozostała 3. Modem automatycznie wybrał LTE B1, EARFCN 225, szerokość 15 MHz. Zmierzono RSRP −51 dBm, RSRQ −7 dB i SNR 18,4 dB. To inne pasmo niż wcześniejsze B3, co ogranicza bezpośrednie porównywanie prób sprzed restartu.

Pierwsze uruchomienie miało sprzeczne opcje --interface i --ip; zostało odrzucone przed transmisją. Poprawne próby z samym --interface=wwan0 i osobno z samym adresem IPv4 kończyły się po około 19 s błędami odczytu. Sprawdzenie DNS zwracało prawidłowe rekordy, a example.com nadal odpowiadało przez modem. Lista serwerów Ookla została pobrana poprawnie.

Następnie wybrano konkretny serwer T-Mobile Polska S.A. w Krakowie, ID 23123, kra1.t-mobile.pl:8080. Przed testem sprawdzono, że jedyną trasą domyślną jest wwan0; metadane klienta również potwierdziły wwan0 i T-Mobile Polska. Próbki postępu pobierania: 1086, 1196, 1162 i 1777 B/s, czyli około 0,0087–0,0142 Mb/s. Po 11,59 s klient zakończył działanie z błędem Cannot read. **Brak końcowego wyniku download i upload.** Nie przedstawiamy tych wartości jako ukończonego Speedtestu ani jako 0 Mb/s.

Łączny przyrost liczników wwan0 w trzech sieciowych próbach klienta wyniósł około 0,231 MB (RX+TX). To liczniki interfejsu, nie rozliczenie operatora. Błędy interfejsu i get_throttled pozostały zerowe. Wyniki uzasadniają dalszą diagnozę wolnej/niestabilnej transmisji; nie ustalają jeszcze przyczyny. Wcześniejsze 1,4 kB/s pochodziło z curl i oznaczało kilobajty, nie kilobity, na sekundę. Metodę, przeliczenia i ograniczenia opisuje rozdział 04.

Logi: 42 (instalacja), 43 (nieprawidłowe połączenie opcji i stan radia), 44–45 (próby przypisania interfejsu/adresu), 46 (lista serwerów), 47 (test T-Mobile i osobny plik summary.json).

## Dlaczego potrzebna była konfiguracja GPIO — wcześniejszy wariant

Początkowo UART był wyłączony, a `cmdline.txt` zawierał konsolę szeregową. W `/boot/firmware/config.txt` ustawiono `enable_uart=1`; z `/boot/firmware/cmdline.txt` usunięto `console=serial0,115200`. Konsola na `tty1` i tryb USB gadget pozostały. Po restarcie potwierdzono `/dev/serial0` oraz funkcje TXD1/RXD1 na pinach 14/15. Źródła: [GPIO w instrukcji PiTalk](https://shop.sb-components.co.uk/blogs/pitalk/tutorial-1-getting-started-with-pitalk), [UART Raspberry Pi](https://www.raspberrypi.com/documentation/computers/configuration.html#configuring-uarts).

Reguła `/etc/udev/rules.d/78-mm-pitalk-uart.rules` wskazuje ModemManagerowi konkretny port `ttyS0` kontrolera `fe215040.serial`. Dodatkowo `ID_MM_TTY_FLOW_CONTROL="none"` wyłącza automatyczny wybór RTS/CTS w ModemManagerze, zgodnie z połączeniem TX/RX bez tych linii. Dzięki temu wykrywa modem przez GPIO; brak urządzenia PiTalk w `lsusb` jest w tym wariancie oczekiwany. Źródło: [wykrywanie portów ModemManager](https://modemmanager.org/docs/modemmanager/port-and-device-detection/).

Pierwsza próba PPP zatrzymała się na oczekiwaniu sygnałów sterujących portem szeregowym. Połączenie HAT-a korzysta z TX/RX, dlatego plik `/etc/ppp/options.ttyS0` zawiera `local` i `nocrtscts`. Dotyczy to wyłącznie tego portu; ogólny `/etc/ppp/options` pozostał bez zmian. Znaczenie tych opcji opisuje [pppd w Debianie](https://manpages.debian.org/trixie/ppp/pppd.8.en.html).

Nieudane połączenie pozostawiło port w trybie danych. Przy zatrzymanym ModemManagerze sekwencją `+++` z odstępami ciszy i poleceniem `ATH` zakończono tę sesję, bez resetu modemu i bez ponownego wpisywania PIN-u. Kolejna próba PPP z nowymi ustawieniami powiodła się. Nie wysyłaj ręcznie komend AT na port zajęty przez działający PPP/ModemManager.

W poprzednim wariancie UART 115200 bit/s ograniczał przepustowość całego połączenia; nie jest to pełna szybkość LTE. Nie wykonywano speedtestu. Producent opisuje również transmisję USB; później uruchomiono ją profilem `tmobile-pitalk-usb`. Zachowany zapasowy profil `tmobile-pitalk` jest przypisany do `ttyS0`. [PiTalk 4G HAT](https://github.com/sbcshop/Pitalk_4G_HAT_Software).

## Wynik testu Internetu

3 października 2026 potwierdzono:

- trasę domyślną przez `ppp0`, z wyłączonym Wi-Fi Pi;
- ping do `1.1.1.1`: 3/3 odpowiedzi;
- DNS operatora `213.158.199.1` i `213.158.199.5`, również przez serwer LAN na `192.168.76.1`;
- HTTPS `https://example.com/` przez `ppp0`: `200 OK`, z normalną weryfikacją certyfikatu;
- `vcgencmd get_throttled=0x0` podczas krótkiego testu.

W pierwszym odczycie po teście liczniki IP interfejsu wskazywały około 7,5 kB odebranych i 4 kB wysłanych. To odczyt liczników, nie rozliczenie transferu operatora. Logi: `logs/10-tmobile-connected.txt` i `logs/10-internet-test.txt`.

## iPhone po Ethernecie

1. Połącz prywatny port Ethernet Pi z adapterem Ethernet–USB-C iPhone’a.
2. Ustaw automatyczną adresację interfejsu Ethernet telefonu.
3. Sprawdź adres `192.168.76.50–150`, maskę `255.255.255.0`, bramę i DNS `192.168.76.1`.
4. Na czas próby wyłącz Wi-Fi i transmisję komórkową samego iPhone’a, aby sprawdzić rzeczywisty ruch przez Pi.
5. Sprawdź dzierżawę i liczniki na Pi: `sudo pi-status`.

Po wymianie pierwszego adaptera USB-C–Ethernet potwierdzono fizyczny link, DHCP `192.168.76.72`, ping 3/3 oraz ruch przez NAT. Użytkownik potwierdził otwarcie example.com i check.torproject.org na iPhonie. Strony ładowały się bardzo wolno. Używany wtedy UART 115200 bit/s dawał teoretycznie najwyżej 11 520 bajtów danych na sekundę przy 8N1, jeszcze przed narzutem PPP/TCP/TLS. Nie jest to zmierzony transfer LTE. Próby 230400 i 921600 bit/s nie poprawiły niezawodności; późniejsze przejście na USB/QMI również nie usunęło problemu. Aktualnie aktywne jest USB, a ponowny test całego toru z iPhone’em po tej zmianie pozostaje do wykonania. Ruch po Ethernecie może zużywać pakiet prywatnej SIM, w tym na działania aplikacji w tle.

## Próby przyspieszenia GPIO/UART — przed przejściem na USB, 3 października 2026

**Stan końcowy tych prób: przywrócono 115200 bit/s.** GPIO pozostało podłączone; Bluetooth, bootloader, SIM i jej PIN nie były zmieniane. Nie wykonywano `AT&W`, resetu modemu ani ponownego odblokowania SIM. Modem cały czas zgłaszał `CPIN: READY`.

| Prędkość UART | Granica danych przy 8N1, przed PPP/TCP | Obserwacja |
|---|---|---|
| 115200 bit/s | 11,52 kB/s | Ustawienie bazowe, przywrócone po testach |
| 230400 bit/s | 23,04 kB/s | Duże straty pakietów; example.com około 6,6 s; test pobierania zakończony timeoutem |
| 921600 bit/s | 92,16 kB/s | PPP działa, ale HTTPS nadal wolne; 32 KiB nie pobrało się w 12 s nawet przy wstrzymanym ruchu telefonu |

W teście 921600 potwierdzono rzeczywistą prędkość przez `stty`, argument procesu `pppd` i regułę udev. Pierwsze pełne odpowiedzi HTTPS: example.com 577 B w 2,77 s i check.torproject.org 7900 B w 8,32 s. Kolejne próby wykazały timeouty. To pojedyncze pomiary, a nie dowód ośmiokrotnego przyspieszenia Internetu.

Po czasowym zablokowaniu tylko przekazywanego ruchu telefonu odebrano 13 721 B z planowanych 32 768 B w 12 s, około 1,1 kB/s licząc cały czas żądania. Usunięto potem tymczasową tabelę `pi_uart_test`. W osobnym teście mniejszych pakietów pobrano 16 KiB w 11,83 s; tymczasową trasę o MTU 576 również usunięto. MTU PPP pozostało 1500.

Dla 921600 bit/s ping do 1.1.1.1 z danymi 64 B odpowiedział 4/4 razy, z 1024 B — 2/4, z 1252 B — 1/4. To krótkie próbki wskazujące problem, nie miarodajny stały procent strat. Ślad TCP pokazuje brakujące segmenty i retransmisje. Liczniki UART nie pokazały błędów ramek/przepełnień, a `get_throttled` wynosiło 0x0. Nie ustalono jeszcze, w którym miejscu giną pakiety; samo powiększenie baudrate nie naprawiło problemu. Użytkownik również nie zauważył wyraźnej poprawy na iPhonie.

Modem przed próbą miał `AT+IFC? = 2,2`, czyli RTS/CTS, podczas gdy PPP pracowało bez tej kontroli. Poprawiono spójność ustawień przez `AT+IFC=0,0` i trwałą regułę `ID_MM_TTY_FLOW_CONTROL="none"`. Sama ta poprawka nie usunęła strat. Obecna konfiguracja prędkości w modemie, udev i obu polach profilu NetworkManagera jest zgodna: 115200.

Następnym krokiem po tych próbach był kabel danych USB-A Pi → USB-C PiTalk, z pozostawieniem kabla Mac → USB-C Pi. To porównanie ścieżek transmisji; ostateczny wybór GPIO/USB można podjąć po wyniku. Samo podłączenie przewodu nie przełącza profilu `tmobile-pitalk`, przypisanego do `ttyS0`. Należy rozłączyć ten profil przed aktywacją profilu USB, aby nie uruchamiać dwóch sesji sterujących tym samym modemem.

Źródła: [Quectel EG25-G Hardware Design, sekcja 3.11](https://quectel.com/content/uploads/2021/03/Quectel_EG25-G_Hardware_Design_V1.4.pdf), [komendy AT+IPR i zapis parametrów](https://forums.quectel.com/uploads/short-url/cBnrTmjnCg7OGnqRsk8dIpbHuVX.pdf), [tagi portów ModemManager](https://modemmanager.org/docs/modemmanager/port-and-device-detection/). Producent PiTalk publikuje [schemat V1.1](https://github.com/sbcshop/Pitalk_4G_HAT_Hardware/blob/main/Design%20Data/Schematic_PiTalk_4G.pdf): na stronach 3–4 UART łączy TX/RX przez rezystory, bez RTS/CTS. Rewizja egzemplarza użytkownika nie została potwierdzona, więc nie traktujemy tego schematu jako dowodu przyczyny awarii.

Logi: `15-uart-capabilities.txt` do `23-uart-baseline-restored.txt`. Kopie sprzed testów: `backups/uart-before-speed-tests/` oraz `/root/pi-uart-speed-backup-20261003/` na Pi. `scripts/test-uart-speed.py` jest zapisem eksperymentu, który przerywa LTE; nie jest narzędziem do codziennego uruchamiania połączenia.

## Kopie i cofnięcie ustawień modemu

Oryginalne pliki startowe są na Pi w `/root/pi-uart-backup-20261003/` i na Macu w `backups/boot-*.before-uart`. Nowe pliki i profil bez PIN-u znajdują się w `config/`. Skrypt routera poprawiono również tak, by odczytywał kilka adresów DNS rozdzielonych przez NetworkManager znakami ` | `.

Pierwotny skrypt cofania routera z rozdziału 02 **nie cofa późniejszych ustawień modemu/UART**. Aby zatrzymać bieżące dane komórkowe, wykonaj `sudo nmcli connection down tmobile-pitalk-usb`; dla wariantu UART użyj nazwy `tmobile-pitalk`. Pełne usunięcie konfiguracji modemu wymaga osobno usunięcia profilu `tmobile-pitalk`, reguły `78-mm-pitalk-uart.rules`, pliku `options.ttyS0` i odtworzenia obu plików startowych z kopii, a następnie restartu. Nie cofaj tych ustawień podczas działającej transmisji.

## Waveshare UPS HAT

Waveshare UPS jest osobnym HAT-em zasilającym; jego model nie został ustalony ani uruchomiony. Pi nadal otrzymuje zasilanie wyłącznie przez USB-C z Maca według informacji użytkownika.

Przed jednoczesnym zasileniem z UPS-a i USB-C trzeba sprawdzić instrukcję konkretnego wariantu UPS i obsługę tej kombinacji źródeł 5 V. Krótki test LTE z wynikiem `get_throttled=0x0` nie potwierdza zapasu mocy pod pełnym obciążeniem ani bezpiecznego współdziałania dwóch źródeł zasilania.

## PiTalk bezpośrednio do MacBooka — brak zasilania, 3 października 2026

Użytkownik przełączył modem z Pi do MacBooka i zgłosił brak diody zasilania. macOS wykrywa huby GenesysLogic i adapter Ethernet ASIX, ale nie Quectel (VID 0x2c7c); brak nowych portów szeregowych modemu. Nie potwierdzono napięcia pomiarem elektrycznym, dlatego brak enumeracji USB sam nie dowodzi braku 5 V. Zgłoszenie braku świecenia pochodzi od użytkownika. Log: `logs/55-modem-direct-mac-detection.json`.

W [schemacie producenta PiTalk V1.1, strona 2](https://github.com/sbcshop/Pitalk_4G_HAT_Hardware/blob/main/Design%20Data/Schematic_PiTalk_4G.pdf) piny CC1/A5 i CC2/B5 gniazda J1 są niepodłączone. Brak zaznaczonych rezystorów Rd do masy. Według [TI — USB Type-C](https://www.ti.com/lit/SLYY228) odbiornik 5 V wymaga sygnalizacji na CC (np. osobnych Rd 5,1 kΩ). To uzasadnia hipotezę, że taki wariant płytki nie uruchamia zasilania z połączenia C–C. Nie potwierdzono rewizji fizycznej płytki użytkownika ani jeszcze typu użytego kabla. Nie przypisujemy tej hipotezie wcześniejszego wolnego LTE zasilanego przez USB-A Raspberry Pi.

Następna próba: Mac → hub/adapter z USB-A → wcześniej sprawdzony kabel danych USB-A–USB-C → PiTalk, bez dodatkowego zasilania GPIO. Najpierw sprawdzić diodę zasilania; dopiero po jej zapaleniu uruchomić moduł przyciskiem PWRKEY przez 3–4 sekundy, zgodnie z [instrukcją PiTalk](https://github.com/sbcshop/Pitalk_4G_HAT_Software). Następnie ponownie sprawdzić enumerację USB. Nie instalowano sterowników, nie zmieniano ustawień modemu, sieci Maca ani SIM. Bez wykrytego urządzenia nie ma portu sterującego do programowego uruchomienia modemu. Internet bezpośrednio przez modem na macOS nie został jeszcze uruchomiony ani przetestowany.

Kopia schematu: `references/Schematic_PiTalk_4G.pdf`. Status: oczekiwanie na wynik fizycznego podłączenia przez USB-A.

## Zakończenie testu Maca

**Stan historyczny po teście Maca (3 października, 18:25): modem zasilany przez USB-A huba przy MacBooku, QMI przywrócone; nie jest obecnie połączony z Raspberry Pi.** USB i AT działają. ECM na Macu uzyskał DHCP, lecz nie przekazywał Internetu. Wewnętrzny HTTP modemu także zakończył się timeoutem. SIM wymaga PIN-u przy kolejnym uruchomieniu połączenia, licznik prób wynosi 3. Szczegóły: [test modemu na Macu](06-MODEM-NA-MACU.md).

## Wynik końcowy i powrót do konfiguracji Raspberry Pi

Próba HTTP z wewnętrznego klienta EG25-G, przy zasilaniu i sterowaniu z MacBooka, również nie zakończyła się pełnym pobraniem: nagłówki HTTP 200 po 0,293 s, a po 31,686 s błąd 702 (timeout HTTP). Plik w RAM modemu miał 10 737 z deklarowanych 16 384 B. Treść pliku nie była przesyłana przez USB do Maca. Wynik reprodukuje niepełne pobranie bez Raspberry Pi i jego zasilania; nie potwierdza pełnej sprawności kabla jako źródła zasilania ani nie izoluje firmware od radia i sieci operatora. Nie jest to Speedtest na Macu ani pomiar maksymalnej przepustowości. Kod 702 opisuje [instrukcja Quectel HTTP(S), rozdział 5](https://forums.quectel.com/uploads/short-url/kxS3asnEWfTxweAAYcLiomJakDE.pdf).

Po teście zakończono HTTP, usunięto własny plik z RAM i zdezaktywowano wewnętrzny kontekst. Następnie czasowo wyłączono radio przez CFUN=0, odtworzono oryginalny kontekst 1 (IPV4V6, pusty APN i dane uwierzytelniające), ustawiono usbnet=0 i ponownie włączono radio (CFUN=1). Odczyt potwierdził oba ustawienia. Ponowny odczyt deskryptorów USB potwierdził powrót interfejsu 4 do klasy vendor-specific QMI; nie pozostawiono modemu w ECM.

**Stan końcowy, 18:25:** modem nadal fizycznie podłączony do Maca przez hub USB-A, wykryty i odpowiada na AT; QMI przywrócone. Brak aktywnego wewnętrznego kontekstu danych. SIM po ponownym włączeniu radia wymaga PIN-u, ma 3 dostępne próby; nie wysyłano PIN-u ponownie na końcu. W trakcie testu Maca były dwie udane operacje odblokowania (przed i po restarcie), razem sześć udanych operacji w całej dotychczasowej sesji. Zabezpieczenia SIM pozostały włączone, PIN nie jest zapisany.

Internet Maca pozostał przez pierwotny Ethernet en9. Usługa sieciowa EG25-G, utworzona automatycznie przez macOS podczas ECM, może pozostać na liście jako nieaktywna; nie jest potwierdzeniem obecnego połączenia danych. W tej sesji nie zainstalowano ani nie uruchomiono Speedtestu na Macu, ponieważ ECM nie zapewnił połączenia do Internetu.

Do powrotu do routera należy fizycznie podłączyć modem z powrotem do USB-A Raspberry Pi, zapewnić osobne połączenie USB-C Pi–Mac do zasilania/SSH i uruchomić na Pi istniejący profil `sudo nmcli --ask connection up tmobile-pitalk-usb`. Po odłączeniu zasilania modemu może być potrzebne użycie przycisku Power i PIN-u. Konfiguracja Raspberry Pi nie była modyfikowana podczas testu na Macu.

Logi końcowe: `65-mac-internal-http.txt`, `66-mac-restore-qmi.txt`, `67-mac-final-state.txt`. Transport PyUSB używa tymczasowego venv zapisanego w `/tmp/pitalk-mac-usb-venv`; jego dostępność po restarcie Maca nie jest gwarantowana. Do powtórzenia tej zaawansowanej diagnostyki potrzebne są Python, PyUSB i libusb; nie jest wymagana do codziennej obsługi Pi przez SSH.


## Zakres projektu — draft do komisji

[Wizja i plan rozwoju](08-WIZJA-I-PLAN-PROJEKTU.md) opisuje telefon po kablu z wyłączonymi radiami, planowany Tor z mostami, panel filtrów i komunikacji oraz miniaturyzację (PCB i CAD). To pierwotny zakres projektu; późniejszy stan panelu, CAD i demonstracji Tora opisuje [STATUS](docs/STATUS.md). [Krótki draft PDF](projekt/Draft-projektu.pdf).
