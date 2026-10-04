#!/usr/bin/env python3
"""Reusable word-highlight captions: cached Whisper -> Chrome PNGs -> FFmpeg.

  rtk python3 marketing/captions/run.py build
  rtk python3 marketing/captions/run.py apply /path/to/new-video.mp4

Only transcribe.py contacts OpenAI. Applying captions never needs an API key.
"""
import argparse
import bisect
import hashlib
import html
import json
import math
from pathlib import Path
import re
import subprocess
from fractions import Fraction
import unicodedata

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CANONICAL = ROOT / 'physical-design/visualization/VOICEOVER-APPROVED-v22.txt'

def read(path):
    return json.loads(path.read_text())

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(args):
    p = subprocess.run(['rtk', *map(str, args)], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-6000:] + p.stdout[-2000:])
    return p.stdout

def normal(text):
    return ''.join(re.findall(r'[^\W_]+', unicodedata.normalize('NFC', text).lower()))

def display_words(text):
    words = []
    for word in text.split():
        if normal(word):
            words.append(word)
        elif words:
            words[-1] += ' ' + word
        else:
            raise ValueError('A phrase cannot start with punctuation only.')
    return words

def align(display, raw, text_key='word'):
    """Match character spans exactly, allowing split Wi-Fi / Nietrudno tokens."""
    source = [w for w in raw if normal(w[text_key])]
    expected = ''.join(normal(w) for w in display)
    actual = ''.join(normal(w[text_key]) for w in source)
    if actual != expected:
        raise ValueError('Transcript differs from the approved text. Review whisper.json; automatic fuzzy substitutions are disabled.')
    ends = []
    cursor = 0
    for w in source:
        cursor += len(normal(w[text_key]))
        ends.append(cursor)
    words = []
    cursor = 0
    for i, text in enumerate(display):
        start_index = bisect.bisect_right(ends, cursor)
        cursor += len(normal(text))
        end_index = bisect.bisect_left(ends, cursor)
        words.append({'index': i, 'text': text, 'start': float(source[start_index]['start']),
                      'end': float(source[end_index]['end']),
                      'whisper_indices': [start_index, end_index]})
    return words

def srt_time(seconds):
    ms = max(0, round(seconds * 1000))
    hour, ms = divmod(ms, 3600000)
    minute, ms = divmod(ms, 60000)
    sec, ms = divmod(ms, 1000)
    return f'{hour:02}:{minute:02}:{sec:02},{ms:03}'

