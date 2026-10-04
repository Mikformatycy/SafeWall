# Szybka diagnostyka podczas prezentacji

> Zapis historyczny testów prototypu z 3 października 2026. Opis połączeń i wdrożeń odnosi się do czasu próby. Aktualny stan projektu, dashboardu i deklaracji dotyczących Tora: [STATUS](docs/STATUS.md). Surowe logi oraz kopie są lokalne.

Kliknij dwukrotnie `Diagnoza.command` w tym folderze, aby zapisać podstawowy raport do `logs/`. Raport nie wymaga sudo i nie pokazuje pełnych reguł firewalla.

Pełniejsza kontrola: na Macu `ssh pi-usb`, następnie na Pi `sudo pi-status`. Ta komenda zbiera stan zasilania, sieci, usług, modemu, firewalla i dzierżaw DHCP.

## Nie działa SSH po USB

Na Macu:

```bash
networksetup -listallhardwareports
route -n get 10.12.194.1
ping -c 3 10.12.194.1
ssh -v pi-usb
```

| Objaw | Dalszy krok |
|---|---|
| Brak „Raspberry Pi USB Gadget” | Sprawdź port USB-C Pi, kabel z transmisją danych i zasilanie; po restarcie daj Pi 30–90 sekund |
| Trasa do `10.12.194.1` idzie przez domyślną sieć hackathonu | Sieć USB nie jest jeszcze gotowa; nie diagnozuj przez ogólne `raspberrypi.local` |
| USB jest, lecz Mac ma `169.254.x.x` | DHCP USB nie przydzieliło adresu; sprawdź stan Pi, odczekaj odnowienie dzierżawy lub podłącz ponownie kabel po zakończeniu startu |
| Ping działa, ale port 22 nie | Sprawdź `ssh.service` i własną tabelę nftables; jeśli zmieniałeś firewall, poczekaj na wcześniej zaplanowane cofnięcie |
| Ostrzeżenie o kluczu hosta | Potwierdź tożsamość Pi lub fakt ponownego flashowania przed usunięciem konkretnego wpisu |

Jeśli działa inna otwarta sesja:

```bash
systemctl status ssh nftables --no-pager
sudo nft list chain inet pi_router input
journalctl -b -u ssh -u nftables --no-pager -n 60
```

## Po restarcie modem wymaga PIN-u

Na Pi wykonaj `mmcli -L`, następnie `sudo nmcli --ask connection up tmobile-pitalk-usb`. Profil ma wyłączone autopołączenie i nie zapisuje PIN-u. Gdy poprawny PIN nie jest znany, przerwij; nie zgaduj. W bieżącym połączeniu USB modem powinien być widoczny w `lsusb` jako `2c7c:0125`, a w `nmcli device` jako `cdc-wdm0`. Zapasowy profil GPIO nazywa się `tmobile-pitalk`.

Jeśli brak modemu w `mmcli -L`, sprawdź przycisk Power, kabel USB danych i `lsusb -t`. Pierwszy użyty przewód nie wykrywał urządzenia; wymiana kabla rozwiązała wykrywanie. Dla wariantu zapasowego GPIO sprawdź `ls -l /dev/serial0` i `udevadm info /dev/ttyS0`. Nie uruchamiaj bezpośrednich prób AT na portach zajętych przez ModemManager lub PPP.

## iPhone nie otrzymuje adresu

Na Pi:

```bash
ip -brief address show eth0
cat /sys/class/net/eth0/carrier
systemctl status pi-lan-dnsmasq --no-pager
sudo cat /var/lib/pi-router/dnsmasq.leases
journalctl -b -u pi-lan-dnsmasq --no-pager -n 60
```

Przy pierwszej fizycznej próbie z iPhonem wykryto `carrier=0`, zero pakietów Ethernet i brak dzierżawy DHCP, mimo że iPhone wyświetlał zakładkę Ethernet. Sama obecność tej zakładki potwierdza rozpoznanie adaptera przez telefon, ale nie potwierdza połączenia kablem do Pi. Automatyczne IP jest właściwym ustawieniem. Ręczny adres nie naprawia braku fizycznego linku.

