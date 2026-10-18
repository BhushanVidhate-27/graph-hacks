import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import { webkit, firefox } from "playwright";
import fs from "node:fs";
import pixelmatch from "pixelmatch";
import { PNG } from "pngjs";

const browserName = process.env.BROWSER ?? "webkit";
const actualUrl = process.env.ACTUAL_URL ?? "https://heronaiapp.com";
const currentUrl = process.env.CURRENT_URL ?? "http://localhost:3100";
const outputDir = resolve("artifacts/scroll-audit");
const engine = browserName === "firefox" ? firefox : webkit;

await mkdir(outputDir, { recursive: true });

const browser = await engine.launch({ headless: true }).catch((error) => {
  console.error(
    `Unable to launch ${browserName}. Install its Playwright browser with ` +
      `npx playwright install ${browserName}.`,
  );
  throw error;
});

const checkpoints = [0, 0.25, 0.5, 0.75, 1];
const results = [];
const diffResults = [];

for (const [name, url] of [
  ["actual", actualUrl],
  ["current", currentUrl],
]) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(url, { waitUntil: "networkidle", timeout: 60_000 });
  await page.evaluate(async () => {
    await Promise.race([
      Promise.all([
        document.fonts.ready,
        ...[...document.images].map(
          (image) =>
            image.complete ||
            new Promise((resolve) => {
              image.addEventListener("load", resolve, { once: true });
              image.addEventListener("error", resolve, { once: true });
            }),
        ),
      ]),
      new Promise((resolve) => window.setTimeout(resolve, 5_000)),
    ]);
  });
  await page.waitForTimeout(name === "actual" ? 5_000 : 1_000);
  const metrics = await page.evaluate(() => ({
    url: location.href,
    title: document.title,
    scrollHeight: document.documentElement.scrollHeight,
    viewportHeight: window.innerHeight,
  }));

  for (const checkpoint of checkpoints) {
    await page.evaluate((fraction) => {
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      window.scrollTo({ top: maxScroll * fraction, behavior: "auto" });
    }, checkpoint);
    await page.waitForTimeout(350);
    await page.screenshot({
      path: resolve(outputDir, `${browserName}-${name}-${checkpoint * 100}.png`),
      fullPage: false,
    });
  }

  results.push({ name, ...metrics });
  await page.close();
}

for (const checkpoint of checkpoints) {
  const actualPath = resolve(outputDir, `${browserName}-actual-${checkpoint * 100}.png`);
  const currentPath = resolve(outputDir, `${browserName}-current-${checkpoint * 100}.png`);
  const actual = PNG.sync.read(fs.readFileSync(actualPath));
  const current = PNG.sync.read(fs.readFileSync(currentPath));
  const width = Math.min(actual.width, current.width);
  const height = Math.min(actual.height, current.height);
  const actualCrop = actual.width === width && actual.height === height
    ? actual
    : crop(actual, width, height);
  const currentCrop = current.width === width && current.height === height
    ? current
    : crop(current, width, height);
  const diff = new PNG({ width, height });
  const mismatchedPixels = pixelmatch(
    actualCrop.data,
    currentCrop.data,
    diff.data,
    width,
    height,
    { threshold: 0.1 },
  );
  const diffPath = resolve(outputDir, `${browserName}-diff-${checkpoint * 100}.png`);
  fs.writeFileSync(diffPath, PNG.sync.write(diff));
  diffResults.push({
    checkpoint: `${checkpoint * 100}%`,
    mismatchedPixels,
    mismatchPercent: `${((mismatchedPixels / (width * height)) * 100).toFixed(2)}%`,
    diffPath,
  });
}

console.table(results);
console.table(diffResults);
console.log(`Screenshots written to ${outputDir}`);
await browser.close();

function crop(image, width, height) {
  const output = new PNG({ width, height });
  PNG.bitblt(image, output, 0, 0, width, height, 0, 0);
  return output;
}
