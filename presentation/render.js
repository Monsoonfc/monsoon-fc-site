const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium',
    args: ['--no-sandbox', '--force-color-profile=srgb', '--font-render-hinting=none'],
  });
  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 2, // -> 3840x2160 output
  });
  const file = 'file://' + path.resolve(__dirname, 'youpro-slide.html');
  await page.goto(file, { waitUntil: 'networkidle' });
  // ensure web fonts are fully loaded before capture
  await page.evaluate(async () => { await document.fonts.ready; });
  await page.waitForTimeout(400);
  const el = await page.$('.stage');
  await el.screenshot({ path: path.resolve(__dirname, 'youpro-slide.png') });
  await browser.close();
  console.log('done');
})().catch(e => { console.error(e); process.exit(1); });
