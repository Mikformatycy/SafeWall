SAFEWALL — PREVIEW v21

ODTWÓRZ: SafeWall-launch-preview-v21.mp4
72,67 s / 960×540 / 24 fps / H.264 + AAC. Lekki preview.

TRZY ZMIANY WZGLĘDEM v20
1. Zakończenie pochodzi z marketing/outro/safewall-outro-landscape.mp4. Cały oryginalny klip 6,2 s, bez zmiany prędkości, przeskalowany i próbkowany do 540p / 24 fps. Zastępuje zakończenie z Blendera. To wyraźnie wskazany przez użytkownika wyjątek od wcześniejszego kierunku „bez plansz”.
2. Trzy przekaźniki są szafami serwerowymi zaimportowanymi z modelu Compute Rack z 3DAssets.dev. Kamera ma nieco szerszy kadr, żeby pokazać trzy serwery. Ruch impulsów i kolejność trasy pozostają w Blenderze. Skala serwerów jest ilustracyjna, nie jest skalą rzeczywistego pokoju serwerowego względem telefonu.
3. Z modelu telefonu cyklicznie wychodzą kopie dokładnego napisu „iPhone (Piotrek)”. W scenie są 23 animowane instancje, uruchamiane co 0,43 s; kilka jest widocznych jednocześnie. Różne trajektorie, łagodne wejścia, zmiana skali i zanikanie. Kontekst „AirDrop · Wszyscy” zostaje przy telefonie. To wizualizacja wykrywania, nie twierdzenie, że każdy pakiet zawiera nazwę telefonu.

CZASY
25,50–44,50 s: nowe serwery 3D.
44,25–54,00 s: wiele nazw wychodzących z telefonu.
57,75–66,71 s: pełne rzeczywiste demo, 215 klatek przy 24 fps, bez przyspieszania.
66,46–72,67 s: gotowe outro z marketing/outro; wejście nachodzi na ostatnie 0,25 s demo.
Pozostałe ujęcia mają timing v20. Zwiększenie długości o 1,67 s wynika wyłącznie z zachowania pełnego outro. Dokładny czas po przeliczeniu 6,2 s na 24 fps wynosi 149/24 s.

LEKTOR I DŹWIĘK
Daniel i ustalony tekst v20 pozostają bez zmian. Użyty miks v20 jest identyczny próbka po próbce w swoim dotychczasowym zakresie; dodano ciszę wyłącznie na dodatkowy koniec outro. Nie generowano nowego lektora ani muzyki.
Obowiązujący tekst: ../VOICEOVER-APPROVED-v20.txt.
Opcjonalne napisy SRT są obok MP4; nie wypalono ich w obraz.

MODEL SERWERA
Compute Rack (Data Centre Infiltration Kit), autor: 3D Assets.
https://3dassets.dev/assets/data-centre-infiltration-kit-data-centre-infiltration--49b6521a
https://cdn.3dassets.dev/assets/29226/v1/model.glb
Licencja według publikacji autora: CC0 1.0 Universal.
https://creativecommons.org/publicdomain/zero/1.0/
Model 343 488 bajtów, cztery siatki i materiały. Oryginał, podgląd i SHA256: ../../references/server-rack-v21/.
Wykorzystano istniejącą geometrię i proste kolory w Workbench. Źródło deklaruje użycie narzędzi AI przy tworzeniu modelu.

EDYTOWALNE PLIKI
tor-v21.blend — trzy serwery, urządzenie, telefon, trasa i ruch kamery.
radios-v21.blend — telefon i 23 instancje napisu.
SafeWall-edit-v21.blend — montaż w Blender Video Sequencer. Korzysta z sekwencji obrazów w folderach projektu v18/v20/v21 oraz final-mix.wav.
edit-timeline.json — montaż; validation.json — kontrola gotowego filmu; outro-source.json — pochodzenie i integralność zakończenia.
contact-sheet.png — kadry do szybkiego przeglądu, nie element filmu.
Skrypty: ../../scripts/build_launch_3d_v21.py, compose_launch_preview_v21.py, save_launch_edit_v21.py.

ZACHOWANE MATERIAŁY
Oryginał marketing/outro, film v20, master premium v04, oryginalne nagranie live i pobrany wstęp Seedance pozostają zachowane. Nie wykonywano nowych generacji Seedance. Podgląd pozostaje uproszczony: Workbench, cienie i proste materiały; finalne shadery nie są renderowane.
