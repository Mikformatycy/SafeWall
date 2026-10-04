# SafeWall — start lokalny

**Aktualny stan projektu:** [docs/STATUS.md](docs/STATUS.md). [README](README.md) zawiera przegląd całego repozytorium, a [spis dokumentacji](docs/README.md) prowadzi do szczegółów.

## Dashboard na Macu

```sh
cd dashboard
npm run dev:safari
```

Adres: http://127.0.0.1:4173. Serwer musi działać w Terminalu. Dane są symulowane; panel nie jest jeszcze wdrożony na Pi. Bez serwera otwórz `dashboard/Podglad.html`. `safewall.local` pozostaje nazwą docelową.

## Materiały do pokazania

- [Prezentacja dla jury](projekt/prezentacja/SafeWall-prezentacja.pdf) i [draft PDF](projekt/Draft-projektu.pdf).
- [Logo 4A i eksporty](brand/index.html) oraz [wzorcowe SVG](brand/svg/safewall-logo.svg).
- [Cover JPG 4:3](marketing/cover/safewall-cover-4x3-v1.jpg) i [źródło animacji outro](marketing/outro/src/outro.html).
- [CAD i wizualizacja](physical-design/README.md), [materiały marketingowe i film v22](marketing/README.md).

## Administracja prototypem

Lokalne skróty Maca `Polacz.command` i `Diagnoza.command` są związane z konfiguracją tego stanowiska; nie są częścią publicznego checkoutu. Alias `pi-usb` oraz prywatny klucz trzeba przygotować osobno.

```sh
ssh pi-usb
```

Na Pi: `sudo pi-status`. USB administracyjne ma adres 10.12.194.1, a prywatny Ethernet telefonu 192.168.76.1/24. Ethernet uruchamia DHCP i nie powinien być podłączany do współdzielonego switcha.

Rozdziały 01–07 dokumentują wcześniejsze testy z 3 października, w tym timeouty modemu. Nie oznaczają aktualnego stanu fizycznych połączeń. Nowsza demonstracja i deklaracja działania Tora nie zostały jeszcze uzgodnione z plikami NAT w `config/`.

## GitHub

https://github.com/Mikformatycy/SafeWall — publiczny kod, dokumentacja i wybrane materiały. Folder roboczy oraz checkout są oddzielne; eksport i wykluczenia opisuje [docs/REPOZYTORIUM.md](docs/REPOZYTORIUM.md). Logi, backupy, profile SIM, klucze i ciężkie multimedia pozostają lokalne.
