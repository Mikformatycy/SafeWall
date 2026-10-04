SAFEWALL — PEŁNY PODGLĄD FILMU v18

ODTWÓRZ: SafeWall-launch-preview-v18.mp4
Kopia na Pulpicie: SafeWall-preview-v18.mp4
Długość 79,75 s; 960×540, 24 fps, H.264 + AAC stereo. Około 6,1 MB.
To podgląd montażu i ruchu. Nowe ujęcia Blendera używają Workbench i prostych kolorów; nie renderowano shaderów premium. Źródłowe sceny i pliki pozostają zachowane.

CO JEST W FILMIE
0,00–15,50: pobrany klip Seedance z deszczem i dziennikarzem. Efekty otoczenia przyciszone pod lektorem.
15,00–22,00: wejście w dopasowaną pionową obudowę w Blenderze, rozłożenie i równoczesne składanie wszystkich warstw. Samo zamykanie trwa 5 s, 16,25–21,25 s, z easingiem.
21,75–25,75: boczne ujęcie z telefonem i przyciągnięcie MagSafe. Ponownie użyto istniejącego renderu Workbench v05; ma inne tło, do ujednolicenia przy finalnym wykończeniu.
25,50–48,25: animowany schemat Tora i zasady osobnej bramy, bez inscenizacji awarii.
48,00–56,25: widoczność telefonu, dokładne „iPhone (Piotrek)” w kontekście AirDrop oraz symbole interfejsów telefonu.
55,75–60,50: obudowa przesuwa się w lewo i przechodzi w model Raspberry Pi/LTE. Dopasowano położenie telefonu, płytek, kabli i antenę do nowego nagrania.
59,75–68,75: rzeczywiste podłączenie, odświeżenie i pozytywny Tor Check. Materiał nieprzyspieszony, bez podmieniania wyniku przeglądarki. Zielony komunikat widoczny od około 65,75 s.
68,50–79,75: prototyp, kolejne kroki i końcowa karta SafeWall z wybranym logo 4A.
Podane przedziały nakładają się, bo przejścia są przenikaniami.

DŹWIĘK
Daniel, Eleven v4, dokładnie gotowe audio v16; lektor bez zmiany tempa, start 0 s. Wszystkie 158 słów / 159 tokenów potwierdzone niezależnym ASR także po zmiksowaniu filmu.
Seedance: zachowano atmosferę i SFX. Transkrypcja oryginalnego dźwięku nie wykryła mowy. Bez dodanej muzyki.
Dodano lekkie akcenty zamknięcia obudowy, MagSafe i wpięcia RJ45. Szczegóły w validation.json. Oryginalnego dźwięku z nagrania demo nie użyto.
Poziom finalnego stereo: -14,26 LUFS; true peak -1,53 dBTP. Techniczna kontrola nie zastępuje oceny intonacji i miksu podczas odsłuchu użytkownika.

PRZEJŚCIA I OGRANICZENIA PREVIEW
Seedance ustawił urządzenie pionowo, więc przebudowano pod to początek ujęcia 3D. Końcowy kadr prototypu dopasowano do rzeczywistego nagrania.
Na tym etapie przejścia to dopasowane kadrem przenikania z easingiem; nie gotowy morph optyczny. Rzeczywisty test Tora pozostaje niezmieniony.
Źródło live po obrocie ma 848×464. Podgląd nie odzyskuje nieistniejących szczegółów ekranu.
MagSafe pokazuje koncepcyjny model Pro Max z wcześniejszej sceny; rzeczywisty demonstracyjny telefon jest osobnym urządzeniem użytkownika.

PLIKI I ODTWARZANIE
assembly-v18.blend / prototype-v18.blend — nowe edytowalne sceny.
edit-timeline.json — czasy klipów i przenikań. validation.json — parametry, integralność i kontrola tekstu.
SafeWall-launch-preview-v18.srt — opcjonalne napisy, nie wypalone w obraz.
final-contact-sheet.png — kadry z gotowego MP4.
Skrypty: ../../scripts/build_launch_preview_v18.py, compose_launch_preview_v18.py, finish_launch_preview_v18.py.
Render Blenderem 4.5.14; kompozycja przez Pillow/ffmpeg. Lokalny Python: /Users/piotrek/Library/Caches/safewall-render/preview-venv/bin/python.
