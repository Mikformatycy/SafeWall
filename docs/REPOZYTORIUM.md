# Co publikujemy w repozytorium

Repozytorium publiczne: https://github.com/Mikformatycy/SafeWall.

## Pliki źródłowe i gotowe materiały

Publikujemy kod dashboardu, testy, kontrakt API, bazową konfigurację routera, skrypty diagnostyczne, dokumentację, źródła generatorów oraz aktualne materiały marki. `dashboard/dist/` jest katalogiem źródeł aplikacji, dlatego jest śledzony. `Podglad.html` jest celowo dołączonym eksportem offline; odtwarza go `npm run build`.

Materiały obejmują logo SVG/PNG/ICO, małą paczkę brand kit, cover JPG/PNG, PDF-y z generatorami, źródło HTML outro i wybrane rendery CAD. W CAD publikujemy niewielkie eksporty własnego studium A/B, skrypty i dokumentację. Złożone sceny Blendera i szczegółowy import Fusion zawierający zewnętrzne modele pozostają w lokalnym archiwum.

## Co pozostaje lokalnie

- Surowe logi sieciowe, kopie konfiguracji urządzeń, profile NetworkManagera, klucze, certyfikaty instalacyjne i dane SIM.
- MP4/MOV, ścieżki audio, sekwencje klatek, cache, raporty wykonania `.log` i kopie `.blend1`.
- Duże sceny `.blend`, szczegółowy eksport Fusion v02 oraz oryginalne modele/dokumenty dostawców.
- Środowiska Python/Node, zrzuty testowe `.artifacts/` i niewybrane propozycje logo w `output/`.

To wykluczenia z Gita, nie kasowanie lokalnych materiałów. Nie uruchamiamy Git LFS ani publikacji filmu w ramach synchronizacji kodu.

## Odtwarzanie materiałów

| Materiał | Źródło i wymagania |
| --- | --- |
| Dashboard | `cd dashboard && npm run build`; Node.js ≥20, bez zależności npm |
| Eksporty logo | `node brand/build.mjs`; Playwright/Chromium i Python/Pillow, opcjonalnie `PLAYWRIGHT_MODULE` i `PYTHON` |
| Draft PDF | `python scripts/build-project-pdf.py`; zależności w `scripts/requirements-pdf.txt`, Arial na macOS lub DejaVu Sans na Linuxie |
| Prezentacja | `python projekt/prezentacja/build.py`; te same biblioteki, fonty SF Rounded/SF Mono z macOS, źródła obrazów w repo |
| Outro | `node marketing/outro/render.mjs`; Playwright/Chromium i ffmpeg; MP4 powstaje lokalnie. Sam HTML pozwala obejrzeć animację bez renderowania |

Film v22 nie jest samowystarczalnym buildem po sklonowaniu: wymaga lokalnych nagrań, audio, scen i referencji. W repo są scenariusz, timingi, skrypty, raporty i contact sheet. Instrukcje historycznych skryptów CAD/filmowych mogą wymagać konkretnego środowiska Fusion/Blendera i przywrócenia lokalnych assetów. Nie są częścią instalacji dashboardu.

## Aktualizacja z folderu roboczego

`scripts/export-public-repo.py` kopiuje jawnie wybrane pliki do istniejącego checkoutu. Nie wykonuje commitów, pushów ani usuwania plików. Przed zapisem sprawdza rozmiary i typowe formaty sekretów; pomija dane lokalne oraz zachowuje istniejącą historię Gita. Domyślnie pokazuje tylko plan:

```sh
python3 scripts/export-public-repo.py --destination ../SafeWall
python3 scripts/export-public-repo.py --destination ../SafeWall --write
```

Eksport utrzymuje kompatybilne kopie dawnych ścieżek dokumentów. Odnośniki Markdown do celowo niepublikowanych materiałów zmienia w opis ścieżki lokalnej. Raport `docs/publication-manifest.json` zawiera listę i hashe opublikowanych plików. Po eksporcie przejrzyj diff, wykonaj testy i dopiero wtedy zatwierdź zmiany.
