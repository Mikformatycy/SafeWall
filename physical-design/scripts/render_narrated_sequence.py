"""Render v09 Workbench preview and mix the native-speed Eleven v4 narration.

Run in Blender on Full-sequence-voice-v09.blend. --encode-only reuses the PNGs.
The API is not used here; regeneration uses the saved request and a hidden key.
"""
import array
import hashlib
import json
import math
import re
import struct
import subprocess
import sys
import time
import wave
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'visualization'
plan=json.loads((OUT/'narrated-sequence-v09.json').read_text())
N=plan['frames'];FPS=plan['fps'];DURATION=plan['duration_seconds']
R0,R1=plan['replacement_frames'];P0,P1=plan['photo_frames']
scene=bpy.context.scene
assert scene['visual_revision'].startswith('v09')
assert scene.render.engine=='BLENDER_WORKBENCH'
assert (scene.render.resolution_x,scene.render.resolution_y,scene.render.fps)==(960,540,FPS)
frames=OUT/'narrated-sequence-frames-v09';frames.mkdir(exist_ok=True)
replacement=OUT/'narrated-sequence-replacement-v09';replacement.mkdir(exist_ok=True)
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
roles={name:[o for o in bpy.data.objects if o.get('sequence_role')==name]
       for name in ('enclosure','prototype','phone','cable')}
# Render re-evaluates animation. Mute visibility curves so each pass stays distinct.
for objects in roles.values():
    for obj in objects:
        if not obj.animation_data or not obj.animation_data.action:continue
        action=obj.animation_data.action
        curves=list(action.fcurves) if action.is_action_legacy else [fc for l in action.layers for s in l.strips for b in s.channelbags for fc in b.fcurves]
        for fc in curves:
            if fc.data_path=='hide_render':fc.mute=True


def phase(frame,incoming=False):
    for obj in roles['enclosure']:obj.hide_render=incoming or frame>R1
    for obj in roles['prototype']:obj.hide_render=not(incoming or frame>R1)
    for obj in roles['phone']:obj.hide_render=frame<plan['phone_visible_frame']
    for obj in roles['cable']:obj.hide_render=frame<plan['cable_arrival_frames'][0]
    if frame<plan['assembly_frames'][1]:
        for obj in roles['enclosure']:
            if obj.name.startswith(('OLED | battery percentage','OLED | percent unit','OLED | battery icon',
                                    'OLED | battery terminal','OLED | charge bar')):obj.hide_render=True


def run(args,**kwargs):
    return subprocess.run(['rtk',*args],check=True,**kwargs)


start=time.monotonic();encode_only='--encode-only' in sys.argv
for frame in ([] if encode_only else range(1,N+1)):
    scene.frame_set(frame);phase(frame)
    scene.render.filepath=str(frames/f'narrated_{frame:04d}.png');bpy.ops.render.render(write_still=True)
    if R0<=frame<=R1:
        phase(frame,True)
        scene.render.filepath=str(replacement/f'replacement_{frame:04d}.png');bpy.ops.render.render(write_still=True)
    if frame%24==0:print('NARRATED_RENDER_PROGRESS',frame,N,flush=True)
