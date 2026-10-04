SAFEWALL — NAPISY KARAOKE

NAŁÓŻ NAPISY NA KOLEJNY FILM (z katalogu repozytorium)

  rtk python3 marketing/captions/run.py apply "/pełna/ścieżka/nowy-film.mp4"

Powstanie nowy-film-captions.mp4 oraz raport walidacji. Nie wymaga klucza API
ani ponownej transkrypcji. Rozmiar napisów dopasowuje się do rozdzielczości.
Lektor musi pozostać w tych samych miejscach. Jednolite przesunięcie można
skompensować np. --offset 1.5. Zmiana cięć lektora wymaga nowego dopasowania.
Opcja --output wybiera ścieżkę wyniku, --crf jakość kodowania (domyślnie 18).

STYL I METODA

Wzorzec: /Users/piotrek/Desktop/Coding/PlatinumCode/marketing/001_night_queue/subs_src
Whisper -> zatwierdzony tekst i krótkie frazy -> HTML/CSS w Chrome -> przezroczyste
PNG z podświetleniem słowa -> jeden overlay FFmpeg. HTML rasteruje same napisy;
nie tworzy plansz w filmie. Helvetica Neue bold 700, biały tekst #FFFFFF,
aktywne słowo #3ECF8E, ciemny obrys #161A13, letter-spacing 0,01 em.
W poziomym kadrze 540p tekst ma 32 px, dolny margines 38 px; bez prostokątnego tła.
Z wzorca zachowano offset -0,2 s i maksymalny ogon frazy 0,5 s.

EDYCJA

style.json              kolory, font, pozycja, rozmiar i przesunięcie
caption-lines.txt       podział zatwierdzonego tekstu na 41 fraz
timing-corrections.json udokumentowane korekty 17 granic słów
events.json            119 zdarzeń podświetlenia i pełne znaczniki czasu
SafeWall-captions.srt   zwykłe napisy do edytora/odtwarzacza

  rtk python3 marketing/captions/run.py build

Odtwarza JSON i SRT bez sieci. Skrypt sprawdza dokładną zgodność tekstu z
physical-design/visualization/VOICEOVER-APPROVED-v22.txt. Przywraca pisownię
„SafeWall”, „Wi-Fi”, „Nietrudno” i interpunkcję; nie dodaje słów od siebie.
Whisper dał 125 tokenów ze znakami interpunkcyjnymi. Granice odbiegające o ponad
220 ms lub prawie zerowe porównano z istniejącym, zweryfikowanym dopasowaniem
słów lektora v22. Wyjątki są zapisane jawnie w timing-corrections.json.
Podczas demonstracji napisy znikają w przerwie lektora 59,58–64,12 s.

ŚRODOWISKO

Python 3 (stdlib), Node.js, FFmpeg/FFprobe, RTK i Google Chrome.
  rtk npm ci --prefix marketing/captions
Chrome: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
Zmienna CHROME_PATH pozwala wskazać inną lokalizację. Helvetica Neue pochodzi
z macOS; na innym systemie może wystąpić font zastępczy.
Cache PNG w renders/ zależy od tekstu, stylu, kodu i rozdzielczości.

TRANSKRYPCJA — TYLKO GDY ZMIENI SIĘ AUDIO

  rtk python3 marketing/captions/transcribe.py --audio "/ścieżka/lektor.wav" --force

Klucz podaje się w ukrytym monicie lub przez OPENAI_API_KEY; nie jest zapisywany.
Wysyłana jest sama ścieżka lektora do api.openai.com. Zapisywane są whisper.json
i hash źródła. Przy nowym tekście zaktualizuj też CANONICAL w run.py,
caption-lines.txt i timing-corrections.json; nie używaj korekt starego głosu.
Model whisper-1, język pl, verbose_json, znaczniki word i segment.
Oficjalna dokumentacja sprawdzona 2026-10-04:
https://developers.openai.com/api/docs/guides/speech-to-text

WERYFIKACJA

Pełne dekodowanie wyniku, rozdzielczość, fps, liczba klatek i czas.
Hash skompresowanego audio przed i po nakładaniu napisów musi być identyczny;
dźwięk jest kopiowany bez ponownego kodowania. Źródłowy film pozostaje zachowany.
Kontrola układu PNG sprawdza, czy tekst nie wychodzi poza kadr.
