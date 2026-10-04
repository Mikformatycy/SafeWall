SAFEWALL — PREZENTACJA DLA JURY

Plik: SafeWall-prezentacja.pdf
Format: 16:9, 8 stron, tekst i logo wektorowe, polskie znaki.
Odbiorca: jury hackathonu czytające samodzielnie.

NARRACJA
Teksty dostosowane do zatwierdzonego VOICEOVER-APPROVED-v14.txt,
użytego w nagraniu Daniela v16. Główne motywy: powierzona historia,
„iPhone (Piotrek)” w kontekście AirDrop dla wszystkich, kontrola poza
telefonem, zasada Tor albo brak połączenia, forma powerbanku i finał
„Bo za każdą historią stoi człowiek”. Zasada odcięcia po awarii jest
oznaczona jako cel do weryfikacji. Oznaczenia sekcji w prawym górnym
rogu oraz cała stopka zostały usunięte zgodnie z życzeniem użytkownika.

Budowanie:
  python3 projekt/prezentacja/build.py

Wymagania: macOS z fontami SFNSRounded/SFNSMono, Python i biblioteki
z scripts/requirements-pdf.txt. Gotowy PDF można czytać na dowolnym systemie.
Podglądy testowe preview/ pozostają lokalne. Do pełnej weryfikacji:
  mkdir -p projekt/prezentacja/preview
  pdftocairo -png -scale-to 1600 projekt/prezentacja/SafeWall-prezentacja.pdf projekt/prezentacja/preview/slajd
  python3 projekt/prezentacja/verify.py

WZORZEC WIZUALNY
RainbowKit: https://rainbowkit.com
Czarne tło, SF Rounded, duże białe nagłówki, karty z zaokrągleniami,
niebiesko-fioletowe gradienty i miękka poświata.
Zachowane logo SafeWall 4A z brand/svg/safewall-logo.svg.
Ikona Tora na slajdzie 4: współczesny Onion Glyph, osadzony wektorowo.
Rozmiar 36 × 36 i fiolet #B39AFB dopasowane do pozostałych ikon.
Oryginalny plik: reference/tor-onion-glyph.svg.
Źródło: https://github.com/torproject/styleguide/blob/main/assets/static/images/tor-browser/glyph/glyph.svg
Źródła stylu zweryfikowane 2026-10-04:
https://github.com/rainbow-me/rainbowkit/blob/main/site/css/tokens.ts
https://github.com/rainbow-me/rainbowkit/blob/main/site/pages/index.tsx
https://github.com/rainbow-me/rainbowkit/blob/main/site/components/Hero/Hero.tsx

ZRZUTY STRONY
reference/rainbowkit-hero.png, rainbowkit-components.png, rainbowkit-mobile.png
to lokalne kopie zrzutów Playwright z dashboard/.artifacts/ (poza Gitem).
Obejrzano je podczas przygotowania prezentacji.
Próba wykonania nowych zrzutów w tej sesji zakończyła się blokadą Chromium:
bootstrap_check_in / MachPortRendezvousServer / Permission denied (1100).
capture-reference.cjs zawiera skrypt do ponownego przechwycenia strony
w środowisku pozwalającym uruchomić przeglądarkę. Nie wykonano nowych zrzutów.

MATERIAŁY I STATUS DANYCH
Konstrukcja: physical-design/layout-study-results.json — wariant B 70×110×24 mm.
Masa kompletnego zestawu: brak pomiaru lub pełnego oszacowania.
Czas pracy 2 h: cel w physical-design/design-brief.json, nie pomiar.
Render obudowy i widok rozłożony: physical-design/visualization/*-preview-v04.png.
Rendery są koncepcją; obudowy i archiwalne sceny pozostawiono bez zmian.
Nagranie prototypu: physical-design/references/live-demo-v13/README.txt i kadry.
Nowszy materiał pokazuje zmianę wyniku Tor Check; użytkownik potwierdził Tora.
Nie traktowano nagrania jako audytu całości ruchu, wycieków ani obsługi awarii.
Panel: dashboard/README.md — interfejs używa danych demo.

FILM
Zgodnie z dyspozycją użytkownika strona 2 zaprasza do obejrzenia gotowego filmu,
zaraz po wprowadzeniu, przed omówieniem problemu i szczegółów projektu.
Kod QR, link oraz przycisk „Obejrzyj film” prowadzą do https://youtube.com/.
To roboczy adres wskazany przez użytkownika. Slajd nie zawiera komunikatów
o przygotowaniu filmu ani o tymczasowym linku.
Po publikacji filmu należy podmienić adres w linku i kodzie QR.

Źródła techniczne wykorzystane przy redakcji (linki do Apple usunięto z PDF):
https://support.apple.com/en-gb/108785
https://support.apple.com/guide/security/airdrop-security-sec2261183f4/web
https://support.torproject.org/tor-browser/security/using-tb-safely/
Repozytorium projektu: https://github.com/Mikformatycy/SafeWall
