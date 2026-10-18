import type { NextConfig } from "next";

/**
 * Static export.
 *
 * The site is three prerendered pages (`/`, `/demo`, 404). Nothing renders per
 * request: the captured landing page is a static HTML file, and `/demo` fetches
 * the agent from the browser via `NEXT_PUBLIC_HELIO_API` (see `src/lib/api.ts`,
 * which is `"use client"`), so there is no server to run.
 *
 * This replaced `output: "standalone"`, which deployed as a Web Service we did
 * not need — and which could not coexist with a static export anyway.
 *
 * `images: { unoptimized }` is required: the default image optimizer needs a
 * Node server, and every image here is a plain local `<img>` in a captured file.
 */
const nextConfig: NextConfig = {
  output: "export",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;