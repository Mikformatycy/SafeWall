const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const dir = path.join(__dirname, 'reference');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  await page.goto('https://rainbowkit.com', { waitUntil: 'networkidle', timeout: 60000 });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(dir, 'rainbowkit-full.png'), fullPage: true });
  await page.screenshot({ path: path.join(dir, 'rainbowkit-hero.png') });
  const styles = await page.evaluate(() => ({
    url: location.href,
    title: document.title,
    viewport: { width: innerWidth, height: innerHeight },
    headings: [...document.querySelectorAll('h1,h2,h3')].map(e => {
      const s = getComputedStyle(e);
      return { text: e.innerText, font: s.fontFamily, size: s.fontSize, weight: s.fontWeight, color: s.color, lineHeight: s.lineHeight, letterSpacing: s.letterSpacing };
    }),
    body: {font: getComputedStyle(document.body).fontFamily, background: getComputedStyle(document.body).background},
    fonts: [...document.fonts].map(f => ({ family: f.family, weight: f.weight, status: f.status })),
    fontUrls: performance.getEntriesByType('resource').map(e => e.name).filter(u => /woff|ttf|otf/.test(u)),
    css: [...document.styleSheets].flatMap(s => {try{return [...s.cssRules].filter(r => r.cssText.startsWith('@font-face')).map(r => r.cssText)}catch{return []}})
  }));
  fs.writeFileSync(path.join(dir, 'rainbowkit-style.json'), JSON.stringify(styles, null, 2));
  await page.getByRole('heading', { name: 'Rainbow 🤝 Developers' }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(dir, 'rainbowkit-features.png') });
  console.log(JSON.stringify(styles, null, 2));
  await browser.close();
})().catch(e => {console.error(e); process.exit(1)});
