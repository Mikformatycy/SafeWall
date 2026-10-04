# PiTalk bezpośrednio z MacBookiem — test USB i ECM

> Zapis historyczny testów prototypu z 3 października 2026. Opis połączeń i wdrożeń odnosi się do czasu próby. Aktualny stan projektu, dashboardu i deklaracji dotyczących Tora: [STATUS](docs/STATUS.md). Surowe logi oraz kopie są lokalne.

## Co udało się potwierdzić

Po przełożeniu modemu do portu USB-A huba przy MacBooku pojawił się Quectel EG25-G (VID:PID 2c7c:0125). Użytkownik potwierdził, że nadal używa tego samego przewodu USB-A–USB-C. Urządzenie odpowiadało na polecenia AT, a po przełączeniu na ECM Mac uzyskał adres DHCP i odpowiadał ping do modemu. To potwierdza transmisję danych przez kabel, lecz nie jest pełnym testem jego niezawodności pod obciążeniem.

Wcześniej użytkownik zgłaszał brak diody zasilania; Mac nie wykrywał wtedy modemu. Schemat PiTalk V1.1 na stronie 2 pokazuje niepodłączone piny CC1/CC2 w gnieździe USB-C. Może to wyjaśniać brak zasilania przy połączeniu C–C. Nie potwierdzono rewizji fizycznej płytki ani dokładnego wcześniejszego kabla, więc pozostaje to hipotezą. Udanym obejściem wykrywania okazał się port USB-A huba. Brak zasilania USB-C i wcześniejsze bardzo wolne LTE to odrębne obserwacje; nie ustalono ich wspólnej przyczyny.

