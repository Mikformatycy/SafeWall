"""Use a verified portable Blender runtime to build the editable product scene."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CACHE=Path('/Users/piotrek/Library/Caches/safewall-render')
NAME='blender-4.5.14-macos-arm64.dmg'
archive=CACHE/NAME
expected_size=311909763
deadline=time.monotonic()+2400
last_bucket=-1
while not archive.exists() or archive.stat().st_size<expected_size:
    if time.monotonic()>deadline:raise RuntimeError('Portable Blender download did not finish within 40 minutes')
    size=archive.stat().st_size if archive.exists() else 0
    bucket=int(size/25_000_000)
    if bucket!=last_bucket:print(f'Blender download: {size/1e6:.1f} / {expected_size/1e6:.1f} MB',flush=True);last_bucket=bucket
    time.sleep(2)
expected=next(line.split()[0] for line in (CACHE/'blender-4.5.14.sha256').read_text().splitlines() if NAME in line)
actual=hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()
if actual!=expected:raise RuntimeError('Blender archive SHA256 mismatch')
print('Official Blender SHA256 verified',flush=True)
mount=CACHE/'blender-volume'
binary=mount/'Blender.app'/'Contents'/'MacOS'/'Blender'
if not binary.exists():
    mount.mkdir(exist_ok=True)
    subprocess.run(['rtk','hdiutil','attach',str(archive),'-readonly','-nobrowse','-mountpoint',str(mount)],check=True)
subprocess.run(['rtk',str(binary),'--version'],check=True)
(ROOT/'visualization'/'runtime.json').write_text(json.dumps({'blender_version':'4.5.14 LTS','runtime_path':str(binary),'source':'https://download.blender.org/release/Blender4.5/','sha256':actual,'portable_runtime':True},indent=2))
subprocess.run(['rtk',str(binary),'--background','--factory-startup','--threads','8','--python',str(ROOT/'scripts'/'build_product_scene.py'),'--','--preview'],check=True)
