"""Edit approved Daniel recordings; only the revised Tor sentence is a pickup."""
import json
import re
import subprocess
import wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'visualization'
OUT = V / 'launch-preview-v20'
VOICE = V / 'voiceover-v20'
OUT.mkdir(exist_ok=True)
RATE = 48000
DURATION = 71.0

def run(args):
    return subprocess.run(['rtk', *args], check=True, capture_output=True)

def read_audio(path):
    raw = run(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ar',str(RATE),'-ac','1','-']).stdout
    return np.frombuffer(raw, dtype='<f4').copy()

def norm(text):
    return re.findall(r'[^\W_]+', text.lower(), re.UNICODE)

canonical = (V/'VOICEOVER-APPROVED-v20.txt').read_text()
old_asr = json.loads((V/'voiceover-v16/SafeWall-voiceover-pl-daniel-v16-final-asr.json').read_text())
pickup_asr = json.loads((VOICE/'tor-pickup-asr.json').read_text())
assert norm(pickup_asr['text']) == norm('SafeWall ma kierować połączenia przez anonimizującą sieć Tor.')
sources = {'v16':read_audio(V/'voiceover-v16/SafeWall-voiceover-pl-daniel-v16.wav'),
           'pickup':read_audio(VOICE/'tor-pickup.mp3')}
# Boundaries fall in pauses, around ASR-verified complete sentences.
segments = [
    {'source':'v16','in':0.,'out':25.30,'at':0.,'purpose':'Original opening, product and powerbank'},
    {'source':'pickup','in':0.,'out':4.56,'at':25.50,'purpose':'Revised Tor sentence'},
    {'source':'v16','in':33.80,'out':48.04,'at':30.10,'purpose':'Separate gateway and fail-closed principle'},
    {'source':'v16','in':48.10,'out':56.16,'at':44.40,'purpose':'Nearby discovery and iPhone (Piotrek)'},
    {'source':'v16','in':56.30,'out':61.48,'at':52.60,'purpose':'Phone radio interfaces'},
    {'source':'v16','in':68.60,'out':69.78,'at':58.20,'purpose':'To nasz prototyp, over actual footage'},
    {'source':'v16','in':75.58,'out':79.44,'at':66.90,'purpose':'Final SafeWall line'},
]
mix = np.zeros(round(DURATION*RATE),dtype=np.float64)
words = []
for seg in segments:
    buf = sources[seg['source']][round(seg['in']*RATE):round(seg['out']*RATE)].astype(np.float64)
    # Match the sentence pickup's speech RMS to the original sentence.
    if seg['source']=='pickup':
        old=sources['v16'][round(25.5*RATE):round(27.98*RATE)]
        active=buf[np.abs(buf)>.01]
        ref=old[np.abs(old)>.01]
        gain=min(np.sqrt(np.mean(ref**2)/np.mean(active**2)), .84/np.max(np.abs(buf)))
        buf*=gain
        seg['gain']=float(gain)
    fade=round(.012*RATE)
    buf[:fade]*=np.linspace(0,1,fade)
    buf[-fade:]*=np.linspace(1,0,fade)
    i=round(seg['at']*RATE);mix[i:i+len(buf)]+=buf
    transcript = pickup_asr if seg['source']=='pickup' else old_asr
    for w in transcript['words']:
        if w.get('type')=='word' and seg['in'] <= w['start'] < seg['out']:
            assert w['end'] <= seg['out'], ('Truncated word', w)
            words.append({**w,'start':w['start']-seg['in']+seg['at'],'end':w['end']-seg['in']+seg['at']})
assert norm(' '.join(w['text'] for w in words)) == norm(canonical), 'Edited transcript differs from approved v20'
assert np.max(np.abs(mix)) < 1, 'Narration clips'
wav=VOICE/'SafeWall-voiceover-pl-daniel-v20.wav'
with wave.open(str(wav),'wb') as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE)
    f.writeframes((mix*32767).astype('<i2').tobytes())
run(['ffmpeg','-v','error','-y','-i',str(wav),'-c:a','libmp3lame','-b:a','192k',str(wav.with_suffix('.mp3'))])
def stamp(t):
    ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
cues=[];batch=[]
for w in words:
    batch.append(w)
    if len(batch)>=9 or w['text'].endswith(('.', '?', '!')):
        cues.append(batch);batch=[]
if batch:cues.append(batch)
srt='\n\n'.join(f'{i}\n{stamp(c[0]["start"])} --> {stamp(c[-1]["end"])}\n'+ ' '.join(w['text'] for w in c) for i,c in enumerate(cues,1))+'\n'
(VOICE/'SafeWall-voiceover-pl-daniel-v20.srt').write_text(srt)
(VOICE/'edit.json').write_text(json.dumps({'duration_seconds':DURATION,'segments':segments,'words':words,'canonical_text':'../VOICEOVER-APPROVED-v20.txt','word_check':'All retained ASR tokens and pickup ASR match canonical v20','narration_time_stretch':False,'demo_has_intentional_space_for_source_action':True},ensure_ascii=False,indent=2)+'\n')
clips=[
    {'name':'seedance','start':0.,'end':15.50,'frames':372,'source':'v18'},
    {'name':'assembly','start':15.,'end':22.,'frames':168,'source':'v18'},
    {'name':'docking','start':21.75,'end':25.75,'frames':96,'source':'v20'},
    {'name':'tor','start':25.50,'end':44.50,'frames':456,'source':'v20'},
    {'name':'radios','start':44.25,'end':54.,'frames':234,'source':'v20'},
    {'name':'prototype','start':53.50,'end':58.25,'frames':114,'source':'v18'},
    {'name':'live','start':57.75,'end':57.75+215/24,'frames':215,'source':'v18'},
    {'name':'closing','start':66.4583333333,'end':71.,'frames':109,'source':'v20'},
]
(OUT/'edit-timeline.json').write_text(json.dumps({'fps':24,'resolution':[960,540],'duration':DURATION,'frames':1704,'clips':clips,'voice':'../voiceover-v20/SafeWall-voiceover-pl-daniel-v20.wav','native_speed_live_demo':True,'all_new_visuals':'BLENDER_WORKBENCH','flat_slides':False},indent=2)+'\n')
print('V20_AUDIO_READY',DURATION,'seconds;',len(norm(canonical)),'verified lexical tokens; native-speed demo retained')
