# System i połączenia

> Zapis historyczny testów prototypu z 3 października 2026. Opis połączeń i wdrożeń odnosi się do czasu próby. Aktualny stan projektu, dashboardu i deklaracji dotyczących Tora: [STATUS](docs/STATUS.md). Surowe logi oraz kopie są lokalne.

**Stan historyczny po teście Maca (3 października, 18:25): modem zasilany przez USB-A huba przy MacBooku, QMI przywrócone; nie jest obecnie połączony z Raspberry Pi.** USB i AT działają. ECM na Macu uzyskał DHCP, lecz nie przekazywał Internetu. Wewnętrzny HTTP modemu także zakończył się timeoutem. SIM wymaga PIN-u przy kolejnym uruchomieniu połączenia, licznik prób wynosi 3. Szczegóły: [test modemu na Macu](06-MODEM-NA-MACU.md).

## Docelowa topologia

```text
Sieć operatora
      │
SIM i antena → PiTalk modem HAT
                     │ kabel USB-C modemu → USB-A Pi, QMI
               Raspberry Pi 4
                 │        │
            eth0 │        │ usb0 przez port USB-C Pi
                 │        └── MacBook: SSH i obecne zasilanie Pi
            kabel RJ45
                 │
        adapter Ethernet → USB-C
                 │
               iPhone

Waveshare UPS HAT: przyszłe zasilanie, jeszcze nieuruchomione.
```

Modem PiTalk i Waveshare UPS HAT to dwa różne urządzenia. PiTalk rozpoznano jako Quectel EG25-G. Docelowo dane idą przez USB/QMI między modemem a Pi; wcześniejszy wariant GPIO14/15 + UART/PPP pozostaje skonfigurowany jako zapasowy. Użytkownik fizycznie odłączył PiTalk od GPIO; podczas testów routera pozostał wyłącznie przewód USB do Pi, zapewniający dane i zasilanie modemu. Na czas późniejszego testu modem przełożono do Maca. Konfiguracja UART jest zachowana, ale bez połączenia GPIO nie może działać. Rewizja płytki HAT i dokładny model UPS pozostają nieustalone.

## Wykryty sprzęt

| Element | Wartość potwierdzona |
|---|---|
| Płyta | Raspberry Pi 4 Model B Rev 1.4 |
| RAM | Około 3,7 GiB widoczne w systemie, wariant 4 GB |
| Karta | 63,2 GB nominalnie; główny system plików około 58 GiB |
| Architektura | `aarch64`, 64 bity |
| Zasilanie podczas konfiguracji | Wyłącznie USB-C z MacBooka, zgodnie z informacją użytkownika |

Podczas konfiguracji `vcgencmd get_throttled` zwracał `0x0`; temperatura wynosiła około 42–47°C. Były to pomiary przy małym obciążeniu. Późniejszy krótki test Internetu LTE również zakończył się wynikiem `0x0`; nie wykonano długiego testu zasilania pod obciążeniem.

## System i podstawowe pakiety

| Składnik | Wersja lub rola |
|---|---|
| Obraz | Raspberry Pi OS Lite 64-bit, wydanie 2026-09-15 |
| Baza systemu | Debian GNU/Linux 13 Trixie, `/etc/os-release` zgłaszał 13.7 |
| Kernel | `6.18.50+rpt-rpi-v8` |
| NetworkManager | `1.52.1-1+rpt4`; zarządza połączeniami sieciowymi |
| rpi-usb-gadget | `1.0.6`; Ethernet USB między Pi a Maciem |

| Składnik routera | Wersja lub rola |
|---|---|
| nftables | `1.1.3-1`; filtr i NAT |
| dnsmasq-base | `2.91-1+deb13u2`; osobna instancja DHCP/DNS dla Ethernetu |
| ModemManager | `1.24.0-1+deb13u1`; wykrywanie i obsługa modemów |
| Narzędzia QMI i MBIM | `libqmi-utils`, `libmbim-utils`; diagnostyka właściwego interfejsu modemu |
| Narzędzia diagnostyczne | `tcpdump`, `dig`, `ip`, `nmcli`, `mmcli` |

Nie wykonywano pełnej aktualizacji systemu ani firmware. Historia instalacji pakietów jest w `logs/02-package-install.txt`.

## Interfejsy i adresacja

| Interfejs na Pi | Funkcja | Adres i zachowanie |
|---|---|---|
| `usb0` | Administracja z Maca | `10.12.194.1/28`; DHCP dla Maca, SSH, mDNS |
| `eth0` | Prywatny LAN iPhone’a | `192.168.76.1/24`; DHCP, DNS, brama do modemu |
| `wlan0` | Radio Wi-Fi wyłączone | Profil hotspotu zachowany; nie służy do administracji ani przekazywania ruchu iPhone’a |
| `wwan0` | Aktywny WAN T-Mobile LTE | USB/QMI, sterowanie `cdc-wdm0`, profil `tmobile-pitalk-usb`; adres i DNS od operatora |
| `ppp0` | Zapasowy wariant WAN | Pojawia się po ręcznej aktywacji UART `tmobile-pitalk`; podczas używania USB nie jest aktywny |

Mac podczas pierwszego testu miał adres `10.12.194.6`, a interfejs USB nazywał się `en11`. Są to wartości dynamiczne. Stałym celem SSH jest adres Pi `10.12.194.1`.

Nazwa hosta to `piotr4mmc-raspberrypi`. Nazwa mDNS `piotr4mmc-raspberrypi.local` jest pomocnicza; alias `pi-usb` używa bezpośrednio adresu USB.

## Co dzieje się z pakietem iPhone’a

1. iPhone otrzymuje adres, maskę, bramę i DNS z DHCP na `eth0`.
2. Zapytania DNS trafiają do dnsmasq na `192.168.76.1`; serwery zewnętrzne pochodzą z aktywnego połączenia modemu.
3. nftables przepuszcza pakiety z LAN tylko do interfejsów obecnych w zbiorze `wan_ifaces`.
4. NAT zamienia adres źródłowy iPhone’a na adres interfejsu modemu; odpowiedzi wracają dzięki śledzeniu połączeń.
5. Bez aktywnego modemu zbiór jest pusty i przekazywanie ruchu jest blokowane. LAN, DHCP, lokalny DNS i SSH mogą nadal działać.

Router obsługuje obecnie LAN IPv4. Nie wdrożono delegacji prefiksu IPv6 ani routingu IPv6 do iPhone’a.


## Zakres projektu — draft do komisji

[Wizja i plan rozwoju](08-WIZJA-I-PLAN-PROJEKTU.md) opisuje telefon po kablu z wyłączonymi radiami, planowany Tor z mostami, panel filtrów i komunikacji oraz miniaturyzację (PCB i CAD). To pierwotny zakres projektu; późniejszy stan panelu, CAD i demonstracji Tora opisuje [STATUS](docs/STATUS.md). [Krótki draft PDF](projekt/Draft-projektu.pdf).
