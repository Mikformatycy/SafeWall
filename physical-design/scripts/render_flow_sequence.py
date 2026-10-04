"""Render the nine-second overlapping sequence, preserving click pitch and sync."""
import array
import hashlib
import json
import struct
import subprocess
import sys
import time
import wave
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'visualization'
scene=bpy.context.scene
assert scene['visual_revision'].startswith('v08')
assert scene.render.engine=='BLENDER_WORKBENCH'
assert (scene.render.resolution_x,scene.render.resolution_y,scene.render.fps)==(960,540,24)
frames=OUT/'flow-sequence-frames-v08';frames.mkdir(exist_ok=True)
replacement=OUT/'flow-sequence-replacement-v08';replacement.mkdir(exist_ok=True)
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
roles={name:[o for o in bpy.data.objects if o.get('sequence_role')==name]
       for name in ('enclosure','prototype','phone','cable')}
for objects in roles.values():
    for obj in objects:
        if not obj.animation_data or not obj.animation_data.action:continue
        action=obj.animation_data.action
        curves=list(action.fcurves) if action.is_action_legacy else [fc for l in action.layers for s in l.strips for b in s.channelbags for fc in b.fcurves]
        for fc in curves:
            if fc.data_path=='hide_render':fc.mute=True


def phase(frame,incoming=False):
    for obj in roles['enclosure']:obj.hide_render=incoming or frame>=114
    for obj in roles['prototype']:obj.hide_render=not(incoming or frame>=114)
    for obj in roles['phone']:obj.hide_render=frame<34
    for obj in roles['cable']:obj.hide_render=frame<105
    if frame<67:
        for obj in roles['enclosure']:
            if obj.name.startswith(('OLED | battery percentage','OLED | percent unit','OLED | battery icon',
                                    'OLED | battery terminal','OLED | charge bar')):obj.hide_render=True


start=time.monotonic()
encode_only='--encode-only' in sys.argv
for frame in ([] if encode_only else range(1,217)):
    scene.frame_set(frame);phase(frame)
    scene.render.filepath=str(frames/f'flow_{frame:04d}.png');bpy.ops.render.render(write_still=True)
    if 89<=frame<=113:
        phase(frame,True)
        scene.render.filepath=str(replacement/f'replacement_{frame:04d}.png');bpy.ops.render.render(write_still=True)
    if frame%24==0:print('FLOW_RENDER_PROGRESS',frame,216,flush=True)
render_seconds=time.monotonic()-start
for folder,stem,first,last in [(frames,'flow',1,216),(replacement,'replacement',89,113)]:
    for f in range(first,last+1):
        data=(folder/f'{stem}_{f:04d}.png').read_bytes()
        assert data[:8]==b'\x89PNG\r\n\x1a\n'
        assert struct.unpack('>II',data[16:24])==(960,540)


def pixels(path):
    return subprocess.check_output(['rtk','ffmpeg','-v','error','-i',str(path),'-frames:v','1',
                                    '-f','rawvideo','-pix_fmt','rgb24','-'])


a=pixels(frames/'flow_0101.png');b=pixels(replacement/'replacement_0101.png')
replacement_difference=sum(abs(x-y) for x,y in zip(a,b))/len(a)
assert replacement_difference>2

# Keep the original click unchanged; move its onset to the new insertion frame.
with wave.open(str(OUT/'connector-click-v07.wav'),'rb') as f:
    assert (f.getnchannels(),f.getsampwidth(),f.getframerate())==(1,2,48000)
    old=array.array('h');old.frombytes(f.readframes(f.getnframes()))
onset=352000;click=old[502000:505840]
samples=array.array('h',[0])*(9*48000);samples[onset:onset+len(click)]=click
wav=OUT/'connector-click-v08.wav'
with wave.open(str(wav),'wb') as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes(samples.tobytes())


def ease(start,length):
    t=f'max(0,min(1,(T-({start}))/({length})))'
    return f'(pow({t},3)*(10-15*{t}+6*pow({t},2)))'


q=ease('88/24','1')
swap=f'if(lt(T,88/24),A,if(gte(T,113/24),A,A*(1-{q})+B*{q}))'
q='max(0,min(1,(T-7)/(47/24)))'  # Constant-rate handoff, no slow static-looking tail.
photo_blend=f'if(lt(T,168/24),A,if(gte(T,215/24),B,A*(1-{q})+B*{q}))'
filters=("[0:v]format=gbrp,setpts=PTS-STARTPTS[main];"
         "[1:v]format=gbrp,tpad=start=88:stop=103:start_mode=clone:stop_mode=clone,setpts=PTS-STARTPTS[incoming];"
         f"[main][incoming]blend=all_expr='{swap}':shortest=1[cg];"
         "[2:v]crop=1362:766:0:118,scale=960:540:flags=lanczos,setsar=1,format=gbrp,setpts=PTS-STARTPTS[photo];"
         f"[cg][photo]blend=all_expr='{photo_blend}':shortest=1,format=yuv420p[out]")
photo=ROOT/'references/live-transition/prototype-phone-photo.png'
movie=OUT/'Full-sequence-flow-v08.mp4'
subprocess.run(['rtk','ffmpeg','-hide_banner','-loglevel','error','-y',
    '-framerate','24','-start_number','1','-i',str(frames/'flow_%04d.png'),
    '-framerate','24','-start_number','89','-i',str(replacement/'replacement_%04d.png'),
    '-loop','1','-framerate','24','-i',str(photo),'-i',str(wav),
    '-filter_complex',filters,'-map','[out]','-map','3:a:0','-frames:v','216','-t','9',
    '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k',
    '-movflags','+faststart',str(movie)],check=True)
probe=json.loads(subprocess.check_output(['rtk','ffprobe','-v','error','-count_frames',
    '-show_entries','stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames,sample_rate:format=duration',
    '-of','json',str(movie)],text=True))
v=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_read_frames']))==(960,540,'24/1',216)
assert any(s['codec_type']=='audio' for s in probe['streams'])
assert abs(float(probe['format']['duration'])-9)<.001
subprocess.run(['rtk','ffmpeg','-v','error','-xerror','-i',str(movie),'-f','null','-'],check=True)
for seconds,label in [(4.2,'replacement'),(8.2,'photo-blend'),(215/24,'final-photo')]:
    subprocess.run(['rtk','ffmpeg','-v','error','-y','-ss',str(seconds),'-i',str(movie),'-frames:v','1',
                    str(OUT/f'flow-{label}-v08.png')],check=True)
checkpoint=json.loads((OUT/'premium-materials-v04.json').read_text())
assert hashlib.sha256((OUT/checkpoint['master_scene']).read_bytes()).hexdigest()==checkpoint['master_sha256']
report={'status':'passed','movie':movie.name,'duration_seconds':9,'resolution':[960,540],'fps':24,
        'frames_decoded':216,'render_seconds':round(render_seconds,2),'replacement_pixel_difference':replacement_difference,
        'click_seconds':176/24,'click_pitch_preserved':True,'premium_master_unchanged':True,'static_holds':False,
        'photo_blend_frames':[169,216],'reused_render_frames':216 if encode_only else 0,
        'source_scene':'Full-sequence-flow-v08.blend','probe':probe,'movie_bytes':movie.stat().st_size}
(OUT/'flow-movie-validation-v08.json').write_text(json.dumps(report,indent=2))
print('FLOW_MOVIE_READY',json.dumps(report),flush=True)
