"""
app/serve.py — production entrypoint. Bhushan owns this file; app/main.py is Soham's
and is imported unmodified.

Two jobs, one process:

1. Serve the API from app.main (POST /ask, GET /health) unchanged.
2. Serve the frontend from site/ on the SAME origin.

Why same-origin matters, twice:
  - It removes CORS entirely. The API's allow_origins only lists
    http://localhost:5173, so opening the page via 127.0.0.1 fails with a bare
    "Failed to fetch" and no hint it is an origin mismatch. Same-origin makes that
    class of bug impossible in production.
  - No reverse proxy sits between the browser and the stream, so nothing buffers
    the SSE response. A proxy that buffers turns a working local stream into a
    dead production one.

`site/` is the static export of front/ (Next.js, `output: "export"`), produced by
the `site` stage of the Dockerfile. It is plain HTML/CSS/JS with no Node runtime
behind it, so this process is still the only thing that has to stay alive.

The StaticFiles mount is registered LAST so it cannot shadow the API routes:
Starlette matches routes in registration order, and /ask and /health are already
registered by app.main.
"""

import os
import stat
from pathlib import Path

import anyio.to_thread
from app.main import app
from fastapi.staticfiles import StaticFiles

# Overridable so a local `npm run build` in front/ can be served without
# rebuilding the image.
SITE_DIR = Path(os.getenv("HELIO_SITE_DIR", "site"))


class SiteFiles(StaticFiles):
    """
    StaticFiles that understands a Next.js static export's layout.

    `next build` with output: "export" writes each route as BOTH `<route>.html`
    and a `<route>/` directory of client-navigation segment files. For /demo that
    means `demo.html` next to `demo/__next.demo.__PAGE__.txt`.

    Plain StaticFiles(html=True) cannot serve that. Asked for /demo it stats the
    path, finds the `demo` DIRECTORY, looks for `demo/index.html`, does not find
    it, and 404s — even though demo.html is sitting right there. The symptom is a
    styled landing page whose own nav link to /demo is a dead end.

    get_response is overridden rather than the route table because the set of
    exported routes is decided at build time. Listing them here would mean every
    new page needs a matching line in the backend, and a forgotten line fails
    silently as a 404 rather than as a build error.

    Two rules, in order:
      1. If the path does not resolve to a file, try `<path>.html`. This is what
         rescues /demo.
      2. Otherwise defer to StaticFiles, which already serves 404.html with a 404
         status when html=True.

    Only the fallback is added. Everything that already worked — /, /favicon.ico,
    /_next/*, /images/*, /demo/*.txt — is served by the original lookup, so this
    cannot change the behaviour of an existing URL.
    """

    async def get_response(self, path: str, scope):
        _, stat_result = await anyio.to_thread.run_sync(self.lookup_path, path)

        # Rule 1: not a regular file on disk. Try the sibling `<path>.html`.
        if not (stat_result and stat.S_ISREG(stat_result.st_mode)):
            html_full, html_stat = await anyio.to_thread.run_sync(
                self.lookup_path, f"{path}.html"
            )
            if html_stat and stat.S_ISREG(html_stat.st_mode):
                return self.file_response(html_full, html_stat, scope)

        # Rule 2: hand back to StaticFiles. If 404, fall back to index.html for SPA routing.
        response = await super().get_response(path, scope)
        if response.status_code == 404:
            index_full, index_stat = await anyio.to_thread.run_sync(
                self.lookup_path, "index.html"
            )
            if index_stat and stat.S_ISREG(index_stat.st_mode):
                return self.file_response(index_full, index_stat, scope)
        return response


# mock/ is mounted SEPARATELY and at the root. The frontend loads its fixture at
# "../mock/trail.json", which resolves to /mock/trail.json — not under /site/.
# Mounting only site/ made that a silent 404 with a blank trail, which reads as a
# broken renderer rather than a missing mount. It is mounted before "/" because
# StaticFiles matches in registration order and the catch-all would swallow it.
app.mount("/mock", StaticFiles(directory="mock"), name="mock")

app.mount("/", SiteFiles(directory=SITE_DIR, html=True), name="site")