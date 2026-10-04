# Skrypty projektu

| Grupa | Zastosowanie |
| --- | --- |
| `pi-router-wan`, `pi-router-firewall`, `90-pi-router-wan` | Obsługa bazowego routera na Linuxie; mapa instalacji w [konfiguracji](../docs/KONFIGURACJA.md) |
| `pi-status`, `probe-pitalk-uart.py`, `test-uart-speed.py`, `mac-usb-at.py` | Diagnostyka konkretnego prototypu; skrypty UART/AT wymagają właściwego portu i wyłącznego dostępu do modemu |
| `prepare-router.py`, `rollback-router.py` | Historyczne wdrożenie i odtwarzanie kopii z 3 października. Mają ścieżki konkretnego urządzenia i wymagają prywatnych profili; nie są uniwersalnym instalatorem |
| `build-project-pdf.py` | Buduje 2-stronicowy PDF z `projekt/Draft-projektu.md` i oficjalnego SVG |
| `export-public-repo.py` | Selektywny eksport do checkoutu; domyślnie tylko plan, zapis po `--write` |

`test-router-isolated.py` (także pod dotychczasową ścieżką `tests/`) wymaga Linuxa, root i przygotowanej konfiguracji. Sprawdza bazowy NAT, izolację, DHCP/DNS i brak przekazywania bez WAN. Nie sprawdza Tora ani modemu. Synchronizacja repozytorium nie wykonuje tych skryptów na Pi.

PDF: utwórz własne środowisko Python i zainstaluj `requirements-pdf.txt`. Skrypt draftu szuka Arial na macOS albo DejaVu Sans na Linuxie; można podać `SAFEWALL_FONT_REGULAR` i `SAFEWALL_FONT_BOLD`. Prezentacja używa osobno systemowych fontów macOS.
