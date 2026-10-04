"""Record the delivered preview only after movie validation and VSE save succeed."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];V=ROOT/'physical-design/visualization';OUT=V/'launch-preview-v21'
validation=json.loads((OUT/'validation.json').read_text())
assert validation['status']=='technical_checks_passed'
assert (OUT/'SafeWall-edit-v21.blend').is_file()
duration=validation['duration_seconds']
plan=json.loads((V/'voiceover-plan-v20.json').read_text())
plan.update(revision='v21_visual_revision_voiceover_unchanged',status='preview_rendered_and_technically_validated',
 current_movie='launch-preview-v21/SafeWall-launch-preview-v21.mp4',validation='launch-preview-v21/validation.json',
 blender_edit='launch-preview-v21/SafeWall-edit-v21.blend',edit_timeline='launch-preview-v21/edit-timeline.json',full_film_duration_seconds=duration)
plan['visual_direction'].update(new_scenes=['tor','radios'],server_instances=3,
 server_model_source='../references/server-rack-v21/source.json',emitted_name_instances=23,
 outro='../../marketing/outro/safewall-outro-landscape.mp4',
 outro_note='User explicitly selected the existing brand outro instead of the Blender closing.',blender_closing_used=False)
(V/'voiceover-plan-v21.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
p=ROOT/'physical-design/design-brief.json';brief=json.loads(p.read_text())
brief['latest_launch_preview'].update(movie='visualization/launch-preview-v21/SafeWall-launch-preview-v21.mp4',
 duration_seconds=duration,plan='visualization/voiceover-plan-v21.json',editable_cut='visualization/launch-preview-v21/SafeWall-edit-v21.blend',
 outro_source='../marketing/outro/safewall-outro-landscape.mp4',server_nodes=3,emitted_phone_names=True)
brief['full_film_planning'].update(status='v21_preview_complete',plan='visualization/voiceover-plan-v21.json',
 readable_plan='visualization/launch-preview-v21/README.txt',proposed_seconds=duration,suggested_total_edit_seconds=[duration,duration],
 current_render='visualization/launch-preview-v21/SafeWall-launch-preview-v21.mp4',
 remaining_edit_work='User review of v21 server nodes, emitted names and existing marketing outro; premium final rendering remains deferred.')
brief['film_sequence_plan'][-1]='Existing landscape marketing/outro MP4, full native-speed 6.2-second brand animation'
brief['visual_revision_v21']={'status':'complete_preview','changes':['Three downloaded CC0 server models replace the relay sculptures','Many iPhone (Piotrek) names emerge from the phone','Existing marketing/outro replaces the Blender ending'],'narration_unchanged':True,'live_demo_unchanged':True,'new_seedance_generation':False}
p.write_text(json.dumps(brief,ensure_ascii=False,indent=2)+'\n')
with (ROOT/'08-WIZJA-I-PLAN-PROJEKTU.md').open('a') as f:
    f.write('''\n\n### Serwery, emitowana nazwa telefonu i gotowe outro — v21\n\nGotowy [preview v21](physical-design/visualization/launch-preview-v21/SafeWall-launch-preview-v21.mp4): **72,67 s, 960×540, 24 fps**. Na prośbę użytkownika zakończenie z Blendera zastąpiono pełnym poziomym klipem z `marketing/outro`, bez przyspieszania; dodatkowe 1,67 s wynikają wyłącznie z długości tego zakończenia. Jest to wskazany przez użytkownika wyjątek od wcześniejszego kierunku bez plansz.\n\nTrzy węzły przedstawia model szafy serwerowej [Compute Rack — 3DAssets.dev](https://3dassets.dev/assets/data-centre-infiltration-kit-data-centre-infiltration--49b6521a), opublikowany przez autora jako CC0. [Źródło, oryginał i hash modelu](physical-design/references/server-rack-v21/source.json) są zapisane lokalnie. W Blenderze użyto trzech egzemplarzy w skali ilustracyjnej. W ujęciu telefonu 23 animowane instancje „iPhone (Piotrek)” kolejno wychodzą z urządzenia i rozchodzą się na kilku trajektoriach. Przy telefonie pozostaje kontekst „AirDrop · Wszyscy”.\n\nZachowano cały tekst i głos Daniela z v20, pełne rzeczywiste demo, składanie oraz MagSafe. Porównanie PCM potwierdziło, że miks v20 pozostał identyczny w swoim dotychczasowym zakresie; dodano tylko ciszę na dłuższy koniec outro. [Opis i czasy v21](physical-design/visualization/launch-preview-v21/README.txt), [edytowalny montaż Blendera](physical-design/visualization/launch-preview-v21/SafeWall-edit-v21.blend), [raport weryfikacji](physical-design/visualization/launch-preview-v21/validation.json). Oryginalny plik outro i scena premium pozostały niezmienione.\n''')
movie=OUT/'SafeWall-launch-preview-v21.mp4';desktop=Path('/Users/piotrek/Desktop/SafeWall-preview-v21.mp4')
shutil.copy2(movie,desktop)
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(movie)==digest(desktop)
(OUT/'delivery.json').write_text(json.dumps({'desktop_movie':str(desktop),'sha256':digest(movie),'duration_seconds':duration,'editable_project':'SafeWall-edit-v21.blend'},indent=2)+'\n')
print('V21_DELIVERED',str(desktop),duration,'seconds',movie.stat().st_size,'bytes')
