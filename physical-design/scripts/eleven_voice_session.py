"""Small interactive ElevenLabs client. API key lives only in process memory.

Run in a real terminal. getpass disables echo; the key is never an argument,
environment variable, file, header dump or log entry. JSON commands afterwards:
  {"op":"discover"}
  {"op":"generate","request":"request.json","stem":"voice-take-a"}
  {"op":"quit"}
Request files and outputs default to visualization/voiceover-v09/.
Use --output-dir to select another revision. No credentials are persisted.
"""
import argparse
import base64
import getpass
import json
import re
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--output-dir',type=Path)
args=parser.parse_args()
OUT=args.output_dir or Path(__file__).resolve().parents[1]/'visualization'/'voiceover-v09'
OUT.mkdir(exist_ok=True)
if not sys.stdin.isatty():raise SystemExit('A terminal with hidden password input is required.')
key=getpass.getpass('ElevenLabs API key (hidden, memory only): ')


def call(path,payload=None):
    # Only the service's official API host ever receives the credential.
    req=urllib.request.Request('https://api.elevenlabs.io'+path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={'xi-api-key':key,'Content-Type':'application/json','Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=120) as response:
        return json.load(response),response.headers.get('request-id')


print('VOICE_SESSION_READY',flush=True)
while True:
    try:
        line=input()
        if not line:continue
        command=json.loads(line)
        if command['op']=='quit':break
        if command['op']=='inspect':
            models,_=call('/v1/models')
            matches=[m for m in models if m['model_id']=='eleven_v4']
            (OUT/'available-v4-models.json').write_text(json.dumps(matches,indent=2))
            print('MODEL_AVAILABLE',bool(matches),flush=True)
            voice,_=call('/v1/voices/nPczCjzI2devNBz1zQrb')
            selected={k:voice.get(k) for k in ('voice_id','name','category','labels','description','settings')}
            (OUT/'selected-voice.json').write_text(json.dumps(selected,indent=2,ensure_ascii=False))
            print('VOICE',json.dumps(selected,ensure_ascii=False),flush=True)
        elif command['op']=='discover':
            models,_=call('/v1/models')
            matches=[{'model_id':m['model_id'],'name':m.get('name'),
                      'can_do_text_to_speech':m.get('can_do_text_to_speech')} for m in models if 'v4' in m['model_id']]
            (OUT/'available-v4-models.json').write_text(json.dumps(matches,indent=2))
            print('MODELS',json.dumps(matches),flush=True)
            data,_=call('/v2/voices?page_size=100')
            voices=[{k:v.get(k) for k in ('voice_id','name','category','labels','description','preview_url')}
                    for v in data.get('voices',[]) if v.get('category') in ('premade','professional')]
            (OUT/'available-voices.json').write_text(json.dumps(voices,indent=2))
            print('VOICES',json.dumps([{k:v[k] for k in ('voice_id','name','category','labels','description')} for v in voices],ensure_ascii=False),flush=True)
        elif command['op']=='generate':
            name=command['request'];stem=command['stem']
            assert re.fullmatch(r'[a-zA-Z0-9_.-]+\.json',name)
            assert re.fullmatch(r'[a-zA-Z0-9_-]+',stem)
            request=json.loads((OUT/name).read_text())
            assert request['model_id']=='eleven_v4'
            print('GENERATING',stem,flush=True)
            result,request_id=call('/v1/text-to-dialogue/with-timestamps?output_format=mp3_44100_128',request)
            encoded=result.pop('audio_base64')
            audio=base64.b64decode(encoded)
            (OUT/(stem+'.mp3')).write_bytes(audio)
            result['model_id']=request['model_id'];result['request_id']=request_id
            (OUT/(stem+'-alignment.json')).write_text(json.dumps(result,indent=2,ensure_ascii=False))
            print('VOICE_GENERATED',json.dumps({'file':stem+'.mp3','bytes':len(audio),
                'model':request['model_id'],'segments':result.get('voice_segments')}),flush=True)
        elif command['op']=='transcribe':
            name=command['file'];stem=command['stem']
            assert re.fullmatch(r'[a-zA-Z0-9_.-]+\.(mp3|wav)',name)
            assert re.fullmatch(r'[a-zA-Z0-9_-]+',stem)
            boundary='safewall-'+uuid.uuid4().hex
            parts=[]
            for field,value in {'model_id':'scribe_v2','language_code':'pol',
                                'tag_audio_events':'false','diarize':'false',
                                'timestamps_granularity':'word'}.items():
                parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"\r\n\r\n{value}\r\n').encode())
            parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: application/octet-stream\r\n\r\n').encode())
            parts.append((OUT/name).read_bytes())
            parts.append(f'\r\n--{boundary}--\r\n'.encode())
            req=urllib.request.Request('https://api.elevenlabs.io/v1/speech-to-text',
                data=b''.join(parts),headers={'xi-api-key':key,
                'Content-Type':'multipart/form-data; boundary='+boundary})
            print('TRANSCRIBING',name,flush=True)
            with urllib.request.urlopen(req,timeout=120) as response:
                result=json.load(response)
            (OUT/(stem+'-asr.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2))
            print('TRANSCRIPT',result.get('text'),flush=True)
        else:print('ERROR unknown operation',flush=True)
    except EOFError:break
    except urllib.error.HTTPError as exc:
        raw=exc.read().decode(errors='replace').replace(key,'[REDACTED]')
        print('API_ERROR',exc.code,raw[:1200],flush=True)
    except Exception as exc:
        print('ERROR',type(exc).__name__,str(exc).replace(key,'[REDACTED]')[:500],flush=True)
key=None
print('VOICE_SESSION_CLOSED',flush=True)
