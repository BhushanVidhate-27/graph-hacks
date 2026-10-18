import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { SiteRuntime } from "@/components/site-runtime";

const SITE = "heronaiapp.com-e0b5c319/root-8a5edab2";

/**
 * Serves the cloned page as-is.
 *
 * The markup is injected verbatim. It used to be mutated here:
 *
 *   body.replace('<div class="loading">', '<div class="loading active">')
 *
 * which is what triggered a React hydration mismatch on every load. The server
 * emitted "loading active"; the client compared that against the unmodified
 * string and reported the two as different trees — React shows the whole
 * injected HTML in the diff, so the console was full of a wall of markup for a
 * one-word difference.
 *
 * Dropping the mutation fixes it at the source: server and client now emit
 * byte-identical HTML, so there is nothing to disagree about. Nothing is lost
 * visually either — LoadingController adds the `active` class in its mount
 * effect, which is strictly better than shipping it pre-set, because the
 * loader then genuinely begins on the client rather than flashing on and off
 * during hydration.
 */
export default async function Home() {
  const body = await readFile(
    join(process.cwd(), `public/sites/${SITE}/heron-body.html`),
    "utf8",
  );

  return (
    <>
      {/* eslint-disable @next/next/no-css-tags --
        Load order IS the mechanism. Both sheets are unlayered, so the later one
        wins on source order: the captured sheet styles the cloned page, and
        helio.css styles the Helio components that sit on top of it. Moving
        either into a static import changes that ordering. See helio.css. */}
      <link rel="stylesheet" href={`/sites/${SITE}/heron.css`} />
      <link rel="stylesheet" href="/helio.css" />
      {/* eslint-enable @next/next/no-css-tags */}
      <div dangerouslySetInnerHTML={{ __html: body }} />
      <SiteRuntime />
    </>
  );
}