Najpierw odłącz adapter USB-C, odblokuj iPhone’a i podłącz adapter ponownie. To zalecana przez [Apple procedura ponownego wykrywania akcesorium](https://support.apple.com/en-gb/111806). Następnie sprawdź/podmień przewód RJ45. Diody kontrolne Ethernetu znajdują się przy samym metalowym gnieździe RJ45 Pi; czerwono-zielone diody zasilania/aktywności na płytce nie potwierdzają linku Ethernet.

Adres Pi powinien wynosić `192.168.76.1/24`. `carrier=0` oznacza brak fizycznego linku — wtedy sprawdź kabel RJ45 i adapter telefonu. `carrier=1` z brakiem dzierżawy kieruje diagnostykę na DHCP.

Podgląd krótkiej próby DHCP:

```bash
sudo timeout 15 tcpdump -ni eth0 'udp port 67 or udp port 68'
```

Szukaj sekwencji DISCOVER → OFFER → REQUEST → ACK. Daj klientowi kilka sekund; serwer może sprawdzać, czy proponowany adres jest wolny. Adres `169.254.x.x` na iPhonie nie jest poprawnym adresem naszego LAN.

## Adres jest, ale Internet nie działa

```bash
mmcli -L
nmcli -f NAME,TYPE,DEVICE connection show --active
ip -4 route
sudo nft list set inet pi_router wan_ifaces
cat /run/pi-router/wan-resolv.conf
```

| Wynik | Znaczenie i działanie |
|---|---|
| `No modems were found` | Najpierw sprzęt, połączenie danych i zasilanie PiTalk |
| Modem jest, ale brak aktywnego profilu komórkowego | Uruchom `sudo nmcli --ask connection up tmobile-pitalk-usb`; w razie błędu sprawdź stan SIM i rejestrację |
| Pusty `wan_ifaces` | To oczekiwane bez modemu; po jego aktywacji uruchom `sudo pi-router-wan` |
| Pi ma Internet, iPhone nie | Sprawdź bramę telefonu, liczniki `forward` i NAT oraz właściwy interfejs modemu |
| iPhone pokazuje Internet mimo braku modemu | Wyłącz na czas testu jego własne Wi-Fi i dane komórkowe |

Liczniki:

```bash
sudo nft list chain inet pi_router forward
sudo nft list chain inet pi_router postrouting
```

Nie rozwiązuj tego przez `nft flush ruleset`. Usunęłoby to również konfigurację NetworkManagera i naruszyło izolację USB.

## PPP zgłasza błąd, mimo rejestracji LTE

Dla zapasowego połączenia GPIO plik `/etc/ppp/options.ttyS0` musi zawierać `local` i `nocrtscts`; profil używa 115200 bit/s. Brak tych ustawień zatrzymywał pierwszą próbę na fazie otwierania portu. Sprawdź `journalctl -b _COMM=pppd --no-pager -n 40`. Nie wpisuj ponownie PIN-u, jeśli modem jest już odblokowany. Szczegóły naprawy zapisano w rozdziale 03.

## Strony otwierają się bardzo wolno

Bieżący profil to `tmobile-pitalk-usb`, interfejs `wwan0`. USB/QMI omija ograniczenie UART, ale w teście nadal występowały straty większych pakietów oraz około 1,5 kB/s w nieudanym pobieraniu 64 KiB. Zapora nie odrzucała brakujących odpowiedzi w kontrolowanym teście ICMP: nie docierały już do `wwan0`. Dokładna przyczyna po stronie modemu lub dalszej ścieżki sieciowej pozostaje nieustalona.

```bash
nmcli -f NAME,TYPE,DEVICE connection show --active
ping -I wwan0 -c 3 -W 2 1.1.1.1
ping -I wwan0 -M do -s 1252 -c 5 -W 2 1.1.1.1
curl -4 --interface wwan0 --head --max-time 20 https://example.com/
```

Sprawdź również `cat /sys/class/net/eth0/carrier`, zanim oceniasz Internet z iPhone’a. Podczas próby USB wynosiło 0. Wykonane porównanie: użytkownik zgłosił na tej samej SIM w iPhonie 16 przez LTE 73,9 Mb/s pobierania i 55,1 Mb/s wysyłania. Nie przypisuj więc około 1,4 kB/s na PiTalku ogólnemu limitowi tej SIM. Pozostaje rozdzielić modem/warunki jego LTE od Raspberry Pi; dokładna przyczyna nie jest ustalona. Nie zgaduj PIN-u, nie resetuj modemu/SIM i nie zdejmuj zabezpieczeń. Szczegółowe pomiary: rozdział 03, logi 25–28.

Zapasowy UART (`tmobile-pitalk`) pozostaje na 115200 bit/s, z teoretycznym limitem 11,52 kB/s przed narzutem. Próby 230400 i 921600 nie usunęły problemu. Nie aktywuj jednocześnie profilu USB i UART tego samego modemu.

## Jak mierzymy szybkość: mały plik i Speedtest CLI

Dotychczasowe 1,4 kB/s było średnią szybkością małego pobrania HTTP/HTTPS przez curl na Pi, przypisanego do wwan0. Nie był to wynik Speedtest ani pomiar maksymalnej przepustowości LTE.

```text
16 KiB = 16 384 bajty
16 384 B / 11,417 s ≈ 1435 B/s ≈ 1,435 kB/s
1435 B/s × 8 ≈ 11 480 bit/s = 11,48 kb/s = 0,01148 Mb/s
```

Duże B oznacza bajty, małe b — bity. Całkowity czas curl obejmuje przygotowanie połączenia, TLS, oczekiwanie na odpowiedź i odebranie treści; dla małego pliku może istotnie zaniżać ocenę maksymalnej przepustowości. Część prób pomijała DNS przez --resolve. Jednocześnie ślady TCP pokazały luki i oczekiwanie na brakujące dane, więc długi czas pobierania nie był samą pomyłką jednostek. Wynik należy opisywać jako konkretną próbę, nie stały limit całego Internetu.

Na prośbę użytkownika zainstalowano oficjalny Ookla Speedtest CLI 1.2.0.84 dla aarch64 w `/usr/local/bin/speedtest`. Archiwum pobrano przez Internet Maca z install.speedtest.net, a pliki przesłano do Pi przez USB/SSH. Nie dodano repozytorium APT. Metadane i sumy SHA-256 są w `config/ookla-speedtest-install.json`, instrukcja dostawcy w `references/ookla-speedtest-1.2.0.md` i na Pi w `/usr/local/share/doc/ookla-speedtest/speedtest.md`.

Pomiar na Pi przez modem, po aktywacji tmobile-pitalk-usb:

```bash
ip -4 route get 1.1.1.1
sudo timeout --signal=INT --kill-after=5s 150s speedtest --interface=wwan0 --progress=no
```

Trasa powinna wskazywać wwan0. Nie podawaj jednocześnie --interface i --ip: klient uznaje te opcje za wzajemnie wykluczające. Wynik czytelny dla człowieka podaje Mb/s. W formacie JSON pola download.bandwidth i upload.bandwidth są w **bajtach/s**, więc przeliczaj je przez ×8/1 000 000. Brak wyniku lub błąd inicjalizacji nie jest wynikiem 0 Mb/s. Pełny Speedtest może zużyć znacznie więcej danych niż małe pobrania curl; uruchamiaj go świadomie na prywatnej SIM.

Ostatnia próba na serwerze T-Mobile Kraków (ID 23123) rozpoczęła pobieranie z postępem 1086–1777 B/s, ale zakończyła się błędem odczytu. Nie ma pełnego wyniku download/upload; log i opis ograniczeń znajdują się w `logs/47-ookla-tmobile-server.txt` i `logs/47-ookla-summary.json`.

## Wynik próby z pominięciem sieci Raspberry Pi

Wbudowany klient HTTP EG25-G pobrał do własnego RAM tylko 10 549 z 16 384 B, po czym zgłosił timeout 702. Nie przesyłano treści pliku przez UART ani stos IP Pi. Ten wynik oraz nieukończony Speedtest pokazują, że dalsze losowe zmiany nftables/baud rate nie mają obecnie uzasadnienia. Dokładnej przyczyny w modemie, radiu, zasilaniu lub sieci operatora jeszcze nie ustalono.

Po eksperymencie przywrócono oryginalny kontekst wewnętrznego klienta, usunięto jego plik RAM i uruchomiono profil USB/QMI. Ostatnie sprawdzenie: WAN wwan0, LTE B1, ping 2/2, get_throttled=0x0. Opis metody i ograniczeń: [modem i zasilanie](03-MODEM-I-ZASILANIE.md); surowe wyniki: `logs/49-internal-http-comparison.txt` do `logs/51-restored-after-speedtest-http.txt`.

## Porównanie miejsca na stadionie

**Próba wykonana 17:57–17:58: bez poprawy.** Na tym samym serwerze Ookla 23123 test znów przerwał się błędem; plik HTTP 16 KiB pobrał się w 11,734 s (1396 B/s). Radio pozostało B1; odczyt SNR bezpośrednio przed pomiarem wyniósł 30 dB, po nim 13,8 dB. Przed próbą Pi zrestartowało się i trzeba było ponownie odblokować SIM/połączyć LTE; przyczyna restartu pozostaje nieznana. Szczegóły i ograniczenia porównania: rozdział 03, logi 52–54. Nie powtarzaj losowych zmian ustawień; najpierw ustal, czy zasilanie zostało odłączone podczas przenoszenia.

Zmiana miejsca jest testem, nie potwierdzoną naprawą. Zestaw PiTalk i iPhone mogą korzystać z innych pasm, komórek i torów antenowych. Moc sygnału nie opisuje całej jakości łącza; wpływ mają też zakłócenia, przeszkody i obciążenie stacji. Nie zakładaj, że położenie anten na dachu oznacza automatycznie lepszy odbiór piętro wyżej. Źródło: [Teltonika — czynniki wpływające na jakość połączenia](https://wiki.teltonika-networks.com/view/Mobile_Signal_Strength_Recommendations).

Najpierw zmierz w obecnym miejscu, później w innym dostępnym miejscu. Zachowaj kabel, antenę i zasilanie; zanotuj LTE band/EARFCN, RSRP/RSRQ/SNR, identyfikator serwera Speedtest i wyniki pobierania/wysyłania. Przy kolejnym pomiarze można podać `--server-id=NUMER` z poprzedniego wyniku. Jednoczesna zmiana miejsca, pasma i serwera ogranicza możliwość przypisania poprawy do jednej przyczyny.

## Problem tylko z DNS

```bash
dig @192.168.76.1 router.pi.home.arpa +short +time=2 +tries=1
dig @192.168.76.1 example.com +time=3 +tries=1
cat /run/pi-router/wan-resolv.conf
journalctl -b -u pi-lan-dnsmasq --no-pager -n 40
```

Pierwsza komenda powinna zwracać `192.168.76.1` także bez SIM. Druga wymaga aktywnego połączenia modemu i jego serwerów DNS. Komunikat o braku serwerów zewnętrznych jest oczekiwany, gdy modem jest odłączony.

## Zasilanie i restarty

```bash
vcgencmd get_throttled
vcgencmd measure_temp
uptime
journalctl -k -b --no-pager | grep -Ei 'under.volt|voltage|over.current|usb.*disconnect'
```

Przy powtarzających się zniknięciach USB albo resetach modemu najpierw ustabilizuj zasilanie zgodnie z instrukcją konkretnego UPS-a. Nie zaczynaj od przeinstalowywania systemu.

## Usługi i ponowne sprawdzenie

```bash
systemctl is-active ssh nftables pi-lan-dnsmasq ModemManager
sudo dnsmasq --test --conf-file=/etc/pi-router/dnsmasq-lan.conf
sudo nft -c -f /etc/nftables.conf
```

Po poprawnej walidacji można odpowiednio przeładować firewall lub zrestartować DHCP/DNS:

```bash
sudo systemctl reload nftables
sudo systemctl restart pi-lan-dnsmasq
```

Pełne cofnięcie wdrożenia opisuje [konfiguracja routera](02-KONFIGURACJA.md). Nie resetuj całej sieci ani NetworkManagera, jeśli wystarczy restart pojedynczej usługi.

## Zachowanie logów przed restartem

Obraz systemu ma `Storage=volatile`: dziennik `journalctl` znajduje się w pamięci i nie zachowuje poprzednich uruchomień. Zapisane raporty w folderze `logs/` na Macu pozostają dostępne po restarcie. Przed odłączeniem lub restartem zapisz potrzebny fragment dziennika z Maca:

```bash
ssh pi-usb 'journalctl -b -u nftables -u pi-lan-dnsmasq -u ModemManager --no-pager' > "$HOME/Desktop/RaspberryPi-Hackathon/logs/journal-$(date +%Y%m%d-%H%M%S).txt"
```

## Czas w logach i cloud-init

Pi nie ma w tej konfiguracji potwierdzonego zegara RTC. Po uruchomieniu LTE wcześniej potwierdzono synchronizację NTP; jej bieżący stan sprawdzaj przez `timedatectl`. Podczas wdrożenia zegar ustawiono z Maca. Po późniejszym długim odłączeniu od zasilania sprawdź `date` i `timedatectl`. Przy braku Internetu można z Maca ustawić czas:

```bash
ssh -t pi-usb "sudo date -u -s '@$(date +%s)'"
```

Po pierwszym uruchomieniu cloud-init zgłaszał `degraded done` z ostrzeżeniem o brakującym `cc_netplan_nm_patch`, bez błędów w tablicy `errors`. Hostname, konto, SSH i USB zostały zastosowane i przetestowane. Nie uruchamiaj `cloud-init clean` ani ponownej inicjalizacji podczas prezentacji.

## Kontrola po eksperymentach UART

W nieaktywnym profilu zapasowym `tmobile-pitalk` aktualne `serial.baud` i `ppp.baud` mają wynosić 115200, a reguła udev dodatkowo zawierać `ID_MM_TTY_FLOW_CONTROL="none"`. Nie zmieniaj samej prędkości Pi: modem musi mieć tę samą prędkość. Nie wysyłaj AT na port zajęty przez PPP.

```bash
nmcli -g serial.baud,ppp.baud connection show tmobile-pitalk
sudo stty -F /dev/ttyS0 speed
sudo nft list tables
ip route
```

Po zakończonych testach powinny pozostać tabele `inet pi_router` i `ip nm-shared-usb0`, bez `pi_uart_test`, oraz brak specjalnej trasy testowej do `172.66.0.218/32`. Pojedynczy brak pingu z uśpionego iPhone’a nie dowodzi awarii Ethernetu — porównaj DHCP, ARP i rzeczywisty ruch telefonu.

## Odczyt radia USB bez zmiany pasm

Na Pi, z podłączonym kablem danych PiTalk i działającym ModemManagerem:

```bash
sudo qmicli --device=/dev/cdc-wdm0 --device-open-proxy --nas-get-signal-info
sudo qmicli --device=/dev/cdc-wdm0 --device-open-proxy --nas-get-rf-band-info
```

To odczyty diagnostyczne przez `qmi-proxy`, bez resetowania modemu, zmiany pasm i operacji na SIM. Potwierdzono działanie z zainstalowaną wersją `qmicli`. Jeżeli nie ma `/dev/cdc-wdm0`, zacznij od `lsusb` i `mmcli -L`.

Około 16:01–16:07 zmierzono RSRP −59…−58 dBm, RSRQ −7 dB, SNR 16,4…30 dB oraz LTE band 3 / 15 MHz. Dobry odbiór nie wyklucza przeciążenia stacji bazowej; same te liczby nie potwierdzają przyczyny wolnego Internetu. Nie blokuj losowo pasm ani nie zmieniaj APN na podstawie samej hipotezy. Wyniki i ograniczenia pomiarów opisano w rozdziale 03.

## Brak zasilania PiTalk po podłączeniu bezpośrednio do Maca

Sprawdzone obejście: port USB-A huba przy Macu i kabel danych USB-A–USB-C. Samo pojawienie się Quectel w USB nie oznacza działającego Internetu. W wykonanej próbie macOS rozpoznał ECM i dostał DHCP, lecz modem nie przekazywał ruchu. Po testach odtworzono QMI dla Pi. Szczegóły, hipotezę dotyczącą pinów CC i wyniki opisuje [test modemu na Macu](06-MODEM-NA-MACU.md).


## Zakres projektu — draft do komisji

[Wizja i plan rozwoju](08-WIZJA-I-PLAN-PROJEKTU.md) opisuje telefon po kablu z wyłączonymi radiami, planowany Tor z mostami, panel filtrów i komunikacji oraz miniaturyzację (PCB i CAD). To pierwotny zakres projektu; późniejszy stan panelu, CAD i demonstracji Tora opisuje [STATUS](docs/STATUS.md). [Krótki draft PDF](projekt/Draft-projektu.pdf).
