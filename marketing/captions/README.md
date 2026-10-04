# Napisy do filmu

Źródła napisów słownych dla zatwierdzonego lektora v22: `caption-lines.txt`, `whisper.json`, korekty czasów, `events.json` i gotowy `SafeWall-captions.srt`. To osobny etap montażu; nie zmienia treści nagrania urządzenia.

`run.py build` tworzy zdarzenia oraz SRT z zapisanej transkrypcji, a `run.py apply PLIK.mp4` nakłada napisy na nowy eksport. Obie operacje sprawdzają zgodność lokalnego audio z hashem w `whisper.source.json`; **wymagają przywrócenia pliku WAV lektora spoza Gita**. Ścieżkę `audio` należy dopasować do lokalnego archiwum, uruchamiając skrypt z katalogu głównego projektu.

Wymagania: Python, RTK, ffmpeg/ffprobe, Node.js, Chrome oraz pakiet z `package-lock.json` (`npm ci` w tym katalogu). Konfigurację przeglądarki sprawdź w `render_caps.cjs`. PNG i cache renderów zapisują się w `renders/`, poza Gitem.

`transcribe.py` służy wyłącznie do świadomego utworzenia nowej transkrypcji przez API; klucz pobiera z `OPENAI_API_KEY` albo ukrytego wejścia terminala. Nie uruchamiaj go dla istniejącego cache bez potrzeby. Aktualizacja repozytorium nie uruchamia API ani renderowania napisów. Stan gotowych mediów należy sprawdzać w lokalnym raporcie eksportu.
