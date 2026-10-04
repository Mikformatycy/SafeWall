SAFEWALL — BLENDER PREVIEW v20

ODTWÓRZ: SafeWall-launch-preview-v20.mp4
71,00 s / 960×540 / 24 fps / H.264 + AAC.
Podgląd ruchu i montażu z prostymi kolorami Workbench, bez renderowania shaderów premium.

OBRAZ
0,00–15,50: istniejące deszczowe otwarcie Seedance.
15,00–22,00: składanie wszystkich warstw w obudowę; zamknięcie trwa 5 s.
21,75–25,75: MagSafe, ponownie wyrenderowany w spójnej ciemnej scenie.
25,50–44,50: nowa przestrzenna animacja Blendera: telefon, osobna brama, trzy rzeźbiarskie przekaźniki, jedna trasa oraz poruszające się impulsy. Kamera podróżuje w przestrzeni i wraca do fizycznej bramy. To wizualna metafora, nie symulacja sieci. Nie ma inscenizacji awarii.
44,25–54,00: nowa scena Blendera z telefonem i falami wykrywania. Dokładne „iPhone (Piotrek)” oraz „AirDrop · Wszyscy” to obiekty tekstowe w przestrzeni, bez paneli UI. Kontekst AirDrop nie oznacza, że imię występuje w każdym pakiecie Wi-Fi lub Bluetooth.
53,50–58,25: obudowa przesuwa się w lewo i ustępuje modelowi Raspberry Pi/LTE.
57,75–66,71: prawdziwe nagranie IMG_4626, wszystkie 215 klatek, bez przyspieszania. Zielony wynik jest widoczny od około 63,75 s. Wyniku przeglądarki nie podmieniano; nagranie pokazuje wynik tego żądania w przeglądarce.
66,46–71,00: nowa scena Blendera — obudowa, przestrzenna nazwa SafeWall i logo 4A z oryginalnego SVG. Obudowa pozostaje bez nazwy i logo.
Nakładki czasowe to przenikania. Nie ma plansz HTML/Pillow, schematów 2D ani końcowej listy dalszych kroków. Pillow służy tylko do składania klatek oraz kontaktówki kontrolnej.

LEKTOR I CZAS
Aktualny tekst: ../VOICEOVER-APPROVED-v20.txt.
Zachowano pełniejszy tekst z historii, cenzury, odbiorców, powerbanku, osobnej bramy i nazwy „iPhone (Piotrek)”.
Usunięto wyjaśnienie przekaźników, zdania o podłączaniu przewodu i sprawdzaniu strony oraz „Kolejny krok: miniaturyzacja, testy bezpieczeństwa i próby z przyszłymi użytkownikami”.
Nowe zdanie: „SafeWall ma kierować połączenia przez anonimizującą sieć Tor.”
Daniel / Eleven v4. Większość pochodzi z zaakceptowanego nagrania v16, nowe zdanie o Torze to osobna dogrywka. Nie przyspieszano głosu. Dwa niezależne etapy kontroli: zgodność wybranych słów źródłowych oraz transkrypcja całego zmontowanego audio; wszystkie 121 tokenów pasują do tekstu v20.
Wcześniejsze około 65 s było szacunkiem narracji. W tym montażu zachowano pełne dziewięciosekundowe demo i przestrzeń na obejrzenie wyniku; stąd zmierzony czas filmu 71 s. Propozycja 40 s nie obejmowałaby przywróconej pełniejszej treści przy tym tempie.
„To nasz prototyp” pada na prawdziwym nagraniu. Dalszą czynność i wynik można obejrzeć bez dodatkowego objaśniania przez lektora.
Seedance dostarcza tylko istniejące efekty deszczu i otoczenia. Dodano dyskretne SFX; bez muzyki. Oryginalnego dźwięku live z rozmowami nie użyto.

EDYCJA
SafeWall-edit-v20.blend — montaż w Blender Video Sequencer; obrazowe sekwencje ujęć i miks audio, odwołania do folderów projektu.
tor-v20.blend / radios-v20.blend / closing-v20.blend — nowe edytowalne sceny 3D.
docking-v20.blend — MagSafe ze zmienionym tłem i tempem dopasowanym do 4 s.
Składanie i przejście do prototypu: ../launch-preview-v18/assembly-v18.blend oraz prototype-v18.blend.
edit-timeline.json — czasy montażowe. validation.json — parametry i wyniki kontroli gotowego MP4.
SafeWall-launch-preview-v20.srt — opcjonalne napisy, niewypalone w film.
contact-sheet.png — kadry kontrolne; nie jest elementem filmu.
../voiceover-v20/ — gotowy głos, pojedyncza dogrywka, parametry oraz dokładny montaż słów.

ODTWORZENIE
Skrypty w ../../scripts/: prepare_launch_audio_v20.py, build_launch_3d_v20.py, compose_launch_preview_v20.py, save_launch_edit_v20.py.
Blender 4.5.14 LTS: /Users/piotrek/Library/Caches/safewall-render/blender-volume/Blender.app/Contents/MacOS/Blender
Python do montażu: /Users/piotrek/Library/Caches/safewall-render/preview-venv/bin/python
Wywołanie renderu: Blender --background --python build_launch_3d_v20.py -- tor (analogicznie radios, closing, docking).
Sceny premium v04, wcześniejszy film v18 i oryginalne nagrania są zachowane.

OGRANICZENIA PREVIEW
Przejścia są przenikaniami z easingiem; to nie finalny morph optyczny. Workbench ma uproszczone oświetlenie i cienie. Materiał live po obrocie ma 848×464, więc jego drobny tekst ogranicza źródłowa rozdzielczość. Nowych generacji Seedance nie wykonywano; pakiet v19 był propozycją, a v20 realizuje wybrany przez użytkownika kierunek Blender.
