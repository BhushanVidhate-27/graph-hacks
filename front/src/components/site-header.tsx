import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { SiteRuntime } from "@/components/site-runtime";
import { HeaderOffset } from "@/components/header-offset";

const SITE = "heronaiapp.com-e0b5c319/root-8a5edab2";

/**
 * The site header, shared by every route.
 *
 * Sliced out of the captured HTML at request time rather than copied into a
 * second file. Duplicating 20KB of nav markup would guarantee the two drift
 * apart the first time a label changes — and the nav is the one thing every
 * page shares, so drift there is visible immediately.
 *
 * Loads both stylesheets, in order, because order is the whole mechanism here.
 * The captured sheet must stay unlayered (its markup uses class names Tailwind
 * also owns) and the Helio sheet must come after it (both unlayered, so source
 * order decides). See public/helio.css.
 */
export async function SiteHeader() {
  const body = await readFile(
    join(process.cwd(), `public/sites/${SITE}/heron-body.html`),
    "utf8",
  );

  const start = body.indexOf("<header-component");
  const endTag = "</header-component>";
  const end = body.indexOf(endTag, start);
  if (start < 0 || end < 0) return null;
  const header = body.slice(start, end + endTag.length);

  return (
    <>
      {/* eslint-disable @next/next/no-css-tags -- same reason as
          src/app/page.tsx: the captured sheet must load first and unlayered,
          and helio.css must load after it. Order is load-bearing. */}
      <link rel="stylesheet" href={`/sites/${SITE}/heron.css`} />
      <link rel="stylesheet" href="/helio.css" />
      {/* eslint-enable @next/next/no-css-tags */}
      <div dangerouslySetInnerHTML={{ __html: header }} />
      <HeaderOffset />
      <SiteRuntime />
    </>
  );
}