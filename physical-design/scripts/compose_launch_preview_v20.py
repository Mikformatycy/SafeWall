"""Assemble actual footage and Blender frames. No generated 2D graphic scenes."""
import functools
import hashlib
import json
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/'visualization'
OUT=V/'launch-preview-v20'
STEM='SafeWall-launch-preview-v20'
timeline=json.loads((OUT/'edit-timeline.json').read_text())
FPS=timeline['fps'];N=timeline['frames'];DURATION=timeline['duration'];W,H=timeline['resolution']
clips=timeline['clips']
for c in clips:
    c['start_frame']=round(c['start']*FPS);c['end_frame']=round(c['end']*FPS)

def run(args):
    r=subprocess.run(['rtk',*args],capture_output=True,text=True)
    if r.returncode:
        print(r.stdout,r.stderr);r.check_returncode()
    return r

def ease(x):
    x=max(0,min(1,x));return x*x*x*(10+x*(-15+6*x))

@functools.lru_cache(maxsize=8)
def frame(source,kind,index):
    return Image.open(V/('launch-preview-'+source)/(kind+'-frames')/f'{index:04d}.png').convert('RGB')

def image_at(i):
    active=[c for c in clips if c['start_frame']<=i<c['end_frame']]
    assert 1<=len(active)<=2,(i,active)
    def im(c):return frame(c['source'],c['name'],min(c['frames'],i-c['start_frame']+1))
    picture=im(active[0])
    if len(active)==2:
        a,b=active
        u=(i-b['start_frame'])/(a['end_frame']-b['start_frame'])
        picture=Image.blend(picture,im(b),ease(u))
    return picture

def contact_sheet():
    times=[2.5,14.9,18.5,23.6,26.5,29.5,33.5,39.5,45.5,49.8,53.2,55.5,58.4,61.4,64.8,69.5]
    sheet=Image.new('RGB',(1280,4*204),(20,25,33));d=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
    for j,t in enumerate(times):
        pic=image_at(round(t*FPS));x=j%4*320;y=j//4*204
        sheet.paste(pic.resize((320,180)),(x,y));d.text((x+8,y+182),f'{t:.1f} s',font=font,fill='white')
    sheet.save(OUT/'contact-sheet.png')
    print('V20_CONTACT_SHEET_READY')

if '--stills' in sys.argv:
    contact_sheet();raise SystemExit

for c in clips:
    missing=[i for i in range(1,c['frames']+1) if not (V/('launch-preview-'+c['source'])/(c['name']+'-frames')/f'{i:04d}.png').exists()]
    assert not missing,(c['name'],missing[:8])
