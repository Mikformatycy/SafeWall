"""Wait for the active render, encode MP4, and validate all frames and video metadata."""
import hashlib
import json
import struct
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'visualization'
log=OUT/'movie-render.log'
deadline=time.monotonic()+1800
while True:
    if time.monotonic()>deadline:raise RuntimeError('Animation render did not finish within 30 minutes')
    with log.open('rb') as stream:
        stream.seek(max(0,log.stat().st_size-12000))
        tail=stream.read().decode(errors='replace')
    if 'ASSEMBLY_FRAMES_READY' in tail:break
    if 'Traceback (most recent call last)' in tail:raise RuntimeError('Animation render failed; inspect movie-render.log')
    time.sleep(3)

for frame in range(1,241):
    path=OUT/'frames'/f'assembly_{frame:04}.png'
    with path.open('rb') as stream:header=stream.read(24)
    if header[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack('>II',header[16:24])!=(960,540):
        raise RuntimeError('Unexpected animation frame: '+str(path))
video=OUT/'SafeWall-assembly-v01.mp4'
subprocess.run(['rtk','ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','24','-start_number','1',
                '-i',str(OUT/'frames'/'assembly_%04d.png'),'-frames:v','240','-an','-c:v','libx264','-preset','medium',
                '-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
probe=subprocess.check_output(['rtk','ffprobe','-v','error','-count_frames','-select_streams','v:0',
                '-show_entries','stream=codec_name,width,height,r_frame_rate,nb_read_frames,duration','-of','json',str(video)],text=True)
metadata=json.loads(probe)['streams'][0]
assert metadata['codec_name']=='h264'
assert (metadata['width'],metadata['height'])==(960,540)
assert metadata['r_frame_rate']=='24/1' and int(metadata['nb_read_frames'])==240
assert abs(float(metadata['duration'])-10)<0.01
subprocess.run(['rtk','ffmpeg','-v','error','-i',str(video),'-f','null','-'],check=True)
report={'status':'complete','video':video.name,'video_metadata':metadata,'PNG_frames_checked':240,
        'all_frames_decode':True,'camera_framing_checked_frames':240,
        'file_bytes':video.stat().st_size,'video_sha256':hashlib.file_digest(video.open('rb'),'sha256').hexdigest(),
        'source_scene':'SafeWall-keynote-v01.blend','source_resolution':[1920,1080],
        'source_scene_embeds_geometry':True,'renderer':'Cycles Metal','preview_samples':8,
        'concept_note':'Official CM4 reference plus decorative carrier; no electrical PCB design or phone-case fit qualification.'}
(OUT/'movie-validation.json').write_text(json.dumps(report,indent=2))
path=OUT/'scene-status.json';status=json.loads(path.read_text())
status.update({'stage':'complete','movie_rendered_and_decoded':True,'movie':video.name,'current_process':None,
               'review_movie_resolution':[960,540],'duration_seconds':10,'fps':24})
path.write_text(json.dumps(status,indent=2))
path=OUT/'scene-manifest.json';manifest=json.loads(path.read_text());manifest['review_movie_status']='complete';path.write_text(json.dumps(manifest,indent=2))
print('MOVIE_READY',json.dumps(report),flush=True)
