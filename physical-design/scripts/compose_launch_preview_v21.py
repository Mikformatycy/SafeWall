"""v21: downloaded server geometry, emitted names, user's marketing outro."""
import functools
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1];V=ROOT/'visualization';OUT=V/'launch-preview-v21'
edit=json.loads((OUT/'edit-timeline.json').read_text())
FPS=24;W,H=960,540;N=edit['frames'];DURATION=N/FPS;STEM='SafeWall-launch-preview-v21'
clips=edit['clips']
for c in clips:c['start_frame']=round(c['start']*FPS);c['end_frame']=round(c['end']*FPS)

def run(args):
    r=subprocess.run(['rtk',*args],capture_output=True,text=True)
    if r.returncode:print(r.stdout,r.stderr);r.check_returncode()
    return r

def ease(t):
    t=max(0,min(1,t));return t*t*t*(10+t*(-15+6*t))

@functools.lru_cache(maxsize=8)
def frame(revision,kind,n):
    return Image.open(V/('launch-preview-'+revision)/(kind+'-frames')/f'{n:04d}.png').convert('RGB')

def image_at(i):
    active=[c for c in clips if c['start_frame']<=i<c['end_frame']]
    assert 1<=len(active)<=2
    def sample(c):return frame(c['source'],c['name'],min(c['frames'],i-c['start_frame']+1))
    pic=sample(active[0])
    if len(active)==2:
        a,b=active;u=(i-b['start_frame'])/(a['end_frame']-b['start_frame'])
        pic=Image.blend(pic,sample(b),ease(u))
    return pic

for c in clips:
    folder=V/('launch-preview-'+c['source'])/(c['name']+'-frames')
    assert all((folder/f'{i:04d}.png').is_file() for i in range(1,c['frames']+1)),c['name']
picture=OUT/(STEM+'-picture.mp4')
with (OUT/'encode.log').open('w') as log:
    p=subprocess.Popen(['rtk','ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','960x540','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(picture)],stdin=subprocess.PIPE,stderr=log)
    for i in range(N):
        p.stdin.write(image_at(i).tobytes())
        if i%240==0:print('V21_ENCODE',i,N,flush=True)
    p.stdin.close();assert p.wait()==0,'See encode.log'
# Existing approved mix is unchanged; pad only for the additional outro tail.
mixed=OUT/'final-mix.wav'
run(['ffmpeg','-v','error','-y','-i',str(V/'launch-preview-v20/final-mix.wav'),'-af',f'apad,atrim=duration={DURATION}','-ar','48000','-c:a','pcm_s24le',str(mixed)])
movie=OUT/(STEM+'.mp4')
run(['ffmpeg','-v','error','-y','-i',str(picture),'-i',str(mixed),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-t',str(DURATION),'-movflags','+faststart',str(movie)])
probe=json.loads(run(['ffprobe','-v','error','-count_frames','-show_entries','stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames:format=duration,size','-of','json',str(movie)]).stdout)
video=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (video['width'],video['height'],video['r_frame_rate'],int(video['nb_read_frames']))==(960,540,'24/1',N)
assert abs(float(probe['format']['duration'])-DURATION)<.05
run(['ffmpeg','-v','error','-xerror','-i',str(movie),'-f','null','-'])
outro_source=json.loads((OUT/'outro-source.json').read_text())
assert hashlib.sha256((ROOT.parent/outro_source['path']).read_bytes()).hexdigest()==outro_source['sha256']
checkpoint=json.loads((V/'premium-materials-v04.json').read_text())
assert hashlib.sha256((V/checkpoint['master_scene']).read_bytes()).hexdigest()==checkpoint['master_sha256']
# Read decoded PCM from both files to confirm every pre-existing mixed sample is unchanged.
def pcm(p):return subprocess.run(['rtk','ffmpeg','-v','error','-i',str(p),'-f','s24le','-acodec','pcm_s24le','-'],capture_output=True,check=True).stdout
old=pcm(V/'launch-preview-v20/final-mix.wav');new=pcm(mixed)
assert new[:len(old)]==old and set(new[len(old):]) <= {0}
measurement=run(['ffmpeg','-hide_banner','-i',str(movie),'-vn','-af','loudnorm=I=-17:TP=-1:LRA=7:print_format=json','-f','null','-'])
levels=json.loads(re.search(r'\{\s*"input_i".*?\}',measurement.stdout+measurement.stderr,re.S).group())
assert float(levels['input_tp'])<-.5
report={'status':'technical_checks_passed','movie':movie.name,'duration_seconds':DURATION,'resolution':[960,540],'fps':24,'frames_decoded':N,'probe':probe,'loudness':levels,
 'new_blender_scenes':['tor','radios'],'server_instances':3,'server_asset':'../../references/server-rack-v21/source.json',
 'emitted_name_instances':23,'emitted_text':'iPhone (Piotrek)','discovery_context':'AirDrop · Wszyscy',
 'outro_source':outro_source,'blender_closing_removed':True,'premium_master_unchanged':True,
 'narration_unchanged_from_v20':True,'mix_prefix_sample_identical_to_v20':True,'only_silence_added_for_longer_outro':True,
 'live_demo_unchanged':True,'live_demo_time_stretch':False,'live_demo_source_frames':215,
 'live_demo_seconds':[57.75,57.75+215/24], 'flat_explanatory_slides':False,'user_selected_existing_2D_brand_outro':True}
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
shutil.copy2(V/'voiceover-v20/SafeWall-voiceover-pl-daniel-v20.srt',OUT/(STEM+'.srt'))
# Only the review contact sheet uses drawn timestamps; these never enter the movie.
times=[18.5,23.6,26.5,29.5,31.5,33.5,39.5,45.5,48.65,50.5,52.2,55.5,58.5,64.8,68.5,72.0]
sheet=Image.new('RGB',(1280,816),(20,25,33));d=ImageDraw.Draw(sheet)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
for j,t in enumerate(times):
    pic=image_at(round(t*FPS));x=j%4*320;y=j//4*204
    sheet.paste(pic.resize((320,180)),(x,y));d.text((x+8,y+182),f'{t:.2f} s',font=font,fill='white')
sheet.save(OUT/'contact-sheet.png')
print('V21_READY',str(movie),DURATION,'seconds',movie.stat().st_size,'bytes',flush=True)
