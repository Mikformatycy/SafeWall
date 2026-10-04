// Same transparent Chrome -> PNG technique as PlatinumCode's first film.
const puppeteer = require('puppeteer-core');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  const [eventsPath, stylePath, output, widthArg, heightArg] = process.argv.slice(2);
  const width = Number(widthArg), height = Number(heightArg);
  const style = JSON.parse(fs.readFileSync(stylePath, 'utf8'));
  const events = JSON.parse(fs.readFileSync(eventsPath, 'utf8')).events;
  const scale = height / 540;
  const stripHeight = Math.ceil(160 * scale);
  fs.mkdirSync(output, {recursive: true});
  const browser = await puppeteer.launch({
    executablePath: process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true,
    args: ['--force-device-scale-factor=1', '--hide-scrollbars'],
  });
  try {
    const page = await browser.newPage();
    await page.setViewport({width, height: stripHeight, deviceScaleFactor: 1});
    await page.goto(pathToFileURL(path.join(__dirname, 'caption.html')).href);
    await page.evaluate(({width, stripHeight, scale, style}) => {
      const cap = document.getElementById('cap'), line = document.getElementById('line');
      cap.style.width = `${width}px`;
      cap.style.height = `${stripHeight}px`;
      cap.style.paddingBottom = `${style.bottom_margin_at_540p * scale}px`;
      line.style.fontFamily = style.font_family;
      line.style.fontWeight = style.font_weight;
      line.style.fontSize = `${style.font_size_at_540p * scale}px`;
      line.style.letterSpacing = `${style.letter_spacing_em}em`;
      line.style.color = style.text_color;
      line.style.webkitTextStroke = `${style.stroke_width_at_540p * scale}px ${style.stroke_color}`;
      const css = document.createElement('style');
      css.textContent = `#line .hl { color: ${style.highlight_color}; }`;
      document.head.appendChild(css);
    }, {width, stripHeight, scale, style});
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({path: path.join(output, 'blank.png'), omitBackground: true});
    const bounds = [];
    for (let i = 0; i < events.length; i++) {
      const ev = events[i];
      const box = await page.evaluate(({html, size, maxWidth}) => {
        const line = document.getElementById('line');
        line.innerHTML = html;
        line.style.fontSize = `${size}px`;
        const natural = line.getBoundingClientRect().width;
        if (natural > maxWidth) line.style.fontSize = `${size * maxWidth / natural}px`;
        const r = line.getBoundingClientRect();
        return {x: r.x, y: r.y, width: r.width, height: r.height, fontSize: getComputedStyle(line).fontSize};
      }, {html: ev.html, size: style.font_size_at_540p * scale,
          maxWidth: width * style.maximum_width_fraction});
      if (box.x < 0 || box.y < 0 || box.x + box.width > width || box.y + box.height > stripHeight)
        throw new Error(`Caption ${i} falls outside the strip`);
      bounds.push({event: i, ...box});
      await page.screenshot({path: path.join(output, `cap_${String(i).padStart(3, '0')}.png`), omitBackground: true});
    }
    fs.writeFileSync(path.join(output, 'layout.json'), JSON.stringify({width, height, stripHeight, bounds}, null, 2));
    console.log(`CAPTION_PNGS_READY ${events.length} events, ${width}x${stripHeight}`);
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error.message); process.exitCode = 1;});
