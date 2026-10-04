#!/usr/bin/python3
"""Restore files saved by prepare-router.py. Run copied script from its root backup directory."""
from pathlib import Path
import json
import shutil
import subprocess

backup = Path(__file__).resolve().parent
manifest = json.loads((backup / 'manifest.json').read_text())
def run(*args):
    subprocess.run(args, check=False)

run('systemctl', 'disable', '--now', 'pi-lan-dnsmasq.service')
run('systemctl', 'disable', '--now', 'nftables.service')
run('/usr/sbin/nft', 'destroy', 'table', 'inet', 'pi_router')
run('nmcli', 'connection', 'down', 'pi-iphone-lan')
for name, existed in manifest.items():
    destination = Path(name)
    if existed:
        shutil.copy2(backup / 'files' / name.lstrip('/'), destination)
    elif destination.is_file():
        destination.unlink()
run('systemctl', 'daemon-reload')
run('nmcli', 'general', 'reload')
run('nmcli', 'connection', 'reload')
print('Router configuration rolled back. USB management retained. Installed packages and SSH key retained.')
