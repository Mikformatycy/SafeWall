#!/usr/bin/env python3
"""Cache Whisper word timings. Credentials stay in memory, never in this folder."""
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.error
import urllib.request
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_AUDIO = ROOT / 'physical-design/visualization/voiceover-v22/SafeWall-voiceover-pl-daniel-v22.wav'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio', type=Path, default=DEFAULT_AUDIO)
    parser.add_argument('--output', type=Path, default=HERE / 'whisper.json')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    source = args.audio.resolve()
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    manifest_path = args.output.with_suffix('.source.json')
    if args.output.exists() and not args.force:
        manifest = json.loads(manifest_path.read_text())
        if manifest['audio_sha256'] != sha:
            parser.error('Audio changed. Use a new --output or explicitly pass --force.')
        print('WHISPER_CACHE_HIT', args.output)
        return

    key = os.environ.get('OPENAI_API_KEY') or getpass.getpass('OpenAI API key (not saved): ')
    if not key.strip():
        parser.error('Missing API key.')
    with tempfile.TemporaryDirectory(prefix='safewall-whisper-') as temp:
        mp3 = Path(temp) / 'narration.mp3'
        subprocess.run(['rtk', 'ffmpeg', '-v', 'error', '-y', '-i', str(source),
            '-vn', '-ac', '1', '-ar', '16000', '-b:a', '64k', str(mp3)], check=True)
        boundary = 'SafeWall' + uuid.uuid4().hex
        fields = [('model', 'whisper-1'), ('language', 'pl'),
                  ('response_format', 'verbose_json'),
                  ('timestamp_granularities[]', 'word'),
                  ('timestamp_granularities[]', 'segment'),
                  ('temperature', '0'),
                  ('prompt', 'SafeWall, Tor, iPhone (Piotrek), Wi-Fi, Bluetooth. Polski lektor.')]
        body = bytearray()
        for name, value in fields:
            body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="narration.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode())
        body.extend(mp3.read_bytes())
        body.extend(f'\r\n--{boundary}--\r\n'.encode())
        request = urllib.request.Request('https://api.openai.com/v1/audio/transcriptions',
            data=bytes(body), headers={'Authorization': 'Bearer ' + key.strip(),
            'Content-Type': 'multipart/form-data; boundary=' + boundary}, method='POST')
        print('WHISPER_TRANSCRIBING', source.name, flush=True)
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                result = json.load(response)
        except urllib.error.HTTPError as error:
            raise SystemExit(f'Whisper HTTP {error.code}; no credentials or response body logged.') from None
        finally:
            key = None
        if not result.get('words'):
            raise SystemExit('Whisper returned no word timestamps.')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        manifest = {'audio': str(source), 'audio_sha256': sha, 'model': 'whisper-1',
            'language': 'pl', 'timestamp_granularities': ['word', 'segment'],
            'documentation': 'https://developers.openai.com/api/docs/guides/speech-to-text',
            'credentials_saved': False}
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        print('WHISPER_SAVED', args.output, len(result['words']), 'words', flush=True)

if __name__ == '__main__':
    main()
