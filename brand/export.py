"""Raster/ICO derivatives of the SVG master. Requires Pillow; run via build.mjs."""
from pathlib import Path
from PIL import Image
import json
import shutil

ROOT = Path(__file__).resolve().parent
SIZES = (16, 24, 32, 48, 64, 128, 180, 192, 256, 512, 1024, 2048)
for theme in ('transparent', 'dark', 'black', 'light'):
    destination = ROOT / 'png' / theme
    destination.mkdir(parents=True, exist_ok=True)
    with Image.open(ROOT / '.render' / f'{theme}.png') as source:
        for size in SIZES:
            source.resize((size, size), Image.Resampling.LANCZOS).save(destination / f'safewall-{size}.png', optimize=True)

(ROOT / 'png' / 'logo').mkdir(parents=True, exist_ok=True)
for name, suffix in (('logo', ''), ('white', '-white'), ('ink', '-ink')):
    with Image.open(ROOT / '.render' / f'{name}.png') as source:
        for width in (256, 512, 1024, 2048):
            size = (width, round(width * 442 / 856))
            source.resize(size, Image.Resampling.LANCZOS).save(ROOT / 'png' / 'logo' / f'safewall-logo{suffix}-{width}.png', optimize=True)

with Image.open(ROOT / '.render' / 'transparent.png') as source:
    source.save(ROOT / 'icons' / 'favicon.ico', format='ICO', sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
for size in (16, 32):
    shutil.copy2(ROOT / 'png' / 'transparent' / f'safewall-{size}.png', ROOT / 'icons' / f'favicon-{size}.png')
shutil.copy2(ROOT / 'png' / 'dark' / 'safewall-180.png', ROOT / 'icons' / 'apple-touch-icon.png')
for size in (192, 512):
    shutil.copy2(ROOT / 'png' / 'transparent' / f'safewall-{size}.png', ROOT / 'icons' / f'icon-{size}.png')
with Image.open(ROOT / '.render' / 'maskable.png') as source:
    source.resize((512, 512), Image.Resampling.LANCZOS).save(ROOT / 'icons' / 'maskable-icon-512.png', optimize=True)

metadata = {
    'name': 'SafeWall', 'selectedConcept': '4A',
    'master': 'svg/safewall-logo.svg',
    'reference': 'reference/4A.png',
    'colors': {'body': '#7D67E9', 'crown': '#B39AFB'},
    'viewBox': [0, 0, 856, 442],
    'geometry': 'Reconstructed from the PNG alpha contour using straight segments and circular arcs; two solid vector paths, no embedded bitmap.',
    'iconSizes': list(SIZES),
    'backgrounds': {'transparent': None, 'dark': '#17171C', 'black': '#000000', 'light': '#FFFFFF'},
    'usage': {
        'dashboardHeader': 'svg/safewall-logo.svg',
        'browserTab': 'icons/favicon.svg',
        'legacyBrowserTab': 'icons/favicon.ico',
        'appleHomeScreen': 'icons/apple-touch-icon.png',
        'maskableAppIcon': 'icons/maskable-icon-512.png',
        'monochromeOnDark': 'svg/safewall-logo-white.svg',
        'monochromeOnLight': 'svg/safewall-logo-ink.svg',
    },
}
(ROOT / 'manifest.json').write_text(json.dumps(metadata, indent=2) + '\n')
with Image.open(ROOT / 'reference' / '4A.png') as reference:
    source_mask = reference.getchannel('A').point(lambda a: 255 if a >= 128 else 0)
    bounds = source_mask.getbbox()
    source_mask = source_mask.crop(bounds)
with Image.open(ROOT / '.render' / 'trace.png') as traced:
    vector_mask = traced.getchannel('A').point(lambda a: 255 if a >= 128 else 0)
if source_mask.size == vector_mask.size:
    pairs = list(zip(source_mask.tobytes(), vector_mask.tobytes()))
    intersection = sum(bool(a and b) for a, b in pairs)
    union = sum(bool(a or b) for a, b in pairs)
    report = {'referenceBounds': bounds, 'vectorSize': vector_mask.size,
              'silhouetteIoU': intersection / union,
              'rasterDifferencePixels': sum(a != b for a, b in pairs)}
    (ROOT / 'trace-report.json').write_text(json.dumps(report, indent=2) + '\n')
print('Brand assets built: vector, four PNG backgrounds, monochrome logos, ICO and app icons.')
