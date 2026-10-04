#!/usr/bin/env python3
"""Export reviewed project assets into an existing checkout; never commit or push.

Dry-run by default. Keeps destination-only files and its complete Git history.
Selection is explicit so adding local recordings or credentials cannot publish them.
"""
import argparse
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_PARTS = {'.git', '.artifacts', '.render', '.pdf-venv', '.venv',
                 'node_modules', '__pycache__', 'logs', 'backups', 'output', 'tmp', 'renders'}
BLOCKED_SUFFIXES = {'.mp4', '.mov', '.mp3', '.wav', '.blend', '.blend1', '.blend2',
                    '.log', '.pyc', '.pem', '.key', '.mobileconfig', '.nmconnection'}
SECRETS = [
    re.compile(rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{25,}'),
    re.compile(rb'gh[pousr]_[A-Za-z0-9]{25,}'),
    re.compile(rb'github_pat_[A-Za-z0-9_]{30,}'),
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY'),
    re.compile(rb'AKIA[A-Z0-9]{16}'),
]


def selection():
    files = {}

    def add(pattern):
        for source in ROOT.glob(pattern):
            if not source.is_file() or source.is_symlink():
                continue
            relative = source.relative_to(ROOT)
            if any(p in BLOCKED_PARTS for p in relative.parts):
                continue
            if source.suffix.lower() in BLOCKED_SUFFIXES or source.name == '.DS_Store':
                continue
            files[relative.as_posix()] = source

    for pattern in ['*.md', '.gitignore', '.gitattributes', 'docs/*.md', 'scripts/*.py', 'scripts/*.txt', 'scripts/*.md',
                    'scripts/pi-*', 'scripts/90-pi-router-wan', 'dashboard/**/*',
                    'brand/**/*', 'marketing/**/*', 'projekt/Draft-projektu.*',
                    'projekt/README.md', 'projekt/prezentacja/*',
                    'projekt/prezentacja/reference/tor-logo-white.svg',
                    'physical-design/*.md', 'physical-design/*.json',
                    'physical-design/*.svg', 'physical-design/fusion-*.png',
                    'physical-design/layout-*.png', 'physical-design/scripts/*.py',
                    'physical-design/exports/*', 'physical-design/visualization/*.txt',
                    'physical-design/visualization/*.json',
                    'physical-design/visualization/*-preview-v04.png',
                    'physical-design/references/**/source.json',
                    'physical-design/references/server-rack-v21/README.txt',
                    'physical-design/references/live-demo-v13/README.txt',
                    'physical-design/references/live-demo-v13/connection-02.0s.png',
                    'physical-design/references/live-demo-v13/tor-positive-07.0s.png',
                    'physical-design/references/live-demo-v13/entry-00.0s.png',
                    'references/*.md', 'mock-check-tor/README.md',
                    'mock-check-tor/safewall-domain', 'mock-check-tor/site/**/*']:
        add(pattern)
    for rev in [18, 20, 21, 22]:
        for name in ['README.txt', '*.json', 'contact-sheet.png']:
            add(f'physical-design/visualization/launch-preview-v{rev}/{name}')
    for rev in [12, 16, 20, 22]:
        for name in ['README.txt', '*.srt', 'edit*.json', 'performance-prompt-pl.txt']:
            add(f'physical-design/visualization/voiceover-v{rev}/{name}')
    for pattern in ['physical-design/visualization/seedance*/**/*.txt',
                    'physical-design/visualization/seedance*/**/*.json']:
        add(pattern)
    for name in ['nftables.conf', 'dnsmasq-lan.conf', 'pi-router.conf',
                 'pi-router-nftables-override.conf', 'pi-lan-dnsmasq.service',
                 '90-pi-router-forwarding.conf', '99-usb-admin-only.conf',
                 '90-pi-lan-carrier.conf', '78-mm-pitalk-uart.rules', 'ppp-options.ttyS0']:
        add('config/' + name)
    files.pop('physical-design/exports/SafeWall-B-detailed-visual-v02.f3d', None)
    files.pop('marketing/outro/poster-portrait.png', None)
    files['tests/test-router-isolated.py'] = ROOT / 'scripts/test-router-isolated.py'
    files['docs/SafeWall-draft.pdf'] = ROOT / 'projekt/Draft-projektu.pdf'
    return files


def public_content(relative, source, selected):
    raw = source.read_bytes()
    if source.suffix in {'.md', '.txt', '.json'}:
        value = raw.decode('utf-8')
        value = value.replace(str(ROOT) + '/', '').replace(str(ROOT), '.')
        if relative == 'AGENTS.md':
            value = re.sub(r'^@[^\n]+RTK\.md\n*', '', value)
        if relative == 'marketing/cover/manifest-v1.json':
            data = json.loads(value)
            data['source_image'] = 'safewall-cover-4x3-v1.png'
            data['original_generation_path'] = 'Retained in local archive; not needed to use this asset.'
            value = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
        if source.suffix == '.md':
            def link(match):
                label, target = match.group(1), match.group(2)
                if re.match(r'[a-zA-Z][\w+.-]*:', target) or target.startswith('#'):
                    return match.group(0)
                path = unquote(target.split('#', 1)[0].split('?', 1)[0])
                if not path:
                    return match.group(0)
                candidate = (source.parent / path).resolve()
                try:
                    rel = candidate.relative_to(ROOT).as_posix()
                except ValueError:
                    return f'{label} (plik lokalny: `{path}`)'
                if rel in selected or any(p.startswith(rel.rstrip('/') + '/') for p in selected):
                    return match.group(0)
                return f'{label} (plik lokalny: `{path}`)'
            value = re.sub(r'(?<!!)\[([^\]\n]+)\]\(([^\s)]+)\)', link, value)
        raw = value.encode('utf-8')
    if relative == 'config/dnsmasq-lan.conf':
        raw = raw.replace(b',piotr4mmc-raspberrypi,', b',safewall,')
    if relative == 'mock-check-tor/site/index.html':
        raw = re.sub(rb'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])', b'198.51.100.24', raw)
    # Remove export-only whitespace noise; preserve the local vendor originals.
    if relative in {'mock-check-tor/site/index.html', 'marketing/captions/.gitignore',
                    'projekt/prezentacja/reference/tor-logo-white.svg',
                    'references/ookla-speedtest-1.2.0.md'} or source.suffix in {'.step', '.mtl'}:
        raw = b'\n'.join(line.rstrip(b' \t\r') for line in raw.splitlines()).rstrip(b'\n') + b'\n'
    return raw


def atomic_write(target, data, source=None):
    """Keep an existing file intact if disk space runs out during the export."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.export-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        if source:
            shutil.copymode(source, temporary)
        else:
            temporary.chmod(0o644)
        temporary.replace(target)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    destination = args.destination.resolve()
    if destination == ROOT or ROOT in destination.parents or not (destination / '.git').exists():
        parser.error('Destination must be a separate, existing Git checkout.')
    selected = selection()
    payloads = {}
    for relative, source in sorted(selected.items()):
        if not source.is_file() or source.is_symlink():
            raise RuntimeError(f'Missing or symlinked source: {relative}')
        if source.stat().st_size > 25_000_000:
            raise RuntimeError(f'File too large for this publication: {relative}')
        data = public_content(relative, source, selected)
        if any(pattern.search(data) for pattern in SECRETS):
            raise RuntimeError(f'Potential secret in {relative}; content suppressed.')
        target = destination / relative
        if not target.resolve().is_relative_to(destination):
            raise RuntimeError(f'Destination symlink escapes checkout: {relative}')
        payloads[relative] = data
    report = {
        'scope': 'Curated public sources and selected assets; no raw logs, credentials or video.',
        'files': [{'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                  for name, data in payloads.items()],
    }
    changed = sum(not (destination / p).is_file() or (destination / p).read_bytes() != data
                  for p, data in payloads.items())
    size = sum(map(len, payloads.values()))
    print(f'{len(payloads)} files, {size / 1e6:.2f} MB, {changed} changed; write={args.write}')
    if not args.write:
        return
    for relative, data in payloads.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_bytes() != data:
            atomic_write(target, data, selected[relative])
    manifest = destination / 'docs/publication-manifest.json'
    atomic_write(manifest, (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    print(f'Exported to {destination}; no files deleted, no Git operations performed.')


if __name__ == '__main__':
    main()