picture=OUT/(STEM+'-picture.mp4')
with (OUT/'encode.log').open('w') as log:
    proc=subprocess.Popen(['rtk','ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(picture)],stdin=subprocess.PIPE,stderr=log)
    for i in range(N):
        proc.stdin.write(image_at(i).tobytes())
        if i%240==0:print('V20_ENCODE',i,N,flush=True)
    proc.stdin.close();assert proc.wait()==0,'See encode.log'

# Small original sound accents; the live clip keeps its original visual timing.
RATE=48000;rng=np.random.default_rng(20)
foley=np.zeros(round(DURATION*RATE))
events=[(21.25,'closure',.045,680),(24.3,'magnet',.075,1150),(60.95,'RJ45',.06,2050)]
for at,name,peak,hz in events:
    t=np.arange(round(.085*RATE))/RATE
    s=(rng.normal(0,.32,len(t))*np.exp(-t/.004)+.42*np.sin(2*np.pi*hz*t)*np.exp(-t/.012))*(1-np.exp(-t/.00015))
    s*=peak/max(abs(s));i=round(at*RATE);foley[i:i+len(s)]+=s
for at in [27.6,31.5,35.1,45.0,49.1,66.65]:
    length=.4;t=np.arange(round(length*RATE))/RATE
    noise=np.convolve(rng.normal(0,1,len(t)),np.ones(35)/35,mode='same')
    s=noise*np.sin(np.pi*t/length)**2*.025
    i=round(at*RATE);foley[i:i+len(s)]+=s
foley_path=OUT/'foley.wav'
with wave.open(str(foley_path),'wb') as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE)
    f.writeframes((foley*32767).astype('<i2').tobytes())
voice=V/'voiceover-v20/SafeWall-voiceover-pl-daniel-v20.wav'
intro=ROOT/'references/seedance-v18/Seedance-rain-opening-original.mp4'
mixed=OUT/'final-mix.wav'
filters=(f'[0:a]aresample=48000,apad,atrim=duration={DURATION},asplit=2[vo][side];'
         '[1:a]aresample=48000,atrim=duration=16,asetpts=PTS-STARTPTS,highpass=f=65,'
         'loudnorm=I=-29:TP=-9:LRA=7,aresample=48000,afade=t=in:st=0:d=0.08,'
         f'afade=t=out:st=14.8:d=1.2,apad,atrim=duration={DURATION}[amb];'
         '[amb][side]sidechaincompress=threshold=0.05:ratio=3:attack=15:release=180[duck];'
         '[vo]pan=stereo|c0=c0|c1=c0[vost];[2:a]pan=stereo|c0=c0|c1=c0[fx];'
         '[vost][duck][fx]amix=inputs=3:normalize=0:duration=longest,'
         'alimiter=limit=0.841395:level=false:latency=true[out]')
run(['ffmpeg','-v','error','-y','-i',str(voice),'-i',str(intro),'-i',str(foley_path),'-filter_complex',filters,'-map','[out]','-t',str(DURATION),'-ar','48000','-c:a','pcm_s24le',str(mixed)])
movie=OUT/(STEM+'.mp4')
run(['ffmpeg','-v','error','-y','-i',str(picture),'-i',str(mixed),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-t',str(DURATION),'-movflags','+faststart','-metadata','title=SafeWall — Blender preview v20',str(movie)])
probe=json.loads(run(['ffprobe','-v','error','-count_frames','-show_entries','stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames:format=duration,size','-of','json',str(movie)]).stdout)
s=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (s['width'],s['height'],s['r_frame_rate'],int(s['nb_read_frames']))==(960,540,'24/1',N)
assert abs(float(probe['format']['duration'])-DURATION)<.05
run(['ffmpeg','-v','error','-xerror','-i',str(movie),'-f','null','-'])
measure=run(['ffmpeg','-hide_banner','-i',str(movie),'-vn','-af','loudnorm=I=-17:TP=-1:LRA=7:print_format=json','-f','null','-'])
levels=json.loads(re.search(r'\{\s*"input_i".*?\}',measure.stdout+measure.stderr,re.S).group())
assert float(levels['input_tp'])<-.5,levels
checkpoint=json.loads((V/'premium-materials-v04.json').read_text())
assert hashlib.sha256((V/checkpoint['master_scene']).read_bytes()).hexdigest()==checkpoint['master_sha256']
asr=json.loads((V/'voiceover-v20/final-edit-asr.json').read_text())
normal=lambda t:re.findall(r'[^\W_]+',t.lower())
assert normal(asr['text'])==normal((V/'VOICEOVER-APPROVED-v20.txt').read_text())
report={'status':'technical_checks_passed','movie':movie.name,'duration_seconds':DURATION,'resolution':[W,H],'fps':FPS,'frames_decoded':N,'probe':probe,'loudness':levels,
        'all_new_CG':'BLENDER_WORKBENCH','new_scenes':['tor','radios','closing','docking'],'flat_slides':False,
        'premium_master_unchanged':True,'narrator':'Daniel / Eleven v4; original audio plus Tor sentence pickup',
        'approved_text':'../VOICEOVER-APPROVED-v20.txt','independent_narration_ASR_all_121_tokens_match':True,
        'narration_time_stretch':False,'live_demo_time_stretch':False,'live_demo_source_frames':215,'live_demo_seconds':[57.75,57.75+215/24],
        'green_result_approx_seconds':[63.75,66.708],'future_steps_removed':True,'connection_narration_removed':True,
        'seedance_opening_retained':True,'seedance_new_generation':False,'original_live_audio_used':False,'music_added':False,
        'transition_method':'Framing-matched eased cross-dissolves, no alteration of real browser result',
        'subjective_audio_listening':'Not claimed; transcript and level checks only'}
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
shutil.copy2(V/'voiceover-v20/SafeWall-voiceover-pl-daniel-v20.srt',OUT/(STEM+'.srt'))
contact_sheet()
print('V20_READY',str(movie),'seconds',DURATION,'bytes',movie.stat().st_size,flush=True)
