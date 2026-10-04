"""v22: AirDrop label, SafeWall phrase and trimmed, accelerated live demonstration."""
import functools
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1];V=ROOT/'visualization';OUT=V/'launch-preview-v22'
edit=json.loads((OUT/'edit-timeline.json').read_text())
FPS=24;W,H=960,540;N=edit['frames'];DURATION=N/FPS;STEM='SafeWall-launch-preview-v22'
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
        if i%240==0:print('V22_ENCODE',i,N,flush=True)
    p.stdin.close();assert p.wait()==0,'See encode.log'
mixed=OUT/'final-mix.wav'
assert mixed.is_file(), 'Run prepare_launch_audio_v22.py first'
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
asr=json.loads((V/'voiceover-v22/final-edit-asr.json').read_text())
normal=lambda t:re.findall(r'[^\W_]+',t.lower())
assert normal(asr['text'])==normal((V/'VOICEOVER-APPROVED-v22.txt').read_text())
retime=json.loads((OUT/'live-retime.json').read_text())
for i,n in enumerate(retime['mapping_1_based'],1):
    expected=V/'launch-preview-v18/live-frames'/f'{n:04d}.png'
    actual=OUT/'live-frames'/f'{i:04d}.png'
    assert hashlib.sha256(expected.read_bytes()).digest()==hashlib.sha256(actual.read_bytes()).digest()
measurement=run(['ffmpeg','-hide_banner','-i',str(movie),'-vn','-af','loudnorm=I=-17:TP=-1:LRA=7:print_format=json','-f','null','-'])
levels=json.loads(re.search(r'\{\s*"input_i".*?\}',measurement.stdout+measurement.stderr,re.S).group())
assert float(levels['input_tp'])<-.5
report={'status':'technical_checks_passed','movie':movie.name,'duration_seconds':DURATION,'resolution':[960,540],'fps':24,'frames_decoded':N,'probe':probe,'loudness':levels,
 'new_blender_scenes':['radios'],'server_instances':3,'server_asset':'../../references/server-rack-v21/source.json',
 'emitted_name_instances':23,'emitted_text':'iPhone (Piotrek)','visible_discovery_label':'AirDrop',
 'outro_source':outro_source,'blender_closing_removed':True,'premium_master_unchanged':True,
 'narration_change':'Osobna brama replaced with SafeWall; complete sentence pickup, Daniel / Eleven v4',
 'canonical_text':'../VOICEOVER-APPROVED-v22.txt','independent_narration_ASR_all_120_tokens_match':True,
 'narration_time_stretch':False,'live_demo_speed_multiplier':1.35,'live_demo_source_frames_used':[9,209],
 'live_demo_output_frames':149,'live_demo_seconds':[57.75,63.95833333333333],
 'live_frame_hashes_match_originals':True,'browser_content_altered':False,
 'green_result_approx_seconds':[61.95,63.96], 'flat_explanatory_slides':False,'user_selected_existing_2D_brand_outro':True}
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
shutil.copy2(V/'voiceover-v22/SafeWall-voiceover-pl-daniel-v22.srt',OUT/(STEM+'.srt'))
# Only the review contact sheet uses drawn timestamps; these never enter the movie.
times=[18.5,23.6,26.5,31.5,39.5,44.9,46.7,49.,52.2,55.5,58.2,59.9,62.2,63.5,65.5,69.3]
sheet=Image.new('RGB',(1280,816),(20,25,33));d=ImageDraw.Draw(sheet)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
for j,t in enumerate(times):
    pic=image_at(round(t*FPS));x=j%4*320;y=j//4*204
    sheet.paste(pic.resize((320,180)),(x,y));d.text((x+8,y+182),f'{t:.2f} s',font=font,fill='white')
sheet.save(OUT/'contact-sheet.png')
print('V22_READY',str(movie),DURATION,'seconds',movie.stat().st_size,'bytes',flush=True)
