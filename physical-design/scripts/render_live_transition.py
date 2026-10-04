"""Render four seconds of blocking animation, blend into the real photo, hold.

Run with Blender --background Overhead-photo-transition-v06.blend --python ...
This edits a video timeline; the supplied photograph is only cropped/scaled to
the delivery frame, never generated, retouched or substituted.
"""
import hashlib
import json
import struct
import subprocess
import time
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'visualization'
scene=bpy.context.scene
assert scene.render.engine=='BLENDER_WORKBENCH'
assert (scene.render.resolution_x,scene.render.resolution_y)==(960,540)
assert (scene.frame_start,scene.frame_end,scene.render.fps)==(1,96,24)
frames=OUT/'live-transition-frames-v06';frames.mkdir(exist_ok=True)
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.filepath=str(frames/'overhead_')
start=time.monotonic();bpy.ops.render.render(animation=True)
render_seconds=time.monotonic()-start
for f in range(1,97):
    data=(frames/f'overhead_{f:04d}.png').read_bytes()
    assert data[:8]==b'\x89PNG\r\n\x1a\n'
    assert struct.unpack('>II',data[16:24])==(960,540)

photo=ROOT/'references/live-transition/prototype-phone-photo.png'
movie=OUT/'CG-to-real-preview-v06.mp4'
t='((T-4)/2)'
q=f'(pow({t},3)*(10-15*{t}+6*pow({t},2)))'
expr=f'if(lt(T,4),A,if(gte(T,6),B,A*(1-{q})+B*{q}))'
filters=("[0:v]format=gbrp,tpad=stop_mode=clone:stop_duration=4,setpts=PTS-STARTPTS[cg];"
         "[1:v]crop=1362:766:0:118,scale=960:540:flags=lanczos,setsar=1,format=gbrp,setpts=PTS-STARTPTS[photo];"
         f"[cg][photo]blend=all_expr='{expr}':shortest=1,format=yuv420p[out]")
command=['rtk','ffmpeg','-hide_banner','-loglevel','error','-y',
         '-framerate','24','-start_number','1','-i',str(frames/'overhead_%04d.png'),
         '-loop','1','-framerate','24','-i',str(photo),
         '-filter_complex',filters,'-map','[out]','-frames:v','192','-r','24',
         '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart','-an',str(movie)]
subprocess.run(command,check=True)
probe=json.loads(subprocess.check_output(['rtk','ffprobe','-v','error','-count_frames','-select_streams','v:0',
    '-show_entries','stream=width,height,r_frame_rate,nb_read_frames:format=duration','-of','json',str(movie)],text=True))
stream=probe['streams'][0]
assert (stream['width'],stream['height'],stream['r_frame_rate'],int(stream['nb_read_frames']))==(960,540,'24/1',192)
assert abs(float(probe['format']['duration'])-8)<.001
subprocess.run(['rtk','ffmpeg','-v','error','-xerror','-i',str(movie),'-f','null','-'],check=True)
for seconds,name in [(5,'transition-halfway-v06.png'),(7.5,'transition-real-photo-v06.png')]:
    subprocess.run(['rtk','ffmpeg','-v','error','-y','-ss',str(seconds),'-i',str(movie),
                    '-frames:v','1',str(OUT/name)],check=True)
checkpoint=json.loads((OUT/'premium-materials-v04.json').read_text())
assert hashlib.sha256((OUT/checkpoint['master_scene']).read_bytes()).hexdigest()==checkpoint['master_sha256']
report={'status':'passed','movie':movie.name,'duration_seconds':8,'resolution':[960,540],
        'frames_decoded':192,'fps':24,'render_seconds':round(render_seconds,2),
        'real_user_photo_included':True,'photo_final_hold_seconds':2,
        'transition':'photo-aligned quintic eased dissolve; not optical-flow morph',
        'premium_master_unchanged':True,'photo_sha256':hashlib.sha256(photo.read_bytes()).hexdigest(),
        'ffmpeg_filter':filters,'probe':probe,'movie_bytes':movie.stat().st_size}
(OUT/'live-transition-movie-validation-v06.json').write_text(json.dumps(report,indent=2))
print('CG_TO_REAL_MOVIE_READY',json.dumps(report),flush=True)
