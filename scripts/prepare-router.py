#!/usr/bin/python3
"""Install reviewed configuration with a file-level backup, then validate. Does not activate the firewall."""
from pathlib import Path
import json
import os
import shutil
import subprocess

assert os.geteuid() == 0
stage = Path('/home/piotr/pi-router-staging')
backup = Path('/root/pi-router-backup-20261003')
assert not backup.exists(), 'Backup already exists; inspect before repeating deployment.'
backup.mkdir(mode=0o700)
manifest = {}
files = {
 'config/nftables.conf': '/etc/nftables.conf',
 'config/dnsmasq-lan.conf': '/etc/pi-router/dnsmasq-lan.conf',
 'config/pi-router.conf': '/etc/pi-router/router.conf',
 'config/pi-lan-dnsmasq.service': '/etc/systemd/system/pi-lan-dnsmasq.service',
 'config/pi-router-nftables-override.conf': '/etc/systemd/system/nftables.service.d/pi-router.conf',
 'config/90-pi-router-forwarding.conf': '/etc/sysctl.d/90-pi-router-forwarding.conf',
 'config/pi-iphone-lan.nmconnection': '/etc/NetworkManager/system-connections/pi-iphone-lan.nmconnection',
 'config/90-pi-lan-carrier.conf': '/etc/NetworkManager/conf.d/90-pi-lan-carrier.conf',
 'config/99-usb-admin-only.conf': '/etc/NetworkManager/dnsmasq-shared.d/99-usb-admin-only.conf',
 'scripts/pi-router-wan': '/usr/local/sbin/pi-router-wan',
 'scripts/pi-router-firewall': '/usr/local/sbin/pi-router-firewall',
 'scripts/pi-status': '/usr/local/bin/pi-status',
 'scripts/90-pi-router-wan': '/etc/NetworkManager/dispatcher.d/90-pi-router-wan',
}
for source, target in files.items():
    dest = Path(target)
    manifest[target] = dest.exists()
    if dest.exists():
        copy = backup / 'files' / target.lstrip('/')
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dest, copy)
(backup / 'manifest.json').write_text(json.dumps(manifest, indent=2))
shutil.copy2(stage / 'scripts/rollback-router.py', backup / 'rollback-router.py')
with (backup / 'ruleset.before.nft').open('w') as out:
    subprocess.run(['/usr/sbin/nft', 'list', 'ruleset'], stdout=out, check=True)
for source, target in files.items():
    dest = Path(target)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(stage / source, dest)
    dest.chmod(0o755 if source.startswith('scripts/') else 0o600 if target.endswith('.nmconnection') else 0o644)
Path('/var/lib/pi-router').mkdir(exist_ok=True)
shutil.chown('/var/lib/pi-router', user='nobody', group='nogroup')
Path('/run/pi-router').mkdir(exist_ok=True)
Path('/run/pi-router/wan-resolv.conf').write_text('# No active cellular uplink yet.\n')
commands = [
 ['/usr/sbin/nft', '-c', '-f', '/etc/nftables.conf'],
 ['/usr/sbin/dnsmasq', '--test', '--conf-file=/etc/pi-router/dnsmasq-lan.conf'],
 ['/usr/sbin/dnsmasq', '--test', '--conf-file=/etc/NetworkManager/dnsmasq-shared.d/99-usb-admin-only.conf'],
 ['systemctl', 'daemon-reload'],
 ['systemd-analyze', 'verify', '/etc/systemd/system/pi-lan-dnsmasq.service'],
]
try:
    for command in commands:
        subprocess.run(command, check=True)
except Exception:
    subprocess.run(['/usr/bin/python3', str(backup / 'rollback-router.py')])
    raise
print('All configuration checks passed. Backup:', backup)
