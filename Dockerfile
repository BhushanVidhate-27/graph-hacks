# Helio company brain — production image.
# Bhushan owns deploy/. app/main.py (Soham) and web/ (Ujwal) are copied unmodified.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

# deps first so code edits do not invalidate the pip layer
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY web/ ./web/
COPY mock/ ./mock/
COPY data/ ./data/
# scripts/ is needed at runtime: the compose `seed` service runs generate.py and
# load.py inside this image to populate the graph. Omitting it made seed exit 2
# with "can't open file '/srv/scripts/generate.py'".
COPY scripts/ ./scripts/

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
