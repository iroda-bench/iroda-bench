// Renders the 1200 × 630 share images into ../dist. Run from the repository root:
// node site/og/render.js
const { chromium } = require("playwright");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

(async () => {
  const card = pathToFileURL(path.join(__dirname, "card.html")).href;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
  for (const lang of ["hu", "en"]) {
    await page.goto(`${card}?lang=${lang}`);
    await page.screenshot({ path: path.join(__dirname, "..", "dist", `og-${lang}.png`) });
  }
  await browser.close();
})();
