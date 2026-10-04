SafeWall — oficjalne logo 4A

Wzorzec: svg/safewall-logo.svg (dwie ścieżki, bez bitmapy).
Kolory: #7D67E9 (korpus), #B39AFB (blanki).
Nagłówek strony: przezroczysty SVG bez kwadratowego tła.
Favicon: icons/favicon.svg i icons/favicon.ico.
Apple: icons/apple-touch-icon.png — nieprzezroczyste grafitowe tło.
Monochromatyczne: svg/safewall-logo-white.svg i safewall-logo-ink.svg.
PNG z tłem: png/dark, png/black, png/light. Przezroczyste: png/transparent.
PNG bez kwadratowego marginesu: png/logo.
Wariant maskowalny mieści znak w centralnym obszarze bezpieczeństwa.
Nie rozciągaj proporcji ani nie dodawaj gradientu, cienia lub tarczy.

Rebuild: node brand/build.mjs z katalogu projektu.
Wymagania: Playwright i Python z Pillow; PLAYWRIGHT_MODULE oraz PYTHON
mogą wskazywać lokalne instalacje. Następnie npm run build w dashboard/.
Dokument PDF: python scripts/build-project-pdf.py (reportlab i svglib).
