import { mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { chromium } from "playwright";

const loginUrl = process.env.LOGIN_URL;
const storageStatePath = resolve(
  process.env.STORAGE_STATE ?? ".auth/storage-state.json",
);
const email = process.env.LOGIN_EMAIL;
const password = process.env.LOGIN_PASSWORD;
const emailSelector = process.env.LOGIN_EMAIL_SELECTOR ?? 'input[type="email"]';
const passwordSelector = process.env.LOGIN_PASSWORD_SELECTOR ?? 'input[type="password"]';
const submitSelector = process.env.LOGIN_SUBMIT_SELECTOR ?? 'button[type="submit"]';
const successSelector = process.env.LOGIN_SUCCESS_SELECTOR;

if (!loginUrl) {
  throw new Error(
    "LOGIN_URL is required. Example: LOGIN_URL=https://example.com/login npm run playwright:auth",
  );
}

await mkdir(resolve(storageStatePath, ".."), { recursive: true });

const browser = await chromium.launch({ headless: false });
const context = await browser.newContext();
const page = await context.newPage();

await page.goto(loginUrl, { waitUntil: "domcontentloaded", timeout: 60_000 });

if (email && password) {
  await page.locator(emailSelector).fill(email);
  await page.locator(passwordSelector).fill(password);
  await page.locator(submitSelector).click();
  await page.waitForLoadState("networkidle").catch(() => {});
} else {
  console.log("Complete login in the opened browser window.");
  console.log("Then press Enter here to save the authenticated session.");
  await waitForEnter();
}

if (successSelector) {
  await page.locator(successSelector).waitFor({ state: "visible", timeout: 30_000 });
}

await context.storageState({ path: storageStatePath });
console.log(`Saved Playwright auth state to ${storageStatePath}`);

await browser.close();

function waitForEnter() {
  return new Promise((resolvePromise) => {
    process.stdin.setEncoding("utf8");
    process.stdin.resume();
    process.stdin.once("data", resolvePromise);
  });
}
