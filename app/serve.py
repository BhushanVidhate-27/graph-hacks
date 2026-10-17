"""
app/serve.py — production entrypoint. Bhushan owns this file; app/main.py is Soham's
and is imported unmodified.

Two jobs, one process:

1. Serve the API from app.main (POST /ask, GET /health) unchanged.
2. Serve the frontend from web/ on the SAME origin.

Why same-origin matters, twice:
  - It removes CORS entirely. The API's allow_origins only lists
    http://localhost:5173, so opening the page via 127.0.0.1 fails with a bare
    "Failed to fetch" and no hint it is an origin mismatch. Same-origin makes that
    class of bug impossible in production.
  - No reverse proxy sits between the browser and the stream, so nothing buffers
    the SSE response. A proxy that buffers turns a working local stream into a
    dead production one.

The StaticFiles mount is registered LAST so it cannot shadow the API routes:
Starlette matches routes in registration order, and /ask and /health are already
registered by app.main.
"""

from app.main import app
from fastapi.staticfiles import StaticFiles

# /health must answer even if a static mount fails, so mount failures stay
# contained.
#
# mock/ is mounted SEPARATELY and at the root. The frontend loads its fixture at
# "../mock/trail.json", which resolves to /mock/trail.json — not under /web/.
# Mounting only web/ made that a silent 404 with a blank trail, which reads as a
# broken renderer rather than a missing mount. It is mounted before "/" because
# StaticFiles matches in registration order and the catch-all would swallow it.
app.mount("/mock", StaticFiles(directory="mock"), name="mock")
app.mount("/", StaticFiles(directory="web", html=True), name="web")
