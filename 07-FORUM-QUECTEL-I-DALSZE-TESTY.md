# Forum Quectela: EG25-G, timeouty także na Windowsie

> Zapis historyczny testów prototypu z 3 października 2026. Opis połączeń i wdrożeń odnosi się do czasu próby. Aktualny stan projektu, dashboardu i deklaracji dotyczących Tora: [STATUS](docs/STATUS.md). Surowe logi oraz kopie są lokalne.

Stan analizy: 3 października 2026. To analiza źródeł i dotychczasowych wyników, bez kolejnych zmian konfiguracji modemu.

## Najważniejszy wniosek

Użytkownik zgłosił, że EG25-G po instalacji sterowników na Windowsie również timeoutuje lub działa skrajnie wolno. Nie mamy logu, trybu USB ani pełnego wyniku Speedtest z tego komputera; traktujemy to jako relację użytkownika. W połączeniu z wcześniejszymi wynikami Pi i niepełnymi pobraniami wewnętrznego klienta modemu istotnie osłabia to hipotezę usterki wyłącznie sterownika Raspberry Pi, nftables albo ograniczenia fizycznego UART.

Nie ustalono dokładnej przyczyny. Wspólne pozostają moduł i jego firmware, płytka PiTalk i tor zasilania/anteny oraz współpraca urządzenia z operatorem. Ta sama SIM osiągnęła według użytkownika 73,9/55,1 Mb/s w iPhonie 16 przez LTE. To wyklucza traktowanie około 1,4 kB/s jako ogólnego stałego limitu tej karty; nie wyklucza różnic pasma, komórki ani obsługi konkretnego urządzenia.

## Najbliższe zgłoszenia na forum