render_seconds=time.monotonic()-start
for folder,stem,first,last in [(frames,'narrated',1,N),(replacement,'replacement',R0,R1)]:
    for frame in range(first,last+1):
        data=(folder/f'{stem}_{frame:04d}.png').read_bytes()
        assert data[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',data[16:24])==(960,540)


def pixels(path):
    return run(['ffmpeg','-v','error','-i',str(path),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE).stdout


mid=(R0+R1)//2
a=pixels(frames/f'narrated_{mid:04d}.png');b=pixels(replacement/f'replacement_{mid:04d}.png')
replacement_difference=sum(abs(x-y) for x,y in zip(a,b))/len(a)
assert replacement_difference>2

# Original click timbre, new exact contact time; lower gain under narration.
with wave.open(str(OUT/'connector-click-v07.wav'),'rb') as f:
    assert (f.getnchannels(),f.getsampwidth(),f.getframerate())==(1,2,48000)
    old=array.array('h');old.frombytes(f.readframes(f.getnframes()))
click=array.array('h',(round(v*10**(-8/20)) for v in old[502000:505840]))
onset=round(plan['click_seconds']*48000)
samples=array.array('h',[0])*round(DURATION*48000);samples[onset:onset+len(click)]=click
wav=OUT/'connector-click-v09.wav'
with wave.open(str(wav),'wb') as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes(samples.tobytes())

# Two-pass level setting, no time stretching or pitch manipulation.
source=OUT/plan['voice_audio'];voice=OUT/'voiceover-v09/voice-pl-normalized-v09.wav'
measure=run(['ffmpeg','-hide_banner','-i',str(source),'-af','loudnorm=I=-19:TP=-2:LRA=7:print_format=json',
             '-f','null','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
measurement=json.loads(re.search(r'\{\s*"input_i".*?\}',measure.stderr,re.S).group())
normalizer=('loudnorm=I=-19:TP=-2:LRA=7:linear=true:'+':'.join([
    f'measured_I={measurement["input_i"]}',f'measured_TP={measurement["input_tp"]}',
    f'measured_LRA={measurement["input_lra"]}',f'measured_thresh={measurement["input_thresh"]}',
    f'offset={measurement["target_offset"]}']))
run(['ffmpeg','-v','error','-y','-i',str(source),'-af',normalizer,'-ar','48000','-ac','1','-c:a','pcm_s16le',str(voice)])
(OUT/'voiceover-v09/loudness-source-v09.json').write_text(json.dumps(measurement,indent=2))


def ease(start,length):
    t=f'max(0,min(1,(T-({start}))/({length})))'
    return f'(pow({t},3)*(10-15*{t}+6*pow({t},2)))'


q=ease((R0-1)/FPS,(R1-R0)/FPS)
swap=f'if(lt(T,{(R0-1)/FPS}),A,if(gte(T,{R1/FPS}),A,A*(1-{q})+B*{q}))'
q=f'max(0,min(1,(T-{(P0-1)/FPS})/{(P1-P0)/FPS}))'
photo_blend=f'if(lt(T,{(P0-1)/FPS}),A,if(gte(T,{(P1-1)/FPS}),B,A*(1-{q})+B*{q}))'
delay=round(plan['voice_offset_seconds']*48000)
filters=("[0:v]format=gbrp,setpts=PTS-STARTPTS[main];"
    f"[1:v]format=gbrp,tpad=start={R0-1}:stop={N-R1}:start_mode=clone:stop_mode=clone,setpts=PTS-STARTPTS[incoming];"
    f"[main][incoming]blend=all_expr='{swap}':shortest=1[cg];"
    "[2:v]crop=1362:766:0:118,scale=960:540:flags=lanczos,setsar=1,format=gbrp,setpts=PTS-STARTPTS[photo];"
    f"[cg][photo]blend=all_expr='{photo_blend}':shortest=1,format=yuv420p[out];"
    f"[4:a]adelay={delay}S:all=1,apad,atrim=duration={DURATION}[vo];"
    "[vo][3:a]amix=inputs=2:normalize=0:duration=longest,"
    "alimiter=limit=0.891251:level=false:latency=true,pan=stereo|c0=c0|c1=c0[audio]")
photo=ROOT/'references/live-transition/prototype-phone-photo.png'
movie=OUT/'Full-sequence-voice-v09.mp4'
run(['ffmpeg','-hide_banner','-loglevel','error','-y',
    '-framerate',str(FPS),'-start_number','1','-i',str(frames/'narrated_%04d.png'),
    '-framerate',str(FPS),'-start_number',str(R0),'-i',str(replacement/'replacement_%04d.png'),
    '-loop','1','-framerate',str(FPS),'-i',str(photo),'-i',str(wav),'-i',str(voice),
    '-filter_complex',filters,'-map','[out]','-map','[audio]','-frames:v',str(N),'-t',str(DURATION),
    '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',
    '-metadata','title=Polish launch preview v09','-movflags','+faststart',str(movie)])
probe=json.loads(run(['ffprobe','-v','error','-count_frames','-show_entries',
    'stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames,sample_rate,channels:format=duration',
    '-of','json',str(movie)],stdout=subprocess.PIPE,text=True).stdout)
v=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_read_frames']))==(960,540,'24/1',N)
assert any(s['codec_type']=='audio' for s in probe['streams'])
assert abs(float(probe['format']['duration'])-DURATION)<.001
run(['ffmpeg','-v','error','-xerror','-i',str(movie),'-f','null','-'])
freeze=run(['ffmpeg','-hide_banner','-i',str(movie),'-vf','freezedetect=n=-70dB:d=0.2',
            '-an','-f','null','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
events=[line for line in freeze.stderr.splitlines() if 'freeze_' in line]
(OUT/'narrated-freeze-check-v09.log').write_text(freeze.stderr)
assert not events,events
levels=run(['ffmpeg','-hide_banner','-i',str(movie),'-af','loudnorm=I=-16:TP=-1:LRA=7:print_format=json',
            '-vn','-f','null','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
final_levels=json.loads(re.search(r'\{\s*"input_i".*?\}',levels.stderr,re.S).group())
assert -18<float(final_levels['input_i'])<-14,final_levels
assert float(final_levels['input_tp'])<-.5,final_levels
for seconds,label in [(4.2,'replacement'),(plan['click_seconds'],'contact'),(7.4,'photo-blend'),((N-1)/FPS,'final-photo')]:
    run(['ffmpeg','-v','error','-y','-ss',str(seconds),'-i',str(movie),'-frames:v','1',str(OUT/f'narrated-{label}-v09.png')])
checkpoint=json.loads((OUT/'premium-materials-v04.json').read_text())
assert hashlib.sha256((OUT/checkpoint['master_scene']).read_bytes()).hexdigest()==checkpoint['master_sha256']
report={'status':'passed','movie':movie.name,'model_id':plan['model_id'],'voice_id':plan['voice_id'],
    'voice_language':'pl','voice_native_speed':True,'voice_offset_seconds':plan['voice_offset_seconds'],
    'spoken_end_seconds':plan['spoken_end_seconds'],'duration_seconds':DURATION,'resolution':[960,540],
    'fps':FPS,'frames_decoded':N,'render_seconds':round(render_seconds,2),'replacement_pixel_difference':replacement_difference,
    'click_seconds':plan['click_seconds'],'click_pitch_preserved':True,'click_gain_db':-8,
    'premium_master_unchanged':True,'freeze_check':{'threshold_db':-70,'minimum_duration_seconds':.2,'events':events},
    'audio_loudness':final_levels,'photo_blend_frames':plan['photo_frames'],'reused_render_frames':N if encode_only else 0,
    'source_scene':'Full-sequence-voice-v09.blend','probe':probe,'movie_bytes':movie.stat().st_size,
    'review_scope':'Frame/image inspection, timestamp sync, complete decode, loudness/peak and freeze checks. No human pronunciation review yet.'}
(OUT/'narrated-movie-validation-v09.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print('NARRATED_MOVIE_READY',json.dumps(report),flush=True)
