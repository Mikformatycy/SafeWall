"""One approved phrase change and a shorter real-demo edit; preserve other voice."""
import json
import re
import subprocess
import wave
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1];V=ROOT/'visualization';VOICE=V/'voiceover-v22';OUT=V/'launch-preview-v22'
RATE=48000;DURATION=json.loads((OUT/'edit-timeline.json').read_text())['duration']
def run(args):return subprocess.run(['rtk',*args],check=True,capture_output=True)
def audio(p):return np.frombuffer(run(['ffmpeg','-v','error','-i',str(p),'-f','f32le','-ar',str(RATE),'-ac','1','-']).stdout,dtype='<f4').copy()
def save(p,data):
    with wave.open(str(p),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes((data*32767).astype('<i2').tobytes())
def norm(t):return re.findall(r'[^\W_]+',t.lower())

canonical=(V/'VOICEOVER-APPROVED-v22.txt').read_text()
asr=json.loads((VOICE/'gateway-pickup-asr.json').read_text())
assert norm(asr['text'])==norm('SafeWall ma pilnować jednej zasady: internet przez Tor albo brak połączenia.')
original=audio(V/'voiceover-v20/SafeWall-voiceover-pl-daniel-v20.wav')
pickup=audio(VOICE/'gateway-pickup.mp3')[:round(6.08*RATE)]
reference=original[round(33.22*RATE):round(39.1*RATE)]
active=pickup[abs(pickup)>.01];oldactive=reference[abs(reference)>.01]
gain=min(np.sqrt(np.mean(oldactive**2)/np.mean(active**2)),.84/max(abs(pickup)))
pickup*=gain
fade=round(.012*RATE);pickup[:fade]*=np.linspace(0,1,fade);pickup[-fade:]*=np.linspace(1,0,fade)
edited=original.copy();edited[round(33.10*RATE):round(39.42*RATE)]=0
at=round(33.10*RATE);edited[at:at+len(pickup)]+=pickup
track=np.zeros(round(DURATION*RATE))
# Preserve all speech before the ending and move the closing line with the outro.
track[:round(64.15*RATE)]=edited[:round(64.15*RATE)]
ending=original[round(66.90*RATE):]
start=round(64.15*RATE);track[start:start+len(ending)]=ending
assert max(abs(track))<1
wav=VOICE/'SafeWall-voiceover-pl-daniel-v22.wav';save(wav,track)
run(['ffmpeg','-v','error','-y','-i',str(wav),'-c:a','libmp3lame','-b:a','192k',str(wav.with_suffix('.mp3'))])
old=json.loads((V/'voiceover-v20/edit.json').read_text())
words=[]
for w in old['words']:
    if 33.10<=w['start']<39.42:continue
    w=w.copy()
    if w['start']>=66.9:w['start']-=2.75;w['end']-=2.75
    words.append(w)
for w in asr['words']:
    if w.get('type')=='word':words.append({**w,'start':w['start']+33.10,'end':w['end']+33.10})
words.sort(key=lambda w:w['start'])
assert norm(' '.join(w['text'] for w in words))==norm(canonical)
def stamp(t):
    ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
cues=[];batch=[]
for w in words:
    batch.append(w)
    if len(batch)>=9 or w['text'].endswith(('.', '!', '?')):cues.append(batch);batch=[]
if batch:cues.append(batch)
srt='\n\n'.join(f'{i}\n{stamp(c[0]["start"])} --> {stamp(c[-1]["end"])}\n'+' '.join(w['text'] for w in c) for i,c in enumerate(cues,1))+'\n'
(VOICE/'SafeWall-voiceover-pl-daniel-v22.srt').write_text(srt)
(VOICE/'edit.json').write_text(json.dumps({'duration_seconds':DURATION,'canonical_text':'../VOICEOVER-APPROVED-v22.txt','source':'../voiceover-v20/SafeWall-voiceover-pl-daniel-v20.wav','replacement_window':[33.10,39.42],'pickup_start':33.10,'pickup_end':33.10+len(pickup)/RATE,'pickup_gain':float(gain),'ending_source_start':66.90,'ending_new_start':64.15,'narration_time_stretch':False,'words':words},ensure_ascii=False,indent=2)+'\n')
# Re-time the RJ45 accent to the accelerated insertion, retaining the quiet edit sound design.
rng=np.random.default_rng(20);foley=np.zeros(round(DURATION*RATE))
insertion_time=57.75+(3.2-8/24)/1.35
events=[(21.25,'closure',.045,680),(24.3,'magnet',.075,1150),(insertion_time,'RJ45',.06,2050)]
for at,name,peak,hz in events:
    t=np.arange(round(.085*RATE))/RATE
    s=(rng.normal(0,.32,len(t))*np.exp(-t/.004)+.42*np.sin(2*np.pi*hz*t)*np.exp(-t/.012))*(1-np.exp(-t/.00015))
    s*=peak/max(abs(s));i=round(at*RATE);foley[i:i+len(s)]+=s
for at in [27.6,31.5,35.1,45.,49.1,63.9]:
    duration=.4;t=np.arange(round(duration*RATE))/RATE
    noise=np.convolve(rng.normal(0,1,len(t)),np.ones(35)/35,mode='same')
    s=noise*np.sin(np.pi*t/duration)**2*.025;i=round(at*RATE);foley[i:i+len(s)]+=s
save(OUT/'foley.wav',foley)
intro=ROOT/'references/seedance-v18/Seedance-rain-opening-original.mp4'
filters=(f'[0:a]aresample=48000,apad,atrim=duration={DURATION},asplit=2[vo][side];'
 '[1:a]aresample=48000,atrim=duration=16,asetpts=PTS-STARTPTS,highpass=f=65,'
 'loudnorm=I=-29:TP=-9:LRA=7,aresample=48000,afade=t=in:st=0:d=0.08,'
 f'afade=t=out:st=14.8:d=1.2,apad,atrim=duration={DURATION}[amb];'
 '[amb][side]sidechaincompress=threshold=0.05:ratio=3:attack=15:release=180[duck];'
 '[vo]pan=stereo|c0=c0|c1=c0[vost];[2:a]pan=stereo|c0=c0|c1=c0[fx];'
 '[vost][duck][fx]amix=inputs=3:normalize=0:duration=longest,alimiter=limit=0.841395:level=false:latency=true[out]')
run(['ffmpeg','-v','error','-y','-i',str(wav),'-i',str(intro),'-i',str(OUT/'foley.wav'),'-filter_complex',filters,'-map','[out]','-t',str(DURATION),'-ar','48000','-c:a','pcm_s24le',str(OUT/'final-mix.wav')])
(OUT/'audio-mix.json').write_text(json.dumps({'source_voice':str(wav.relative_to(V)),'foley_events':events,'music_added':False,'insertion_global_seconds':insertion_time,'original_live_audio_used':False,'filter':filters},indent=2)+'\n')
print('V22_AUDIO_READY',DURATION,'seconds;',len(norm(canonical)),'matching lexical tokens')
