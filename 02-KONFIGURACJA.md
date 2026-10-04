# Konfiguracja routera

> Zapis historyczny testów prototypu z 3 października 2026. Opis połączeń i wdrożeń odnosi się do czasu próby. Aktualny stan projektu, dashboardu i deklaracji dotyczących Tora: [STATUS](docs/STATUS.md). Surowe logi oraz kopie są lokalne.

## Dostęp administracyjny

Na Macu `~/.ssh/config` zawiera alias `pi-usb`: adres `10.12.194.1`, użytkownik `piotr`, osobny klucz `~/.ssh/piotr4mmc_usb`. Klucz publiczny dodano do `/home/piotr/.ssh/authorized_keys` na Pi. Logowanie hasłem pozostało dostępne przez USB jako możliwość awaryjna.

SSH i uprawnienia `sudo` sprawdzono praktycznie. Nie usuwano istniejących kluczy znanych hostów. Nie należy usuwać ich automatycznie przy ostrzeżeniu o zmianie klucza — najpierw potwierdź, że chodzi o to samo Pi lub świeżo przeinstalowaną kartę.

## Polityka nftables

Własna tabela nazywa się `inet pi_router`. Wejście i przekazywanie mają domyślną politykę `drop`; wyjście samego Pi jest dozwolone.

| Kierunek | Reguła |
|---|---|
| USB → Pi | SSH TCP 22, DHCP i mDNS; diagnostyczny ICMP |
| Ethernet → Pi | DHCP i DNS TCP/UDP 53; SSH z Ethernetu jest blokowany |
| Ethernet → modem | Dozwolony IPv4 z `192.168.76.0/24` z NAT |
| Modem → Ethernet | Tylko odpowiedzi do już ustanowionych/powiązanych połączeń |
| USB → inne sieci | Przekazywanie blokowane, także gdy NetworkManager ma własne reguły udostępniania |

Reguły DHCP klienta na interfejsie modemu oraz komunikaty ICMP/ICMPv6 pozwalają na podstawowe działanie sieci. Porty aplikacji nie są automatycznie otwierane.

