# Konfiguracja bazowego routera

Stan plików `config/`: wcześniejsza baza NAT z 3 października. Nowsza deklaracja i nagranie Tora nie zostały jeszcze odtworzone w tych plikach. [Aktualny status](STATUS.md). Nie wdrażaj tej bazy na działającej chronionej bramie bez uzgodnienia konfiguracji; zastąpiłaby jej reguły wcześniejszym NAT.


Baza: Raspberry Pi 4, Raspberry Pi OS Lite 64-bit (Debian Trixie), NetworkManager, nftables, dnsmasq i ModemManager. Modem PiTalk EG25-G jest połączony przez USB/QMI; `cdc-wdm0` steruje modemem, `wwan0` przenosi pakiety.

## Adresacja i działanie

| Port | Rola | Adres |
|---|---|---|
| usb0 | SSH z Maca, osobny USB-C Pi | 10.12.194.1/28 |
| eth0 | Prywatny Ethernet telefonu | 192.168.76.1/24 |
| wwan0 | Łącze komórkowe | Przydział operatora |

DHCP telefonu: 192.168.76.50–150; brama i DNS: 192.168.76.1. Ethernet jest prywatnym LAN z DHCP i nie powinien być wpinany do wspólnego switcha hackathonu. USB administracyjne nie udostępnia internetu Macowi.

Zapora zarządza wyłącznie tabelą `inet pi_router`, zachowując reguły NetworkManagera. Pozwala na SSH po USB, DHCP/DNS w odpowiednich segmentach, ruch powrotny oraz LAN → aktywny modem. NAT dotyczy IPv4 LAN. Brak aktywnego modemu oznacza pusty zbiór WAN i brak przekazywania. To zabezpieczenie routera, nie blokada awarii Tora. Ruch wychodzący samego Pi nie jest ograniczony do Tora.

## Pliki i docelowe ścieżki

| Plik w repozytorium | Miejsce na Pi |
|---|---|
| config/nftables.conf | /etc/nftables.conf |
| config/pi-router.conf | /etc/pi-router/router.conf |
| config/dnsmasq-lan.conf | /etc/pi-router/dnsmasq-lan.conf |
| config/pi-lan-dnsmasq.service | /etc/systemd/system/pi-lan-dnsmasq.service |
| config/pi-router-nftables-override.conf | /etc/systemd/system/nftables.service.d/pi-router.conf |
| config/90-pi-router-forwarding.conf | /etc/sysctl.d/90-pi-router-forwarding.conf |
| config/99-usb-admin-only.conf | /etc/NetworkManager/dnsmasq-shared.d/99-usb-admin-only.conf |
| scripts/pi-router-firewall | /usr/local/sbin/pi-router-firewall |
| scripts/pi-router-wan | /usr/local/sbin/pi-router-wan |
| scripts/90-pi-router-wan | /etc/NetworkManager/dispatcher.d/90-pi-router-wan |

To mapa konfiguracji, nie uniwersalny instalator. Przed wdrożeniem potrzebne są kopie istniejących plików i działające SSH po USB. Skrypty mają być własnością root, wykonywalne i niezapisywalne przez innych użytkowników. Utwórz katalog `/var/lib/pi-router` na dzierżawy DHCP. Sprawdź wersję nftables: reguły używają `destroy table`.

## Profile NetworkManagera

Skonfiguruj eth0 ręcznie jako 192.168.76.1/24 bez trasy domyślnej, z wyłączonym IPv6. Skonfiguruj oddzielny profil GSM dla cdc-wdm0 z APN właściwym dla SIM, metryką IPv4 50, wyłączonym IPv6 i autopołączeniem wyłączonym. Nie zapisuj PIN-u w repozytorium ani poleceniach; połączenie uruchamiaj przez `nmcli --ask`. W prototypie użyto APN `internet` dla T-Mobile; nie jest to uniwersalne ustawienie operatorów.

Tryb USB gadget i SSH trzeba uruchomić wcześniej w konfiguracji systemu Raspberry Pi. Hostname powinien być unikatowy. Prywatne UUID profili i dane karty nie są częścią repozytorium.

Po rozmieszczeniu plików i przygotowaniu profili sprawdź `nft -c -f /etc/nftables.conf` oraz `dnsmasq --test --conf-file=/etc/pi-router/dnsmasq-lan.conf`. Dopiero po sprawdzeniu konfiguracji przeładuj systemd, zastosuj ustawienia sysctl, uruchom nftables, odśwież `pi-router-wan` i uruchom `pi-lan-dnsmasq`. Nie zmieniaj zapory przez połączenie, którego nowe reguły nie dopuszczają.

## Testy

`tests/test-router-isolated.py` uruchamia 11 testów w tymczasowych przestrzeniach sieciowych Linux: m.in. SSH po USB, izolację segmentów, NAT, blokadę bez WAN, DNS i pełną wymianę DHCP. Wymaga uprawnień root, iproute2, nftables, dnsmasq, dig, tcpdump, Python 3, wdrożonych plików w `/etc` i istniejącej tabeli NetworkManagera `ip nm-shared-usb0`.

```sh
sudo python3 tests/test-router-isolated.py
```

Test był wykonany podczas przygotowania prototypu. Nie jest testem SIM, radia, adaptera iPhone’a ani Tora. Przy aktualizacji repozytorium sprawdzono składnię i testy dashboardu; nie powtarzano testów routera na sprzęcie. Na macOS nie uruchamiaj testu wymagającego przestrzeni sieciowych Linux.

## Cofanie wdrożenia

Przywróć własne kopie konfiguracji i profili NetworkManagera, usuń wyłącznie własne usługi i nadpisania, przeładuj systemd oraz odtwórz poprzednie ustawienia sysctl. Nie używaj `nft flush ruleset`: usuwa także cudze reguły. Archiwum konkretnego urządzenia pozostaje lokalne i nie jest publikowane.