def build():
    manifest = read(HERE / 'whisper.source.json')
    if sha(Path(manifest['audio'])) != manifest['audio_sha256']:
        raise ValueError('The narration changed. Run transcribe.py with the new audio before rebuilding.')
    lines = [line.strip() for line in (HERE / 'caption-lines.txt').read_text().splitlines() if line.strip()]
    if ' '.join(lines).split() != CANONICAL.read_text().split():
        raise ValueError('caption-lines.txt must contain exactly the approved words and punctuation.')
    chunks = [display_words(line) for line in lines]
    display = [word for chunk in chunks for word in chunk]
    words = align(display, read(HERE / 'whisper.json')['words'])
    corrections_path = HERE / 'timing-corrections.json'
    corrections = read(corrections_path) if corrections_path.exists() else []
    for correction in corrections:
        word = words[correction['word_index']]
        if word['text'] != correction['text']:
            raise ValueError('Timing correction does not match the current caption text.')
        word['whisper_original'] = {key: word[key] for key in ['start', 'end']}
        word.update({key: correction[key] for key in ['start', 'end'] if key in correction})
        word['correction_reason'] = correction['reason']
    # Whisper sometimes returns a zero-duration word at the following start.
    # Borrow a small part of the preceding interval so every spoken word gets a highlight.
    repairs = []
    for i in range(len(words) - 2, -1, -1):
        if words[i]['start'] >= words[i+1]['start']:
            lower = words[i-1]['start'] if i else 0
            old = words[i]['start']
            words[i]['start'] = max(lower + .02, words[i+1]['start'] - .10)
            repairs.append({'index': i, 'text': words[i]['text'], 'old_start': old, 'start': words[i]['start']})
    style = read(HERE / 'style.json')
    shift, tail = style['display_offset_seconds'], style['phrase_tail_seconds']
    events, phrases = [], []
    cursor = 0
    for ci, chunk in enumerate(chunks):
        ws = words[cursor:cursor + len(chunk)]
        cursor += len(chunk)
        next_start = words[cursor]['start'] + shift if cursor < len(words) else math.inf
        last_end = min(ws[-1]['end'] + shift + tail, next_start)
        phrase = {'text': lines[ci], 'start': max(0, ws[0]['start'] + shift), 'end': last_end}
        phrases.append(phrase)
        for wi, word in enumerate(ws):
            start = max(0, word['start'] + shift)
            end = ws[wi + 1]['start'] + shift if wi + 1 < len(ws) else last_end
            if end <= start:
                raise ValueError(f'Empty caption interval: {word}')
            spans = [f'<span class="hl">{html.escape(w["text"])}</span>' if j == wi else html.escape(w['text'])
                     for j, w in enumerate(ws)]
            events.append({'start': round(start, 6), 'end': round(end, 6), 'html': ' '.join(spans),
                           'phrase_index': ci, 'highlight_word': word['index'], 'highlight_text': word['text']})
    for a, b in zip(events, events[1:]):
        if a['end'] > b['start'] + 1e-6:
            raise ValueError('Overlapping caption events.')
    document = {'canonical_text': str(CANONICAL.relative_to(ROOT)), 'canonical_sha256': sha(CANONICAL),
        'audio_sha256': manifest['audio_sha256'], 'model': 'whisper-1',
        'source_words': len(read(HERE / 'whisper.json')['words']),
        'display_words': len(words), 'phrases': phrases, 'words': words, 'events': events,
        'timing_corrections': corrections, 'zero_duration_repairs': repairs,
        'display_offset_seconds': shift, 'phrase_tail_seconds': tail}
    save(HERE / 'events.json', document)
    (HERE / 'SafeWall-captions.srt').write_text('\n\n'.join(
        f'{i}\n{srt_time(p["start"])} --> {srt_time(p["end"])}\n{p["text"]}'
        for i, p in enumerate(phrases, 1)) + '\n')
    print('CAPTIONS_BUILT', len(phrases), 'phrases,', len(events), 'word highlights', flush=True)
    return document

def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path]))

def concat_path(path):
    return str(path).replace("'", "'\\''")

def audio_hash(path):
    return run(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:a:0', '-c:a', 'copy',
                '-f', 'hash', '-hash', 'sha256', '-']).strip()

