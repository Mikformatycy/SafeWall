# Outro SafeWall

[Animacja HTML — działa bez MP4](src/outro.html) · [Plansza PNG](poster-landscape.png)

Plik MP4 jest lokalnym eksportem i nie trafia do Gita. Po renderowaniu [odtwarzacz i pobieranie](index.html) otwiera gotowe wideo.

Logo [4A](../../brand/svg/safewall-logo.svg) z nazwą SafeWall i podpisem **„Bo za każdą historią stoi człowiek.”**. Ciemne tło, delikatna fioletowa poświata, płynne wejście i pojedynczy ukośny light sweep. Docelowy format: poziomy 1920 × 1080 (16:9), 6,2 s, 60 fps, H.264, yuv420p, bez dźwięku.

Animacja bazuje na lokalnym `PlatinumCode/marketing/outro/src/outro.html`: wejście logo 900 ms, wejście podpisu 900 ms z opóźnieniem 450 ms, sweep od 2700 ms przez 3600 ms, easing `cubic-bezier(.85,0,.15,1)`, maska 45° o szerokości 300%. Tak jak we wzorcu refleks jest przyciemnioną kopią znaku odsłanianą przez maskę. Nazwa, symbol i podpis mają jeden wspólny pas. Oryginalna muzyka i materiały LeafLoop nie zostały skopiowane.

## Edycja i renderowanie

- [src/outro.html](src/outro.html) — źródło animacji; domyślnie poziome.
- [render.mjs](render.mjs) — deterministyczny rendering klatek w Chromium i kodowanie przez ffmpeg. Czyta wzorcowy SVG bez duplikowania jego ścieżek.
- [index.html](index.html) — odtwarzacz i pobieranie docelowego pliku poziomego.

Wymagania: Node.js, Playwright z Chromium oraz `ffmpeg` w PATH. Uruchom z katalogu projektu:

```sh
node marketing/outro/render.mjs
```

Jeśli Playwright nie jest zainstalowany lokalnie, `PLAYWRIGHT_MODULE` może wskazywać jego `index.mjs`. Domyślnie renderowana jest wersja `landscape` oraz plansza `poster-landscape.png`. Wcześniejszy plik pionowy pozostał jako archiwalna wersja bez podpisu; nie jest prezentowany w odtwarzaczu. Renderer zachowuje opcjonalne argumenty `portrait` i `all` do przyszłego użycia.

Przykład z osobno zainstalowanym Playwrightem:

```sh
PLAYWRIGHT_MODULE=/sciezka/do/playwright/index.mjs node marketing/outro/render.mjs landscape
```

Samodzielne źródło HTML skaluje animację do okna; po otwarciu odtwarza ją jednokrotnie. Przeładuj stronę, aby powtórzyć. Wymagania i wykluczenia repo: [REPOZYTORIUM.md](../../docs/REPOZYTORIUM.md).
