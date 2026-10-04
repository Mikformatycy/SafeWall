"""Render and verify a versioned product movie from the saved scene timeline."""
import hashlib
import json
import struct
import subprocess
import sys
import time
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'visualization'
scene = bpy.context.scene
revision = scene.get('visual_revision', '').split('|')[0].strip()
assert revision in {'v02', 'v03', 'v04'}
stem = scene.get('render_stem', 'SafeWall')
width = int(scene.get('review_width', 1280)); height = int(scene.get('review_height', 720))
samples = int(scene.get('review_samples', 8))
FRAMES = OUT/f'frames-{revision}'
FRAMES.mkdir(exist_ok=True)
first, last, fps = scene.frame_start, scene.frame_end, scene.render.fps
total = last-first+1
duration = total/fps
validation = json.loads((OUT/f'scene-validation-{revision}.json').read_text())
assert not validation['failed_framing_frames'] and validation['closed_groups_at_origin']
assert validation['frames_checked'] == total
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.get_devices()
for device in prefs.devices:
    device.use = device.type == 'METAL'
scene.cycles.device = 'GPU' if any(d.type == 'METAL' for d in prefs.devices) else 'CPU'
scene.render.engine = 'CYCLES'; scene.cycles.samples = samples
scene.cycles.use_denoising = True; scene.render.use_persistent_data = True
scene.cycles.denoising_use_gpu = True
scene.render.resolution_x = width; scene.render.resolution_y = height
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGB'
def valid_frame(path):
    if not path.exists() or path.stat().st_size < 40:
        return False
    with path.open('rb') as stream:
        header = stream.read(24)
        stream.seek(-12, 2); ending = stream.read()
    return (header[:8] == b'\x89PNG\r\n\x1a\n' and
            struct.unpack('>II', header[16:24]) == (width, height) and
            ending == b'\x00\x00\x00\x00IEND\xaeB`\x82')

# Explicit recovery only: use --resume with an unchanged scene.
resume = '--resume' in sys.argv
skipped = rendered = 0
started = time.monotonic()
for frame in range(first, last+1):
    if resume and valid_frame(FRAMES/f'assembly_{frame:04}.png'):
        skipped += 1
        continue
    scene.frame_set(frame); scene.render.filepath = str(FRAMES/f'assembly_{frame:04}.png')
    bpy.ops.render.render(write_still=True)
    rendered += 1
    if frame % 24 == 0 or rendered == 1:
        elapsed = time.monotonic()-started
        print('MOVIE_PROGRESS', json.dumps({'frame': frame, 'total': total,
              'elapsed_seconds': round(elapsed), 'estimated_seconds_left': round(elapsed/rendered*(last-frame))}), flush=True)

for frame in range(first, last+1):
    path = FRAMES/f'assembly_{frame:04}.png'
    assert valid_frame(path), path
    with path.open('rb') as stream: header = stream.read(24)
    assert header[:8] == b'\x89PNG\r\n\x1a\n'
    assert struct.unpack('>II', header[16:24]) == (width, height)
video = OUT/f'{stem}-assembly-{revision}.mp4'
subprocess.run(['rtk', 'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-framerate', str(fps),
                '-start_number', str(first), '-i', str(FRAMES/'assembly_%04d.png'), '-frames:v', str(total),
                '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart', str(video)], check=True)
probe = subprocess.check_output(['rtk', 'ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                '-show_entries', 'stream=codec_name,width,height,r_frame_rate,nb_read_frames,duration',
                '-of', 'json', str(video)], text=True)
metadata = json.loads(probe)['streams'][0]
assert metadata['codec_name'] == 'h264'
assert (metadata['width'], metadata['height']) == (width, height)
assert metadata['r_frame_rate'] == f'{fps}/1' and int(metadata['nb_read_frames']) == total
assert abs(float(metadata['duration'])-duration) < .01
subprocess.run(['rtk', 'ffmpeg', '-v', 'error', '-i', str(video), '-f', 'null', '-'], check=True)
with video.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
report = {'status': 'complete', 'video': video.name, 'metadata': metadata,
          'PNG_frames_checked': total, 'all_frames_decode': True, 'all_frames_inside_camera': True,
          'video_bytes': video.stat().st_size, 'sha256': digest,
          'source_scene': f'{stem}-keynote-{revision}.blend', 'source_resolution': [1920, 1080],
          'renderer': 'Cycles '+scene.cycles.device, 'review_samples': samples,
          'resumed_frames': skipped, 'denoiser': 'OpenImageDenoise', 'GPU_denoising_for_resumed_render': True,
          'render_seconds': round(time.monotonic()-started), 'display_percentage_is_demo': True}
(OUT/f'movie-validation-{revision}.json').write_text(json.dumps(report, indent=2))
index_path = OUT/'asset-index.json'
index = json.loads(index_path.read_text())
index['primary_editable_scene'] = f'visualization/{stem}-keynote-{revision}.blend'
index['animation_preview'] = f'visualization/{stem}-assembly-{revision}.mp4'
still_revision = 'v04' if revision == 'v04' else 'v02'
index['stills'] = [f'visualization/assembled-preview-{still_revision}.png', f'visualization/exploded-preview-{still_revision}.png',
                   'visualization/cm4-detail.png']
index['workflow']['refine_powerbank_scene'] = 'scripts/refine_powerbank_scene.py'
index['workflow']['render_current_movie'] = 'scripts/render_powerbank_movie.py'
if revision in {'v03', 'v04'}:
    index['workflow']['retime_current_scene'] = 'scripts/retime_simultaneous_assembly.py'
if revision == 'v04':
    index['workflow']['style_current_scene'] = 'scripts/style_premium_scene.py'
index['engineering_scope'] = 'Visual concept; shell, OLED and material finishes are Blender styling proposals, Fusion CAD is previous packaging reference'
index_path.write_text(json.dumps(index, indent=2))
status = json.loads((OUT/'scene-status.json').read_text())
status.update({'stage': 'complete', 'movie_rendered_and_decoded': True, 'movie': video.name,
               'current_process': None, 'editable_scene': f'{stem}-keynote-{revision}.blend',
               'review_movie_resolution': [width, height], 'duration_seconds': duration, 'fps': fps})
(OUT/'scene-status.json').write_text(json.dumps(status, indent=2))
print('MOVIE_READY', json.dumps(report), flush=True)