| Źródło | Co opisano | Co rzeczywiście wynika dla nas |
|---|---|---|
| [EG25 — frequent disconnects, dropped packets](https://forums.quectel.com/t/eg25-frequent-disconnects-dropped-packets/18433) | Autor w 2022 r. odtworzył utratę łączności na Linuxie i wewnętrznym QPING sterowanym z Windowsa; przerwy około 5–15 s, także przy rozsądnych parametrach RF. Quectel w 2024 r. zaproponował firmware oraz próbę z innym operatorem. | Bardzo podobna niezależność od systemu hosta. Autor miał 01.003.01.003, my 30.203.30.203. Wątek nie zawiera potwierdzenia jednej skutecznej naprawy naszego przypadku. Późniejszy wpis z 30.204 dotyczy odmiennego objawu SSH connection refused, więc nie dowodzi identycznej usterki. |
| [EG25: Poor RSRQ with excellent RSSI & RSRP](https://forums.quectel.com/t/eg25-poor-rsrq-with-excellent-rssi-rsrp/19049) | Straty 50–70% przy dobrym RSSI/RSRP; podczas zdarzeń RSRQ spadało około −18 dB. Quectel sugerował porównanie warunków radiowych z telefonem. | Moc sygnału nie wystarcza. U nas próbki RSRQ były często około −7 dB, a zmiana miejsca nie pomogła; nie wolno utożsamiać tych przypadków ani zakładać, że całe radio zostało wykluczone. |
| [EG25-G firmware update](https://forums.quectel.com/t/eg25-g-firmware-update/21217) | Zgłoszenia powolnej pracy i dystrybucja firmware przez wsparcie; producent opisuje ograniczenia cofania wersji. | Firmware jest uzasadnionym tropem, ale nie ma potwierdzonej poprawki dla naszego objawu/30.203. Nie dobierać paczki tylko po napisie EG25-G; potrzebne potwierdzenie dokładnego wariantu i dozwolonej ścieżki aktualizacji. |
| [EC25 USB Interfaces crash](https://forums.quectel.com/t/ec25-usb-interfaces-crash/23356) | W pokrewnym EC25 autor potwierdził problem z zasilaniem powodujący znikanie USB. | Warto zweryfikować zasilanie płytki pod obciążeniem; to inny model i inny objaw, nie dowód przyczyny naszych strat. Zmiana komputera nie wymienia regulatora na PiTalku. Nie kopiujemy zaleceń łączenia wielu źródeł zasilania. |

Dodatkowo [wątek z 2026 r. dotyczący PinePhone](https://forums.quectel.com/t/eg25-frequently-disconnects/57324) opisuje głównie znikanie USB po uśpieniu. Nie pasuje dobrze do naszych aktywnych pobrań i błędów wewnętrznego HTTP. Nie wdrażamy na tej podstawie kolejnych zmian autosuspend ani przypadkowych zmian USB.

## Dokładna wersja firmware i profil operatora

Odczytana wcześniej pełna wersja: `EG25GGBR07A08M2G_30.203.30.203`. W przeszukanych materiałach nie znaleziono potwierdzonego błędu tej konkretnej wersji, który wyjaśnia nasze około 1,4 kB/s i timeouty, ani udokumentowanej poprawki rozwiązującej taki przypadek.

Istnieje [zgłoszenie na dokładnie 30.203 dotyczące profili MBN](https://forums.quectel.com/t/how-to-get-and-parse-content-of-mbn-file/43384). Dotyczy rejestracji IMS/VoLTE, nie zmierzonej przepustowości danych. To uzasadnia odczyt bieżącego profilu do zgłoszenia serwisowego, ale nie zmianę profilu na chybił-trafił ani rozpoznanie przyczyny na podstawie podobnego numeru firmware. T-Mobile Polska ma kod 26002; porad dla T-Mobile USA nie należy traktować jako potwierdzonej konfiguracji dla Polski.

Bezpieczne odczyty do późniejszego zebrania na aktualnie podłączonym komputerze, przez właściwy port AT (bez równoległego programu sterującego):

```text
AT+QGMR
AT+QMBNCFG="List"
AT+QENG="servingcell"
AT+QCFG="band"
```

Są to odczyty, nie procedura flashowania, resetu fabrycznego ani zmiany MBN. Nie wykonano ich ponownie w ramach tej analizy; aktualny stan po testach Windowsa jest nieznany. Nie zbieramy publicznie PIN-u, numeru telefonu, IMSI, ICCID ani IMEI. Wynik servingcell zawiera identyfikatory komórki, więc przed publiczną publikacją należy je zanonimizować.

## Czy iPhone używa innych pasm lub protokołów?

Może korzystać z innego pasma/komórki i bardziej zaawansowanego toru radiowego. W naszych pomiarach PiTalk rzeczywiście pracował w LTE: najpierw B3, później B1 (kanał 225, szerokość 15 MHz). B3 ma odbiór w zakresie 1805–1880 MHz, a B1 2110–2170 MHz. Oba należą do obsługiwanych pasm iPhone’a 16; nie jest to przypadek modemu niezdolnego do pracy na tych częstotliwościach. Nie znamy pasma i identyfikatora komórki podczas szybkiego testu iPhone’a.

EG25-G to LTE Cat 4 z teoretycznym maksimum 150/50 Mb/s. Apple podaje dla iPhone’a 16 Gigabit LTE i 4×4 MIMO. Lepszy modem telefonu i inne warunki przydziału zasobów mogą powodować różnicę wyników także bez 5G. Same różnice klasy urządzeń nie są jednak wystarczającym wyjaśnieniem uporczywych timeoutów tak małych plików. Teoretyczne maksima nie są gwarancją prędkości w sieci.

Źródła: [dane EG25-G](https://forums.quectel.com/uploads/short-url/fznFTQYaeQKtW9BlJOhL6aXL1T9.pdf), [częstotliwości w Hardware Design, tabela 28](https://quectel.com/content/uploads/2021/03/Quectel_EG25-G_Hardware_Design_V1.4.pdf), [specyfikacja iPhone’a 16](https://support.apple.com/pl-pl/121029).

## Kolejność dalszych testów

1. Porównać w tym samym modemie sprawną kartę innego operatora, np. Play lub Orange, z właściwym APN. To pierwsza rekomendacja, jeśli karta jest dostępna. Działa dobrze → podejrzenie współpracy T-Mobile/profilu/warunków sieci; nadal źle → rośnie podejrzenie zestawu modem–płytka–antena–zasilanie lub firmware. Przed wymianą SIM normalnie wyłączyć modem; nie wyjmować karty pod napięciem.
2. Jeśli dostępny jest drugi sprawny modem, porównać go na tej samej SIM. Alternatywnie sprawdzić z mentorem zasilanie PiTalka i dopasowaną antenę/złącze. Odczyt get_throttled=0 na Pi nie mierzy napięcia na module LTE. Zmieniać jeden element na próbę.
3. Z wynikami i pełnym QGMR poprosić producenta/sprzedawcę o właściwy firmware i potwierdzenie znanych usterek albo wymianę zestawu. Nie robić downgrade, factory reset ani aktualizacji plikiem przeznaczonym dla innego wariantu. Dla demonstracji praktycznym planem awaryjnym jest pożyczenie sprawnego modemu; nie twierdzimy, że egzemplarz już na pewno jest uszkodzony.

To plan diagnostyczny, nie kolejne wykonane pomiary. Nie wysłano wiadomości na forum ani do producenta i nie zmieniono ustawień SIM/modemu w tej turze.

## Szkic zgłoszenia do Quectela — do ręcznego wysłania

Subject: EG25-G / 30.203.30.203: severe packet loss and HTTP timeouts across hosts

Our PiTalk HAT uses a Quectel EG25-G, full firmware EG25GGBR07A08M2G_30.203.30.203. Operator is T-Mobile Poland (26002), APN internet. The user reports 73.9 Mbps down / 55.1 Mbps up on the same SIM in an iPhone 16 using LTE.

On Raspberry Pi 4, both GPIO PPP and USB QMI showed very slow small-file transfers, approximately 1.4 kB/s, with TCP retransmissions. Ookla CLI failed before producing a complete result. Moving location did not improve this; B3 and B1 were observed during different tests, with several strong signal samples. The user also reports severe slowness/timeouts on Windows with modem drivers installed; Windows logs and connection mode are not yet available.

To bypass the host IP stack, we used the modem's own HTTP client to fetch http://httpbingo.org/bytes/16384 into a RAM file. Powered/controlled from Pi: HTTP 200 headers, 10549/16384 bytes saved, QHTTPREADFILE error 702 after approximately 31 seconds. Powered/controlled from Mac through a USB-A hub: 10737/16384 bytes saved, same error 702 after approximately 32 seconds. Test RAM files and temporary internal contexts were cleaned up.

A separate Mac ECM trial obtained DHCP and successful local ping to 192.168.225.1, but the modem returned Destination Net Unreachable for external IPs despite LTE registration and an active internet PDP context. A restart did not fix ECM routing. We restored QMI and the original context-1 configuration afterward. This ECM symptom may be separate from the original throughput issue.

One supplied antenna is connected to GSM ANT. Antenna path and module supply voltage under load have not been independently validated; exact PiTalk PCB revision is unknown. No firmware upgrade, factory reset, SIM security changes or random carrier-profile changes were performed.

Please advise whether this firmware/hardware variant has a known TCP/packet-loss or ECM data-call issue, which diagnostics you need (including carrier profile), and the officially supported firmware upgrade path for this exact variant. We can provide logs with subscriber identifiers redacted.


## Zakres projektu — draft do komisji

[Wizja i plan rozwoju](08-WIZJA-I-PLAN-PROJEKTU.md) opisuje telefon po kablu z wyłączonymi radiami, planowany Tor z mostami, panel filtrów i komunikacji oraz miniaturyzację (PCB i CAD). To pierwotny zakres projektu; późniejszy stan panelu, CAD i demonstracji Tora opisuje [STATUS](docs/STATUS.md). [Krótki draft PDF](projekt/Draft-projektu.pdf).
