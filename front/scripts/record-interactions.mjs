import { mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { chromium, firefox, webkit } from "playwright";

const browserName = process.env.BROWSER ?? "chromium";
const url = process.env.URL ?? "http://localhost:3000";
const outputDir = resolve(process.env.OUTPUT_DIR ?? "artifacts/interaction-recording");
const storageState = process.env.STORAGE_STATE ?? ".auth/storage-state.json";
const maxTargets = Number.parseInt(process.env.MAX_TARGETS ?? "30", 10);
const browserTypes = { chromium, firefox, webkit };
const browserType = browserTypes[browserName];

if (!browserType) {
  throw new Error(`Unsupported BROWSER "${browserName}". Use chromium, firefox, or webkit.`);
}

await mkdir(outputDir, { recursive: true });

const browser = await browserType.launch({ headless: true }).catch((error) => {
  console.error(
    `Unable to launch ${browserName}. Install its Playwright browser with ` +
      `npx playwright install ${browserName}.`,
  );
  throw error;
});

const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  recordVideo: { dir: outputDir, size: { width: 1440, height: 900 } },
  ...(exists(storageState) ? { storageState } : {}),
});
const page = await context.newPage();

await page.addInitScript(() => {
  window.addEventListener("DOMContentLoaded", () => {
    const cursor = document.createElement("div");
    cursor.id = "__interaction-recording-cursor";
    cursor.style.cssText = [
      "position:fixed",
      "z-index:2147483647",
      "width:16px",
      "height:16px",
      "border:2px solid #ffffff",
      "border-radius:50%",
      "background:#d86645",
      "box-shadow:0 0 0 2px rgba(0,0,0,.55),0 2px 8px rgba(0,0,0,.35)",
      "pointer-events:none",
      "transform:translate(-50%,-50%)",
      "transition:left .18s ease,top .18s ease,transform .18s ease",
    ].join(";");
    document.body.append(cursor);
  });
});

await page.goto(url, { waitUntil: "networkidle", timeout: 60_000 });
await page.waitForTimeout(500);

const targets = await page.locator(
  "a, button, [role='button'], input, select, textarea, summary",
).evaluateAll((elements, limit) => elements
  .map((element, index) => ({ element, index }))
  .filter(({ element }) => {
    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);
    return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
  })
  .slice(0, limit)
  .map(({ element, index }) => ({
    index,
    tag: element.tagName.toLowerCase(),
    text: (element.textContent || element.getAttribute("aria-label") || element.getAttribute("placeholder") || "")
      .trim()
      .replace(/\s+/g, " ")
      .slice(0, 80),
  })), maxTargets);

await page.screenshot({ path: resolve(outputDir, "initial.png"), fullPage: false });

for (const target of targets) {
  const locator = page.locator(
    "a, button, [role='button'], input, select, textarea, summary",
  ).nth(target.index);
  if (!(await locator.isVisible().catch(() => false))) continue;

  const box = await locator.boundingBox();
  if (!box) continue;

  const label = `${String(target.index).padStart(2, "0")}-${target.tag}-${slugify(target.text || "untitled")}`;
  await page.evaluate(({ x, y }) => {
    const cursor = document.getElementById("__interaction-recording-cursor");
    if (cursor) {
      cursor.style.left = `${x}px`;
      cursor.style.top = `${y}px`;
      cursor.style.transform = "translate(-50%,-50%) scale(1.2)";
    }
  }, { x: box.x + box.width / 2, y: box.y + box.height / 2 });
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.waitForTimeout(350);
  await page.screenshot({ path: resolve(outputDir, `${label}-hover.png`), fullPage: false });
  await page.waitForTimeout(300);
  await page.evaluate(() => {
    const cursor = document.getElementById("__interaction-recording-cursor");
    if (cursor) cursor.style.transform = "translate(-50%,-50%) scale(1)";
  });
}

await page.waitForTimeout(500);
await context.close();
await browser.close();

console.table(targets);
console.log(`Recorded ${targets.length} interactive targets to ${outputDir}`);

function slugify(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40) || "untitled";
}

function exists(path) {
  return existsSync(path);
}
