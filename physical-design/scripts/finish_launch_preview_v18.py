"""Mix the existing Daniel voice with checked Seedance SFX and light edit foley."""
import hashlib
import json
import math
import re
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'visualization/launch-preview-v18'
RATE=48000
DURATION=79.75
STEM='SafeWall-launch-preview-v18'


def run(args):
    result=subprocess.run(['rtk',*args],capture_output=True,text=True)
    if result.returncode:
        print(result.stdout, result.stderr, flush=True)
        result.check_returncode()
    return result


# Original short foley cues; no music or additional voice.
rng=np.random.default_rng(18)
track=np.zeros(round(DURATION*RATE),dtype=np.float64)
events=[{'time':21.25,'kind':'enclosure closure','peak':.045,'tone':680},
        {'time':24.325,'kind':'magnetic attachment','peak':.10,'tone':1150},
        {'time':62.95,'kind':'RJ45 insertion accent','peak':.06,'tone':2050}]
for event in events:
    t=np.arange(round(.085*RATE))/RATE
    click=(rng.normal(0,.32,len(t))*np.exp(-t/.004)
           +.42*np.sin(2*np.pi*event['tone']*t)*np.exp(-t/.012))*(1-np.exp(-t/.00015))
    click*=event['peak']/np.max(np.abs(click))
    start=round(event['time']*RATE);track[start:start+len(click)]+=click
foley=OUT/'edit-foley.wav'
with wave.open(str(foley),'wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE)
    w.writeframes((np.clip(track,-1,1)*32767).astype('<i2').tobytes())

voice=ROOT/'visualization/voiceover-v16/SafeWall-voiceover-pl-daniel-v16.wav'
intro=ROOT/'references/seedance-v18/Seedance-rain-opening-original.mp4'
picture=OUT/(STEM+'-picture.mp4')
mixed=OUT/'final-mix.wav'
filters=(f'[0:a]aresample=48000,apad,atrim=duration={DURATION},asplit=2[vo][side];'
         '[1:a]aresample=48000,atrim=duration=16.0,asetpts=PTS-STARTPTS,'
         'highpass=f=65,loudnorm=I=-29:TP=-9:LRA=7,aresample=48000,'
         'afade=t=in:st=0:d=0.08,afade=t=out:st=14.8:d=1.2,apad,'
         f'atrim=duration={DURATION}[amb];'
         '[amb][side]sidechaincompress=threshold=0.05:ratio=3:attack=15:release=180[duck];'
         '[vo]pan=stereo|c0=c0|c1=c0[vost];'
         '[2:a]pan=stereo|c0=c0|c1=c0[foley];'
         '[vost][duck][foley]amix=inputs=3:normalize=0:duration=longest,'
         'alimiter=limit=0.841395:level=false:latency=true[out]')
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(voice),'-i',str(intro),'-i',str(foley),
     '-filter_complex',filters,'-map','[out]','-t',str(DURATION),'-ar','48000','-c:a','pcm_s24le',str(mixed)])
movie=OUT/(STEM+'.mp4')
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(picture),'-i',str(mixed),
     '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k',
     '-t',str(DURATION),'-movflags','+faststart','-metadata','title=SafeWall — pełny podgląd z Danielem',str(movie)])
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(movie),'-vn','-ac','1','-c:a','libmp3lame','-b:a','128k',str(OUT/'final-audio-check.mp3')])
probe=json.loads(run(['ffprobe','-v','error','-count_frames','-show_entries',
     'stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames,sample_rate,channels:format=duration,size',
     '-of','json',str(movie)]).stdout)
v=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_read_frames']))==(960,540,'24/1',1914),probe
assert abs(float(probe['format']['duration'])-DURATION)<.05
run(['ffmpeg','-hide_banner','-loglevel','error','-xerror','-i',str(movie),'-f','null','-'])
measurement=run(['ffmpeg','-hide_banner','-i',str(movie),'-vn','-af','loudnorm=I=-17:TP=-1:LRA=7:print_format=json','-f','null','-'])
levels=json.loads(re.search(r'\{\s*"input_i".*?\}',measurement.stdout+measurement.stderr,re.S).group())
assert float(levels['input_tp'])<-.5,levels
checkpoint=json.loads((ROOT/'visualization/premium-materials-v04.json').read_text())
premium=ROOT/'visualization'/checkpoint['master_scene']
assert hashlib.sha256(premium.read_bytes()).hexdigest()==checkpoint['master_sha256'],'Premium source modified'
original=Path('/Users/piotrek/Downloads/e5334818-4df6-41ef-b4a6-1e2f16a97973.mp4')
assert hashlib.sha256(original.read_bytes()).digest()==hashlib.sha256(intro.read_bytes()).digest()
sfx_asr=json.loads((OUT/'seedance-sfx-check-asr.json').read_text())
assert not sfx_asr.get('text','').strip(),'Unexpected speech in Seedance SFX'
report={'status':'technical_checks_passed_final_transcript_pending','movie':movie.name,'duration_seconds':DURATION,
        'resolution':[960,540],'fps':24,'frames_decoded':1914,'probe':probe,'loudness':levels,
        'workbench_only_new_CG':True,'premium_master_unchanged':True,'downloaded_seedance_unchanged':True,
        'narration':'Daniel, Eleven v4, approved v14 script, v16 audio; no time stretch',
        'seedance_sfx_ASR_detected_speech':False,'music_added':False,'original_live_audio_used':False,
        'live_footage':'Actual user-supplied IMG_4626, counterclockwise rotation previously baked; native speed',
        'live_global_seconds':[59.75,68.708333],'foley_events':events,'mix_filter':filters,
        'transition_method':'Eased framing-matched cross-dissolves; 3D-to-live is a preview composite, not a finished optical morph',
        'live_result_readability':'Green result from approximately 65.75 s; source footage is only 848x464 after rotation',
        'subjective_audio_listening':'Not claimed; transcript and level checks only'}
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
shutil.copy2(ROOT/'visualization/voiceover-v16/SafeWall-voiceover-pl-daniel-v16.srt',OUT/(STEM+'.srt'))
print('V18_MOVIE_READY',json.dumps({'movie':str(movie),'seconds':DURATION,'bytes':movie.stat().st_size,'loudness':levels},ensure_ascii=False),flush=True)
