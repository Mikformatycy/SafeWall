"""Render v07 blocking, two matched dissolves, and a synchronized connector click."""
import array
import hashlib
import json
import math
import random
import struct
import subprocess
import sys
import time
import wave
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'visualization'
scene=bpy.context.scene
assert scene.render.engine=='BLENDER_WORKBENCH'
assert (scene.render.resolution_x,scene.render.resolution_y,scene.render.fps)==(960,540,24)
assert scene.render.resolution_percentage==100
frames=OUT/'full-sequence-frames-v07';frames.mkdir(exist_ok=True)
replacement=OUT/'full-sequence-replacement-v07';replacement.mkdir(exist_ok=True)
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
roles={name:[o for o in bpy.data.objects if o.get('sequence_role')==name]
       for name in ('enclosure','prototype','phone','cable')}
repair_replacement='--repair-replacement' in sys.argv
# Rendering reevaluates animation. Mute only visibility curves so the incoming
# pass can override the keyed enclosure/prototype state; retain all motion.
for objects in roles.values():
    for obj in objects:
        if not obj.animation_data or not obj.animation_data.action:continue
        action=obj.animation_data.action
        curves=list(action.fcurves) if action.is_action_legacy else [
            fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
        for curve in curves:
            if curve.data_path=='hide_render':curve.mute=True


def show_phase(frame,incoming=False):
    for obj in roles['enclosure']:obj.hide_render=incoming or frame>=193
    for obj in roles['prototype']:obj.hide_render=not(incoming or frame>=193)
    for obj in roles['phone']:obj.hide_render=frame<=120
    for obj in roles['cable']:obj.hide_render=frame<=192
    # In Workbench the OLED is plain geometry: switch the pixels on at closure.
    if frame<95:
        for obj in roles['enclosure']:
            if obj.name.startswith(('OLED | battery percentage','OLED | percent unit',
                                     'OLED | battery icon','OLED | battery terminal','OLED | charge bar')):
                obj.hide_render=True


start=time.monotonic()
for frame in (range(169,193) if repair_replacement else range(1,277)):
    scene.frame_set(frame);show_phase(frame)
    if not repair_replacement:
        scene.render.filepath=str(frames/f'sequence_{frame:04d}.png')
        bpy.ops.render.render(write_still=True)
    if 169<=frame<=192:
        show_phase(frame,incoming=True)
        scene.render.filepath=str(replacement/f'replacement_{frame:04d}.png')
        bpy.ops.render.render(write_still=True)
    if frame%24==0:print('SEQUENCE_RENDER_PROGRESS',frame,276,flush=True)
render_seconds=time.monotonic()-start
for folder,stem,first,last in [(frames,'sequence',1,276),(replacement,'replacement',169,192)]:
    for frame in range(first,last+1):
        data=(folder/f'{stem}_{frame:04d}.png').read_bytes()
        assert data[:8]==b'\x89PNG\r\n\x1a\n'
        assert struct.unpack('>II',data[16:24])==(960,540)
def pixels(path):
    return subprocess.check_output(['rtk','ffmpeg','-v','error','-i',str(path),
                                    '-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
a=pixels(frames/'sequence_0181.png');b=pixels(replacement/'replacement_0181.png')
replacement_pixel_difference=sum(abs(x-y) for x,y in zip(a,b))/len(a)
assert replacement_pixel_difference>2, 'Incoming prototype pass still contains the enclosure'

# Short, original synthetic plastic-connector click. No external sound assets.
sample_rate=48000;duration=15;click_time=251/24
samples=array.array('h',[0])*(sample_rate*duration)
random.seed(70)
click=[]
for i in range(round(.08*sample_rate)):
    t=i/sample_rate
    transient=random.uniform(-1,1)*.54*math.exp(-t/.005)
    body=.27*math.sin(2*math.pi*2150*t)*math.exp(-t/.010)
    tail=.19*math.sin(2*math.pi*860*t)*math.exp(-t/.015)
    click.append((1-math.exp(-t/.00018))*(transient+body+tail))
amplitude=.25/max(abs(v) for v in click)
onset=round(click_time*sample_rate)
for i,v in enumerate(click):samples[onset+i]=round(v*amplitude*32767)
wav=OUT/'connector-click-v07.wav'
with wave.open(str(wav),'wb') as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(sample_rate);f.writeframes(samples.tobytes())


def ease_expr(start,length):
    t=f'((T-{start})/{length})'
    return f'(pow({t},3)*(10-15*{t}+6*pow({t},2)))'


q=ease_expr(7,1)
replace_expr=f'if(lt(T,7),A,if(gte(T,8),A,A*(1-{q})+B*{q}))'
q=ease_expr(11.5,1.5)
photo_expr=f'if(lt(T,11.5),A,if(gte(T,13),B,A*(1-{q})+B*{q}))'
filters=("[0:v]format=gbrp,setpts=PTS-STARTPTS[case];"
         "[1:v]format=gbrp,tpad=start_mode=clone:start_duration=7:stop_mode=clone:stop_duration=3.5,setpts=PTS-STARTPTS[proto];"
         f"[case][proto]blend=all_expr='{replace_expr}':shortest=1,tpad=stop_mode=clone:stop_duration=3.5[cg];"
         "[2:v]crop=1362:766:0:118,scale=960:540:flags=lanczos,setsar=1,format=gbrp,setpts=PTS-STARTPTS[photo];"
         f"[cg][photo]blend=all_expr='{photo_expr}':shortest=1,format=yuv420p[out]")
photo=ROOT/'references/live-transition/prototype-phone-photo.png'
movie=OUT/'Full-sequence-preview-v07.mp4'
subprocess.run(['rtk','ffmpeg','-hide_banner','-loglevel','error','-y',
    '-framerate','24','-start_number','1','-i',str(frames/'sequence_%04d.png'),
    '-framerate','24','-start_number','169','-i',str(replacement/'replacement_%04d.png'),
    '-loop','1','-framerate','24','-i',str(photo),'-i',str(wav),
    '-filter_complex',filters,'-map','[out]','-map','3:a:0','-frames:v','360','-t','15',
    '-r','24','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',
    '-c:a','aac','-b:a','128k','-movflags','+faststart',str(movie)],check=True)
probe=json.loads(subprocess.check_output(['rtk','ffprobe','-v','error','-count_frames',
    '-show_entries','stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames,sample_rate:format=duration',
    '-of','json',str(movie)],text=True))
video=next(s for s in probe['streams'] if s['codec_type']=='video')
sound=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (video['width'],video['height'],video['r_frame_rate'],int(video['nb_read_frames']))==(960,540,'24/1',360)
assert sound['codec_name']=='aac' and int(sound['sample_rate'])==48000
assert abs(float(probe['format']['duration'])-15)<.001
subprocess.run(['rtk','ffmpeg','-v','error','-xerror','-i',str(movie),'-f','null','-'],check=True)
for seconds,name in [(7.5,'replacement'),(12.25,'photo-blend'),(14,'real-photo')]:
    subprocess.run(['rtk','ffmpeg','-v','error','-y','-ss',str(seconds),'-i',str(movie),'-frames:v','1',
                    str(OUT/f'full-sequence-{name}-v07.png')],check=True)
checkpoint=json.loads((OUT/'premium-materials-v04.json').read_text())
assert hashlib.sha256((OUT/checkpoint['master_scene']).read_bytes()).hexdigest()==checkpoint['master_sha256']
report={'status':'passed','movie':movie.name,'duration_seconds':15,'resolution':[960,540],
        'frames_decoded':360,'fps':24,'render_seconds':round(render_seconds,2),
        'rendered_CG_frames':276,'replacement_overlap_frames':24,'premium_shaders_used':False,
        'reused_main_frames':276 if repair_replacement else 0,
        'replacement_mean_pixel_difference':replacement_pixel_difference,
        'premium_master_unchanged':True,'real_photo_included':True,'click_seconds':click_time,
        'click_sample_onset':onset,'audio_peak_dBFS':20*math.log10(max(abs(v) for v in samples)/32767),
        'photo_sha256':hashlib.sha256(photo.read_bytes()).hexdigest(),'movie_bytes':movie.stat().st_size,
        'probe':probe,'ffmpeg_filter':filters}
(OUT/'full-sequence-movie-validation-v07.json').write_text(json.dumps(report,indent=2))
print('FULL_SEQUENCE_MOVIE_READY',json.dumps(report),flush=True)
