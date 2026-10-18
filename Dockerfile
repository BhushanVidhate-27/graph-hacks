# Helio company brain — production image.
# Bhushan owns deploy/. app/main.py (Soham) and front/ are copied unmodified.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

# --------------------------------------------------------------------------- #
# Stage 1: build the marketing site.
#
# front/ is a Next.js app in static-export mode (next.config.ts sets
# output: "export"), so `next build` emits plain files into front/out/ and needs
# no Node runtime afterwards. Building here and copying the result into the
# Python stage keeps the served site and the served API on ONE origin, which is
# the whole point — see the CMD note below.
#
# NEXT_PUBLIC_HELIO_API is deliberately EMPTY, and it must be set here to be
# empty — omitting it entirely leaves src/lib/api.ts to fall back to its own
# default of "https://helio-brain.onrender.com", which bakes an absolute URL
# into the bundle. Empty string is not nullish, so it wins over that default and
# the browser calls "/ask" relative to the page. Same-origin means CORS never
# applies and no proxy sits between the page and the SSE stream. Do NOT set it to
# the public API URL here — that reintroduces a cross-origin request from a page
# served by that very same host.
# same host.
FROM node:24.14.1-slim AS site

# Set to empty ON PURPOSE — see the note above.
ENV NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_HELIO_API=""

WORKDIR /site

# Lockfile first so a source-only edit does not re-run npm ci.
COPY front/package.json front/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY front/ ./

# `prepare: husky` runs on npm ci above. It is a no-op without a .git (the
# context has none), so no --ignore-scripts is needed here.
RUN npm run build

# --------------------------------------------------------------------------- #
# Stage 2: the runtime image.
FROM python:3.12-slim

# deps first so code edits do not invalidate the pip layer
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY mock/ ./mock/
COPY data/ ./data/
# scripts/ is needed at runtime: the compose `seed` service runs generate.py and
# load.py inside this image to populate the graph. Omitting it made seed exit 2
# with "can't open file '/srv/scripts/generate.py'".
COPY scripts/ ./scripts/

# The exported site, mounted at / by app.serve. Copies `out/` only — the source
# and node_modules stay in the builder stage.
COPY --from=site /site/out ./site/

EXPOSE 8080

# app.serve mounts the frontend on the SAME origin as the API. Two consequences:
#   - CORS disappears. The API's allow_origins lists only localhost:5173, so a
#     cross-origin production page fails with a bare "Failed to fetch".
#   - Nothing sits in front of the SSE stream to buffer it. A buffering proxy
#     turns a stream that works locally into one that silently dies in production.
#
# --timeout-keep-alive is long because a streamed answer holds the connection open.
CMD ["uvicorn", "app.serve:app", "--host", "0.0.0.0", "--port", "8080", \
     "--timeout-keep-alive", "120", "--no-access-log"]