NetworkManager zachowuje własną tabelę `ip nm-shared-usb0`. Nasz filtr działa z priorytetem `filter + 10`, więc wcześniejsze `accept` w tabeli NetworkManagera nie omija naszej blokady. Nie stosujemy `nft flush ruleset`. Źródło semantyki: [podręcznik nftables](https://netfilter.org/projects/nftables/manpage.html).

## Aktywny modem i DNS

`pi-router-wan` odczytuje aktywne profile NetworkManagera typu GSM/CDMA i ich rzeczywisty interfejs IP. To istotne, bo port kontrolny `cdc-wdm0` i interfejs danych `wwan0` mogą mieć różne nazwy. Następnie atomowo odświeża zbiór `wan_ifaces` oraz plik `/run/pi-router/wan-resolv.conf` z DNS operatora. Źródło: [NetworkManager IpInterface](https://www.networkmanager.dev/docs/api/latest/gdbus-org.freedesktop.NetworkManager.Device.html).

Wykluczone są `usb0`, `eth0`, `wlan0` i `lo`. Modem udający zwykły Ethernet/RNDIS wymaga świadomego wskazania UUID jego profilu w `/etc/pi-router/router.conf`. Nie ustawiaj tam UUID portu LAN ani administracyjnego USB.

Dispatcher NetworkManagera odświeża stan po połączeniu, rozłączeniu i zmianie parametrów DHCP. Przeładowanie firewalla także odtwarza zbiór. Bez modemu plik DNS nie ma serwerów zewnętrznych; lokalna nazwa routera nadal działa. W realnym teście T-Mobile potwierdzono `ppp0` i dwa serwery DNS. Parser obsługuje wiele adresów na jednej linii rozdzielonych przez ` | `.

## Ethernet i USB

Profil `pi-iphone-lan` przypisuje `192.168.76.1/24` do `eth0`, nie dodaje bramy domyślnej i wyłącza IPv6 dla tego LAN. Priorytet autopołączenia wynosi 1000. Konfiguracja ignorowania braku kabla pozwala przygotować adres i usługę przed podłączeniem telefonu.

Usługa `pi-lan-dnsmasq` działa tylko na prywatnym Ethernecie. Przydziela adresy `.50–.150` na godzinę; brama i DNS to `.1`. Nie uruchamiano ogólnej usługi `dnsmasq.service`, która mogłaby kolidować z DHCP interfejsu USB.

USB nadal używa fabrycznego profilu `USB Gadget (shared)` oraz mechanizmu `rpi-usb-gadget`. Plik `99-usb-admin-only.conf` usuwa z odpowiedzi DHCP na USB opcje bramy i DNS. Mac ma traktować ten kabel jako połączenie administracyjne. Nazwa profilu „shared” nie oznacza, że firewall udostępnia Macowi Internet. Reguła z tagiem interfejsu opiera się na [mechanizmie tagów dnsmasq](https://thekelleys.org.uk/dnsmasq/docs/dnsmasq-man.html).

## Pliki sieci i firewalla

| Plik na Pi | Zadanie |
|---|---|
| `/etc/nftables.conf` | Własna tabela, reguły i NAT |
| `/etc/systemd/system/nftables.service.d/pi-router.conf` | Przeładowanie i zatrzymanie dotyczą tylko własnej tabeli |
| `/etc/sysctl.d/90-pi-router-forwarding.conf` | IPv4 forwarding; wyłączone przekazywanie IPv6 i wysyłanie redirectów |
| `/etc/NetworkManager/system-connections/pi-iphone-lan.nmconnection` | Statyczny LAN dla iPhone’a |
| `/etc/NetworkManager/conf.d/90-pi-lan-carrier.conf` | Adres LAN również przy odłączonym kablu |

## Pliki usług i diagnostyki

| Plik lub grupa | Zadanie |
|---|---|
| `/etc/pi-router/dnsmasq-lan.conf`, `/etc/systemd/system/pi-lan-dnsmasq.service` | DHCP i DNS dla iPhone’a |
| `/etc/pi-router/router.conf` | Opcjonalny UUID modemu RNDIS |
| `/usr/local/sbin/pi-router-wan`, `/etc/NetworkManager/dispatcher.d/90-pi-router-wan` | Aktualizacja interfejsu modemu i DNS |
| `/usr/local/sbin/pi-router-firewall`, `/usr/local/bin/pi-status` | Bezpieczne przeładowanie i diagnostyka |
| `/etc/NetworkManager/dnsmasq-shared.d/99-usb-admin-only.conf` | Brak bramy i DNS w DHCP administracyjnego USB |

Kopie plików są w `config/` i `scripts/` na Macu. Stan przed zmianami znajduje się na Pi w `/root/pi-router-backup-20261003` oraz w lokalnym `backups/pi-before-router.tar.gz`.

## Sprawdzanie i przeładowanie

Na Pi:

```bash
sudo nft -c -f /etc/nftables.conf
sudo systemctl reload nftables
sudo nft list table inet pi_router
```

Po zmianie reguł zawsze otwórz nowe, niezależne połączenie z Maca:

```bash
ssh -o ControlPath=none pi-usb hostname
```

Istniejąca sesja może działać dzięki śledzeniu połączeń nawet wtedy, gdy nowe logowania zostały przypadkowo zablokowane.

## Cofnięcie pierwotnej konfiguracji routera

Ta operacja usuwa LAN/DHCP i filtr routera, odtwarza poprzednie pliki oraz zostawia zainstalowane pakiety i klucz SSH. Nie cofa późniejszych ustawień UART ani profilu T-Mobile, opisanych w [rozdziale modemu](03-MODEM-I-ZASILANIE.md). Używaj jej świadomie, gdy chcesz wrócić do samego dostępu USB:

```bash
sudo python3 /root/pi-router-backup-20261003/rollback-router.py
```

Przed ryzykowną zmianą można zaplanować to cofnięcie na dwie minuty później. Wykonaj na Pi:

```bash
ROLLBACK_UNIT="router-rescue-$(date +%s)"
sudo systemd-run --unit="$ROLLBACK_UNIT" --on-active=2m \
  /usr/bin/python3 /root/pi-router-backup-20261003/rollback-router.py
```

Po poprawnym teście nowej sesji SSH anuluj timer w pierwszym terminalu:

```bash
sudo systemctl stop "$ROLLBACK_UNIT.timer"
```

To cofnięcie do stanu sprzed całego wdrożenia, a nie archiwum każdej przyszłej edycji. Przed dalszym rozwojem wykonaj nową kopię działającej konfiguracji.


## Zakres projektu — draft do komisji

[Wizja i plan rozwoju](08-WIZJA-I-PLAN-PROJEKTU.md) opisuje telefon po kablu z wyłączonymi radiami, planowany Tor z mostami, panel filtrów i komunikacji oraz miniaturyzację (PCB i CAD). To pierwotny zakres projektu; późniejszy stan panelu, CAD i demonstracji Tora opisuje [STATUS](docs/STATUS.md). [Krótki draft PDF](projekt/Draft-projektu.pdf).