def apply(video_path, output_path, offset, crf):
    doc = build()
    source, output = video_path.resolve(), output_path.resolve()
    if source == output:
        raise ValueError('Input and output must be different files.')
    info = probe(source)
    video = next(s for s in info['streams'] if s['codec_type'] == 'video')
    width, height = video['width'], video['height']
    fps_string = video['r_frame_rate']
    fps = float(Fraction(fps_string))
    duration = float(video.get('duration', info['format']['duration']))
    total_frames = int(video.get('nb_frames') or round(duration * fps))
    if doc['events'][-1]['end'] + offset > duration + 1 / fps:
        raise ValueError('Video ends before the final caption. Check the narration timeline.')
    source_hash = sha(source)
    cache_hash = hashlib.sha256()
    for p in ['events.json', 'style.json', 'caption.html', 'render_caps.cjs']:
        cache_hash.update((HERE / p).read_bytes())
    cache = HERE / 'renders' / f'{width}x{height}-{cache_hash.hexdigest()[:12]}'
    layout_path = cache / 'layout.json'
    if not layout_path.exists():
        print(run(['node', HERE / 'render_caps.cjs', HERE / 'events.json', HERE / 'style.json',
                   cache, width, height]), flush=True)
    layout = read(layout_path)
    if len(layout['bounds']) != len(doc['events']):
        raise ValueError('Incomplete caption PNG cache.')

    blank = cache / 'blank.png'
    pieces, cursor = [], 0
    def add(image, frames):
        if frames > 0:
            if not image.is_file():
                raise ValueError(f'Missing caption image: {image}')
            pieces.extend([f"file '{concat_path(image)}'", f'option framerate {fps_string}',
                           f'duration {frames / fps:.9f}'])
    for i, ev in enumerate(doc['events']):
        start = max(0, round((ev['start'] + offset) * fps))
        end = min(total_frames, round((ev['end'] + offset) * fps))
        if end <= start:
            continue
        add(blank, start - cursor)
        add(cache / f'cap_{i:03d}.png', end - start)
        cursor = end
    add(blank, total_frames - cursor)
    pieces.extend([f"file '{concat_path(blank)}'", f'option framerate {fps_string}'])
    sequence = cache / 'overlay.ffconcat'
    sequence.write_text('ffconcat version 1.0\n' + '\n'.join(pieces) + '\n')
    output.parent.mkdir(parents=True, exist_ok=True)
    print('ENCODING_CAPTIONED_VIDEO', output, flush=True)
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', source, '-f', 'concat', '-safe', '0', '-i', sequence,
         '-filter_complex', f'[1:v]format=rgba,setpts=PTS-STARTPTS[c];[0:v][c]overlay=0:{height-layout["stripHeight"]}:format=auto:eof_action=pass:repeatlast=0[v]',
         '-map', '[v]', '-map', '0:a:0', '-c:v', 'libx264', '-preset', 'fast', '-crf', str(crf),
         '-pix_fmt', 'yuv420p', '-r', fps_string, '-fps_mode', 'cfr', '-c:a', 'copy',
         '-t', f'{duration:.9f}', '-movflags', '+faststart', output])
    # Decode the complete export, check timing/dimensions and exact compressed audio data.
    run(['ffmpeg', '-v', 'error', '-xerror', '-i', output, '-f', 'null', '-'])
    output_info = probe(output)
    output_video = next(s for s in output_info['streams'] if s['codec_type'] == 'video')
    assert (output_video['width'], output_video['height']) == (width, height)
    assert output_video['r_frame_rate'] == fps_string
    assert int(output_video['nb_frames']) == total_frames
    assert abs(float(output_info['format']['duration']) - float(info['format']['duration'])) < .05
    original_audio, final_audio = audio_hash(source), audio_hash(output)
    assert original_audio == final_audio, 'Audio stream changed.'
    assert sha(source) == source_hash, 'Source video changed.'
    report = {'status': 'passed', 'source': str(source), 'output': str(output),
        'resolution': [width, height], 'fps': fps_string, 'frames': total_frames, 'duration': duration,
        'phrases': len(doc['phrases']), 'word_highlights': len(doc['events']),
        'source_sha256': source_hash, 'output_sha256': sha(output),
        'exact_compressed_audio_preserved': True, 'audio_hash': final_audio,
        'full_video_decode_passed': True, 'caption_png_layout_checked': True,
        'canonical_text_exact_match': True, 'whisper_model': 'whisper-1',
        'api_calls_during_apply': 0, 'additional_offset_seconds': offset,
        'caption_cache': str(cache), 'style': read(HERE / 'style.json')}
    save(output.with_suffix('.validation.json'), report)
    print('CAPTIONED_VIDEO_READY', output, flush=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('build', help='Build events and SRT from cached Whisper timings; offline.')
    p = sub.add_parser('apply', help='Render and burn captions onto a new picture edit; offline.')
    p.add_argument('video', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--offset', type=float, default=0, help='Extra uniform caption shift in seconds.')
    p.add_argument('--crf', type=int, default=18)
    args = parser.parse_args()
    if args.command == 'build':
        build()
    else:
        output = args.output or args.video.with_name(args.video.stem + '-captions.mp4')
        apply(args.video, output, args.offset, args.crf)

if __name__ == '__main__':
    main()
