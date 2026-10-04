"""Render the saved Workbench preview, encode H.264 and validate the delivered clip.

Run inside Blender against visualization/Phone-docking-preview-v05.blend.
The premium Cycles scene is never opened or changed by this script.
"""
import hashlib
import json
import struct
import subprocess
import time
from pathlib import Path

import bpy

OUT = Path(__file__).resolve().parents[1] / 'visualization'
scene = bpy.context.scene
assert scene.render.engine == 'BLENDER_WORKBENCH'
assert (scene.render.resolution_x, scene.render.resolution_y) == (960, 540)
assert scene.render.resolution_percentage == 100
assert (scene.frame_start, scene.frame_end, scene.render.fps) == (1, 120, 24)
assert scene.render.fps_base == 1
frames = OUT / 'docking-frames-v05'
frames.mkdir(exist_ok=True)
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.filepath = str(frames / 'docking_')
start = time.monotonic()
bpy.ops.render.render(animation=True)
render_seconds = time.monotonic() - start
for frame in range(1, 121):
    path = frames / f'docking_{frame:04d}.png'
    header = path.read_bytes()[:24]
    assert header[:8] == b'\x89PNG\r\n\x1a\n', path
    assert struct.unpack('>II', header[16:24]) == (960, 540), path

movie = OUT / 'Phone-docking-preview-v05.mp4'
subprocess.run(['rtk', 'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                '-framerate', '24', '-start_number', '1', '-i', str(frames / 'docking_%04d.png'),
                '-frames:v', '120', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', str(movie)], check=True)
probe = json.loads(subprocess.check_output(['rtk', 'ffprobe', '-v', 'error', '-count_frames',
    '-select_streams', 'v:0', '-show_entries',
    'stream=width,height,r_frame_rate,nb_read_frames,codec_name,pix_fmt:format=duration',
    '-of', 'json', str(movie)], text=True))
stream = probe['streams'][0]
assert (stream['width'], stream['height']) == (960, 540)
assert stream['r_frame_rate'] == '24/1' and int(stream['nb_read_frames']) == 120
assert abs(float(probe['format']['duration']) - 5) < .001
subprocess.run(['rtk', 'ffmpeg', '-v', 'error', '-xerror', '-i', str(movie), '-f', 'null', '-'], check=True)
checkpoint = json.loads((OUT / 'premium-materials-v04.json').read_text())
assert hashlib.sha256((OUT / checkpoint['master_scene']).read_bytes()).hexdigest() == checkpoint['master_sha256']
report = {'status': 'passed', 'movie': movie.name, 'resolution': [960, 540],
          'fps': 24, 'duration_seconds': 5, 'frames_rendered_and_decoded': 120,
          'render_engine': 'BLENDER_WORKBENCH', 'render_seconds': round(render_seconds, 2),
          'premium_shaders_used_in_preview': False, 'premium_master_unchanged': True,
          'movie_bytes': movie.stat().st_size, 'probe': probe}
(OUT / 'docking-movie-validation-v05.json').write_text(json.dumps(report, indent=2))
print('DOCKING_MOVIE_READY', json.dumps(report), flush=True)
