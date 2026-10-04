"""Replace only the Seedance picture; retain v22 narration, SFX and exact timing."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / 'physical-design/visualization'
OUT = V / 'launch-preview-v23'
REF = ROOT / 'physical-design/references/seedance-v23'
SOURCE = Path('/Users/piotrek/Downloads/3994e4a0-00cd-452e-9158-ef7329a6773a.mp4')
for folder in [OUT, REF, OUT / 'seedance-frames']:
    folder.mkdir(parents=True, exist_ok=True)
stored = REF / 'Seedance-rain-opening-original.mp4'
shutil.copy2(SOURCE, stored)
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(stored) == digest(SOURCE)
source = {'download': str(SOURCE), 'stored': str(stored.relative_to(ROOT)),
          'sha256': digest(stored), 'picture_source_range_seconds': [0, 15.5],
          'speed_multiplier': 1, 'output_frames': 372,
          'audio': 'Existing finished v22 mix preserved; this revision replaces picture only.'}
(REF / 'source.json').write_text(json.dumps(source, indent=2) + '\n')
subprocess.run(['rtk', 'ffmpeg', '-v', 'error', '-y', '-i', str(stored),
    '-vf', 'fps=24,scale=960:540:flags=lanczos,setsar=1', '-frames:v', '372', '-q:v', '2',
    str(OUT / 'seedance-frames/%04d.jpg')], check=True)
edit = json.loads((V / 'launch-preview-v22/edit-timeline.json').read_text())
edit['clips'][0]['source'] = 'v23'
edit['clips'][0]['frame_extension'] = 'jpg'
edit['voice'] = '../voiceover-v22/SafeWall-voiceover-pl-daniel-v22.wav'
edit['opening_source'] = '../../references/seedance-v23/source.json'
(OUT / 'edit-timeline.json').write_text(json.dumps(edit, indent=2) + '\n')
for name in ['final-mix.wav', 'foley.wav', 'audio-mix.json', 'outro-source.json', 'live-retime.json']:
    shutil.copy2(V / 'launch-preview-v22' / name, OUT / name)

# Same compositor and validation as v22, with the new opening reference.
code = (ROOT / 'physical-design/scripts/compose_launch_preview_v22.py').read_text()
code = code.replace('v22: AirDrop label, SafeWall phrase and trimmed, accelerated live demonstration.',
                    'v23: newer Seedance picture; retain v22 edit and audio for reusable captions.')
code = code.replace("OUT=V/'launch-preview-v22'", "OUT=V/'launch-preview-v23'")
code = code.replace("STEM='SafeWall-launch-preview-v22'", "STEM='SafeWall-launch-preview-v23'")
code = code.replace("actual=OUT/'live-frames'", "actual=V/'launch-preview-v22/live-frames'")
code = code.replace("'new_blender_scenes':['radios']", "'new_blender_scenes':[], 'new_seedance_opening':'../../references/seedance-v23/source.json'")
code = code.replace('V22_ENCODE', 'V23_ENCODE').replace('V22_READY', 'V23_READY')
code = code.replace("f'{n:04d}.png'", "(f'{n:04d}.jpg' if revision=='v23' and kind=='seedance' else f'{n:04d}.png')")
code = code.replace("f'{i:04d}.png').is_file()", "f'{i:04d}.{c.get(\"frame_extension\",\"png\")}').is_file()")
(ROOT / 'physical-design/scripts/compose_launch_preview_v23.py').write_text(code)
print('V23_OPENING_READY', stored, '372 frames; all v22 timings and audio retained')
