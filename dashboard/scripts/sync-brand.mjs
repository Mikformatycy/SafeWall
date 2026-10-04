import { copyFile, mkdir } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const brand = fileURLToPath(new URL('../../brand/', import.meta.url));
const dist = fileURLToPath(new URL('../dist/', import.meta.url));
const files = {
  'svg/safewall-logo.svg': 'assets/brand/safewall-logo.svg',
  'svg/safewall-mask.svg': 'assets/brand/safewall-mask.svg',
  'icons/favicon-32.png': 'assets/brand/favicon-32.png',
  'icons/favicon.svg': 'favicon.svg',
  'icons/favicon.ico': 'favicon.ico',
  'icons/apple-touch-icon.png': 'apple-touch-icon.png',
};

export async function syncBrand() {
  for (const [source, target] of Object.entries(files)) {
    const destination = resolve(dist, target);
    await mkdir(dirname(destination), { recursive: true });
    await copyFile(resolve(brand, source), destination);
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) await syncBrand();
