"""Document and deliver the validated v22 preview, retaining previous revisions."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / 'physical-design/visualization'
OUT = V / 'launch-preview-v22'
VOICE = V / 'voiceover-v22'

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

validation = json.loads((OUT / 'validation.json').read_text())
assert validation['status'] == 'technical_checks_passed'
assert (OUT / 'SafeWall-edit-v22.blend').is_file()
duration = validation['duration_seconds']

plan = json.loads((V / 'voiceover-plan-v21.json').read_text())
plan.update(
    revision='v22_label_narration_and_demo_pacing',
    status='preview_rendered_and_technically_validated',
    canonical_text='VOICEOVER-APPROVED-v22.txt',
    canonical_sha256=digest(V / 'VOICEOVER-APPROVED-v22.txt'),
    lexical_token_count=120,
    audio='voiceover-v22/SafeWall-voiceover-pl-daniel-v22.wav',
    audio_duration_seconds=duration,
    audio_timing_note='Narration is not time-stretched. Closing moves 2.75 seconds earlier; the actual demo is trimmed and played at 1.35x.',
    voiceover_edit='voiceover-v22/edit.json',
    independent_ASR='voiceover-v22/final-edit-asr.json',
    current_movie='launch-preview-v22/SafeWall-launch-preview-v22.mp4',
    validation='launch-preview-v22/validation.json',
    blender_edit='launch-preview-v22/SafeWall-edit-v22.blend',
    edit_timeline='launch-preview-v22/edit-timeline.json',
    full_film_duration_seconds=duration,
)
plan['approved_changes'].append('Replace Osobna brama with SafeWall; no other narration cuts.')
plan['visual_direction'].update(new_scenes=['radios'], visible_discovery_label='AirDrop')
plan['live_demo'].update(frames=149, duration=149/24, speed_multiplier=1.35,
    global_end=63.958333333333336, source_frames_inclusive=[9, 209],
    retime_manifest='launch-preview-v22/live-retime.json',
    green_result_approx_global_seconds=[61.95, 63.96])
plan['sound']['new_voice_generation'] = 'Only the sentence beginning SafeWall ma pilnować jednej zasady; same Daniel voice and Eleven v4 model.'
plan['claim_boundaries'] = [
    item.replace('Nearby name contextualized as AirDrop Everyone.',
                 'Nearby name is an AirDrop discovery illustration; visible context label is AirDrop.')
    for item in plan['claim_boundaries']
]
save(V / 'voiceover-plan-v22.json', plan)

(OUT / 'README.txt').write_text('''SAFEWALL — PREVIEW v22

Otwórz: SafeWall-launch-preview-v22.mp4
69,917 s / 960×540 / 24 fps / H.264 + AAC.

ZMIANY
1. Przy telefonie pozostaje wyłącznie „AirDrop”. Usunięto „· Wszyscy”.
2. Daniel mówi: „SafeWall ma pilnować jednej zasady: internet przez Tor albo brak połączenia”.
   Dograno całe zdanie tym samym głosem i modelem. Pozostały tekst bez zmian.
3. Rzeczywiste demo skrócono z 8,958 do 6,208 s: źródłowe klatki 9–209,
   odtwarzanie 1,35×. Zachowano podłączenie, odświeżenie i zielony wynik.
   Obrazu przeglądarki nie retuszowano; każda klatka ma zgodny hash ze źródłem.
   Outro i końcowy lektor przesunięte o 2,75 s wcześniej, bez przyspieszania.

MONTAŻ (przejścia częściowo nakładają ujęcia)
00,00–15,50  Seedance: deszczowy wstęp.
15,00–22,00  Blender: składanie obudowy.
21,75–25,75  Blender: MagSafe.
25,50–44,50  Blender: trzy serwery i przepływ ruchu.
44,25–54,00  Blender: wiele „iPhone (Piotrek)”, podpis „AirDrop”.
53,50–58,25  Blender: prototyp Raspberry Pi.
57,75–63,96  Rzeczywiste demo, 1,35×. Zielony wynik około 61,95–63,96 s.
63,71–69,92  Istniejące marketing/outro w oryginalnym tempie.

PLIKI DO EDYCJI
SafeWall-edit-v22.blend — pełny montaż Blender VSE; korzysta z klatek w repozytorium.
radios-v22.blend — edytowalna scena 3D z poprawionym podpisem.
../launch-preview-v21/tor-v21.blend — trzy modele szaf serwerowych.
../VOICEOVER-APPROVED-v22.txt — aktualny tekst.
../voiceover-v22/ — głos, SRT, dogrywka i znaczniki czasu.
edit-timeline.json / live-retime.json — czasy i mapowanie klatek demo.
validation.json — weryfikacja dekodowania, audio, tekstu i źródeł.
contact-sheet.png — podgląd klatek; widoczne tam czasy nie trafiają do filmu.

To podgląd Workbench, bez końcowego renderowania materiałów premium.
Oryginalne outro i scena premium v04 zachowane bez zmian.
Wszystkie wcześniejsze wersje pozostają w swoich folderach.
''')

(VOICE / 'README.txt').write_text('''SAFEWALL — GŁOS v22

SafeWall-voiceover-pl-daniel-v22.mp3 / .wav — gotowa ścieżka lektora.
Tekst: ../VOICEOVER-APPROVED-v22.txt. Język polski, Daniel / eleven_v4.

Jedyna zmiana słowna względem v20/v21: „Osobna brama” → „SafeWall”.
Dograno całe zdanie z zasadą Tor albo brak połączenia i dopasowano poziom.
Dogrywka zaczyna się w 33,10 s. Kolejne zdania zachowują dotychczasowy timing.
Końcowe „SafeWall. Bo za każdą historią stoi człowiek.” przesunięto o 2,75 s
wcześniej z powodu krótszej demonstracji. Lektor nie jest przyspieszony.
Cała ścieżka wraz z ciszą na końcu: 69,917 s.

request-gateway-pickup.json — ustawienia dogrywki, bez danych uwierzytelniających.
gateway-pickup.mp3 — wygenerowane zdanie.
edit.json — montaż i znaczniki czasu słów.
final-edit-asr.json — niezależna transkrypcja zmontowanego audio;
po normalizacji interpunkcji wszystkie 120 tokenów odpowiada tekstowi.
SafeWall-voiceover-pl-daniel-v22.srt — napisy do opcjonalnego włączenia.
''')

p = ROOT / 'physical-design/design-brief.json'
brief = json.loads(p.read_text())
brief['confirmed_requirements']['voiceover'].update(
    approved_text='visualization/VOICEOVER-APPROVED-v22.txt',
    estimated_full_duration_seconds=[duration, duration],
    measured_duration_seconds=duration,
    latest_audio='visualization/voiceover-v22/SafeWall-voiceover-pl-daniel-v22.mp3',
    latest_audio_text_revision='v22: SafeWall replaces Osobna brama; other v20 wording retained',
    edit_timing='visualization/voiceover-v22/edit.json')
brief['latest_launch_preview'].update(
    movie='visualization/launch-preview-v22/SafeWall-launch-preview-v22.mp4',
    duration_seconds=duration, plan='visualization/voiceover-plan-v22.json',
    editable_cut='visualization/launch-preview-v22/SafeWall-edit-v22.blend',
    narrator='Daniel / Eleven v4; v22 SafeWall phrase pickup',
    live_demo_native_speed=False, live_demo_speed_multiplier=1.35,
    live_demo_duration_seconds=149/24)
brief['full_film_planning'].update(
    status='v22_preview_complete', plan='visualization/voiceover-plan-v22.json',
    readable_plan='visualization/launch-preview-v22/README.txt',
    proposed_seconds=duration, suggested_total_edit_seconds=[duration, duration],
    current_render='visualization/launch-preview-v22/SafeWall-launch-preview-v22.mp4',
    real_demo='User-supplied IMG_4626; trimmed and played at 1.35x, original browser result preserved.',
    measured_narration_seconds=duration, timing='visualization/voiceover-v22/edit.json',
    live_action_status='Rotated, trimmed and incorporated into v22; original source frame hashes verified.',
    narration_timing_note='69.917-second audio timeline including quiet demo space; no narration time stretch.',
    remaining_edit_work='User review of v22; premium final rendering remains deferred.')
brief['film_sequence_plan'][4] = 'Blender phone discovery with many exact iPhone (Piotrek) names; visible context label AirDrop'
brief['film_sequence_plan'][7] = 'Trimmed 6.208-second live connection, refresh and positive Tor Check result at 1.35x'
brief['visual_revision_v22'] = {
    'status': 'complete_preview',
    'changes': ['Remove dot and Wszyscy from AirDrop label',
                'Replace spoken Osobna brama with SafeWall',
                'Trim live demo and accelerate to 1.35x; 6.208 seconds'],
    'narration_other_words_unchanged': True, 'browser_content_altered': False,
    'new_seedance_generation': False,
}
save(p, brief)

vision = ROOT / '08-WIZJA-I-PLAN-PROJEKTU.md'
heading = '### Krótsze demo, nazwa SafeWall i prostszy podpis — v22'
if heading not in vision.read_text():
    with vision.open('a') as f:
        f.write('''\n\n### Krótsze demo, nazwa SafeWall i prostszy podpis — v22

Gotowy [preview v22](physical-design/visualization/launch-preview-v22/SafeWall-launch-preview-v22.mp4): **69,92 s, 960×540, 24 fps**. Z podpisu w scenie telefonu usunięto „· Wszyscy”; pozostało samo „AirDrop”. W lektorze „Osobna brama” zastąpiono „SafeWall”. Daniel dograł całe zdanie z zasadą „internet przez Tor albo brak połączenia”; pozostałe słowa zatwierdzonego tekstu nie zmieniły się.

Rzeczywiste demo skrócono z 8,96 do 6,21 s przez przycięcie początku i końca oraz przyspieszenie do 1,35×. Zachowano podłączenie, odświeżenie i około dwóch sekund zielonego wyniku Tor Check. Klatki przeglądarki nie były retuszowane, a ich zgodność ze źródłem sprawdzono hashami. Końcowy lektor i istniejące outro z `marketing/outro` przesunięto o 2,75 s wcześniej; zachowują własne tempo.

[Aktualny tekst](physical-design/visualization/VOICEOVER-APPROVED-v22.txt), [opis montażu](physical-design/visualization/launch-preview-v22/README.txt), [edytowalny projekt Blendera](physical-design/visualization/launch-preview-v22/SafeWall-edit-v22.blend), [weryfikacja](physical-design/visualization/launch-preview-v22/validation.json). Nadal używamy podglądu Workbench, bez renderowania materiałów premium. Wcześniejsze wersje pozostają jako archiwum.
''')

movie = OUT / 'SafeWall-launch-preview-v22.mp4'
desktop = Path('/Users/piotrek/Desktop/SafeWall-preview-v22.mp4')
shutil.copy2(movie, desktop)
assert digest(movie) == digest(desktop)
save(OUT / 'delivery.json', {'desktop_movie': str(desktop), 'sha256': digest(movie),
    'duration_seconds': duration, 'editable_project': 'SafeWall-edit-v22.blend'})
print('V22_DELIVERED', str(desktop), duration, 'seconds', movie.stat().st_size, 'bytes')