Źródła: [schemat PiTalk V1.1](https://github.com/sbcshop/Pitalk_4G_HAT_Hardware/blob/main/Design%20Data/Schematic_PiTalk_4G.pdf), [TI: wykrywanie odbiornika USB-C przez piny CC](https://www.ti.com/lit/SLYY228).

## Dlaczego sam modem w USB nie oznacza Internetu

W oryginalnym trybie QMI (`AT+QCFG="usbnet"` → 0) macOS nie utworzył portów /dev/cu.usb* ani interfejsu sieciowego. Dostęp AT uzyskano bez sterownika jądra: PyUSB 1.3.1 w tymczasowym środowisku Python i istniejąca biblioteka Homebrew libusb. Użyto interfejsu USB 2, bulk OUT 0x03 i bulk IN 0x84. Nie zmieniano konfiguracji audio ani innych urządzeń USB. Pomocniczy transport jest zapisany w `scripts/mac-usb-at.py`; sam import nie wysyła poleceń.

Po zapisaniu stanu wyjściowego (`config/mac-ecm-before.json`) ustawiono `AT+QCFG="usbnet",1`. macOS sam rozpoznał kartę EG25-G jako en12 i otrzymał DHCP 192.168.225.22/24, bramę i DNS 192.168.225.1. APN kontekstu 1 ustawiono na IPv4/internet. Odblokowanie podanym przez użytkownika PIN-em było udane, licznik nadal wskazywał 3 próby. PIN nie został zapisany w plikach. Modem zarejestrował się w LTE T-Mobile (26002), B1/kanał 225, z aktywnym kontekstem internet i DNS operatora 213.158.199.1/.5.

Połączenie lokalne działało: ping 192.168.225.1 odpowiedział 3/3, średnio 1,031 ms. Jednak modem sam zwracał ICMP Destination Net Unreachable dla 1.1.1.1. DNS modemu zwracał REFUSED, a próby HTTP i HTTPS z Maca przypisane do en12 kończyły się timeoutem połączenia. Nie uzyskano wyniku szybkości Internetu na Macu — to nie jest wynik 0 Mb/s ani pomiar wcześniejszych 1,4 kB/s.

Instrukcja producenta zestawów Sixfab dla EG25-G przewiduje restart po ustawieniu ECM. Wykonano `AT+CFUN=1,1`. Pierwsze sprawdzenie trafiło na trwające ponowne wykrywanie USB; następnie modem wrócił. Po jednej udanej operacji odblokowania wymaganej po restarcie SIM ponownie miała 3 próby. en12 otrzymał 192.168.225.24; modem zarejestrował LTE, ale dalej zwracał Destination Net Unreachable. Sam restart nie naprawił przekazywania ruchu ECM. [Procedura ECM dla EG25-G](https://docs.sixfab.com/page/cellular-internet-connection-in-ecm-mode).

## Oddzielenie pomiaru od Internetu hackathonu

Domyślna trasa Maca pozostała przez en9/AX88179B i bramę 10.250.192.1. Nie wyłączano innych połączeń. ECM miał osobną trasę ograniczoną do en12 przez 192.168.225.1. Testy wykonywano ze wskazaniem interfejsu:

```bash
route -n get -ifscope en12 default
ping -b en12 -c 3 -W 1000 192.168.225.1
ping -b en12 -c 3 -W 1000 1.1.1.1
curl -4 --interface en12 --connect-timeout 6 --max-time 20 http://httpbingo.org/bytes/16384 -o /dev/null
```

Nazwa en12 i adres DHCP są z tej sesji; po przyszłym podłączeniu sprawdź je ponownie przez `networksetup -listallhardwareports`. Te polecenia sieciowe mają sens wyłącznie w aktywnym wariancie ECM. Przed powrotem do istniejącego profilu Raspberry Pi trzeba przywrócić QMI, usbnet=0; zapis ustawień wyjściowych jest w config/mac-ecm-before.json. Nie wysyłaj poleceń AT jednocześnie z innym programem sterującym modemem.

## Logi i stan końcowy

Logi 55–57: brak wykrycia, następnie działające USB AT oraz stan przed ECM. Logi 58–61: przełączenie ECM, DHCP, rejestracja LTE i niedziałające przekazywanie do Internetu. Logi 62–64: restart i ponowne sprawdzenie, bez poprawy.

## Wynik końcowy i powrót do konfiguracji Raspberry Pi

Próba HTTP z wewnętrznego klienta EG25-G, przy zasilaniu i sterowaniu z MacBooka, również nie zakończyła się pełnym pobraniem: nagłówki HTTP 200 po 0,293 s, a po 31,686 s błąd 702 (timeout HTTP). Plik w RAM modemu miał 10 737 z deklarowanych 16 384 B. Treść pliku nie była przesyłana przez USB do Maca. Wynik reprodukuje niepełne pobranie bez Raspberry Pi i jego zasilania; nie potwierdza pełnej sprawności kabla jako źródła zasilania ani nie izoluje firmware od radia i sieci operatora. Nie jest to Speedtest na Macu ani pomiar maksymalnej przepustowości. Kod 702 opisuje [instrukcja Quectel HTTP(S), rozdział 5](https://forums.quectel.com/uploads/short-url/kxS3asnEWfTxweAAYcLiomJakDE.pdf).

Po teście zakończono HTTP, usunięto własny plik z RAM i zdezaktywowano wewnętrzny kontekst. Następnie czasowo wyłączono radio przez CFUN=0, odtworzono oryginalny kontekst 1 (IPV4V6, pusty APN i dane uwierzytelniające), ustawiono usbnet=0 i ponownie włączono radio (CFUN=1). Odczyt potwierdził oba ustawienia. Ponowny odczyt deskryptorów USB potwierdził powrót interfejsu 4 do klasy vendor-specific QMI; nie pozostawiono modemu w ECM.

**Stan końcowy, 18:25:** modem nadal fizycznie podłączony do Maca przez hub USB-A, wykryty i odpowiada na AT; QMI przywrócone. Brak aktywnego wewnętrznego kontekstu danych. SIM po ponownym włączeniu radia wymaga PIN-u, ma 3 dostępne próby; nie wysyłano PIN-u ponownie na końcu. W trakcie testu Maca były dwie udane operacje odblokowania (przed i po restarcie), razem sześć udanych operacji w całej dotychczasowej sesji. Zabezpieczenia SIM pozostały włączone, PIN nie jest zapisany.

Internet Maca pozostał przez pierwotny Ethernet en9. Usługa sieciowa EG25-G, utworzona automatycznie przez macOS podczas ECM, może pozostać na liście jako nieaktywna; nie jest potwierdzeniem obecnego połączenia danych. W tej sesji nie zainstalowano ani nie uruchomiono Speedtestu na Macu, ponieważ ECM nie zapewnił połączenia do Internetu.

Do powrotu do routera należy fizycznie podłączyć modem z powrotem do USB-A Raspberry Pi, zapewnić osobne połączenie USB-C Pi–Mac do zasilania/SSH i uruchomić na Pi istniejący profil `sudo nmcli --ask connection up tmobile-pitalk-usb`. Po odłączeniu zasilania modemu może być potrzebne użycie przycisku Power i PIN-u. Konfiguracja Raspberry Pi nie była modyfikowana podczas testu na Macu.

Logi końcowe: `65-mac-internal-http.txt`, `66-mac-restore-qmi.txt`, `67-mac-final-state.txt`. Transport PyUSB używa tymczasowego venv zapisanego w `/tmp/pitalk-mac-usb-venv`; jego dostępność po restarcie Maca nie jest gwarantowana. Do powtórzenia tej zaawansowanej diagnostyki potrzebne są Python, PyUSB i libusb; nie jest wymagana do codziennej obsługi Pi przez SSH.



## Zakres projektu — draft do komisji

[Wizja i plan rozwoju](08-WIZJA-I-PLAN-PROJEKTU.md) opisuje telefon po kablu z wyłączonymi radiami, planowany Tor z mostami, panel filtrów i komunikacji oraz miniaturyzację (PCB i CAD). To pierwotny zakres projektu; późniejszy stan panelu, CAD i demonstracji Tora opisuje [STATUS](docs/STATUS.md). [Krótki draft PDF](projekt/Draft-projektu.pdf).
