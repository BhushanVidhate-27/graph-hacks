# Setup — Graph Hacks · Company Brain

Everything the three of us need installed, with verification for each.
**Click any section to expand it.**

> All commands verified on macOS. Worked example: Python 3.14.2, Docker 29.9.1, FalkorDB `latest`.

---

## Index

| # | Tool | Needed by |
|---|---|---|
| 1 | [Homebrew](#) | Everyone |
| 2 | [Git + GitHub](#) | Everyone |
| 3 | [Docker Desktop](#) | Everyone |
| 4 | [FalkorDB](#) | Everyone |
| 5 | [FalkorDB Browser](#) | Everyone |
| 6 | [Python](#) | Everyone |
| 7 | [Virtual environment](#) | Everyone |
| 8 | [Python packages](#) | Everyone |
| 9 | [Anthropic API key](#) | Soham, Bhushan |
| 10 | [FalkorDB Cloud](#) | Ujwal → all |
| 11 | [Environment variables](#) | Everyone |
| 12 | [FastAPI + Uvicorn](#) | Soham |
| 13 | [SSE](#) | Soham, Ujwal |
| 14 | [Docker Compose](#) | Bhushan |
| 15 | [Fly.io](#) | Bhushan |
| 16 | [Vercel](#) | Bhushan (alternative) |
| 17 | [VS Code](#) | Everyone |
| 18 | [Node.js](#) | Optional |
| 19 | [MCP](#) | Optional |
| 20 | [Bulk loader](#) | Bhushan, optional |
| 21 | [Deadline timezone check](#) | Everyone |

---

<details>
<summary><b>1. Homebrew</b> — package manager · everyone</summary>

**Why:** everything else installs through it. If you have it, skip to 2.

**Check**
```bash
brew --version
```

**Install**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Add to your shell profile (Apple Silicon):
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

**Trouble:** if `brew: command not found` after install, restart your terminal.
</details>

<details>
<summary><b>2. Git + GitHub</b> — version control · everyone</summary>

**Why:** Rule 10 requires a **public** repository.

**Check**
```bash
git --version
gh --version        # GitHub CLI, optional but useful
```

**Install**
```bash
brew install git gh
```

**First-time setup**
```bash
git config --global user.name "Bhushan"
git config --global user.email "you@example.com"
gh auth login
```

**Create the shared repo — Bhushan**
```bash
cd ~/Life && gh repo create graph-hacks --public --clone
cd graph-hacks
gh repo add-collaborator soham -f Reader
gh repo add-collaborator ujwal -f Reader
```
</details>

<details>
<summary><b>3. Docker Desktop</b> — runs FalkorDB · everyone</summary>

**Why:** FalkorDB runs in Docker. Rule 4 allows Docker, self-hosted, or Cloud.

**Check**
```bash
docker --version
docker ps
```

**Install**
```bash
brew install --cask docker
open -a Docker          # IMPORTANT: launch it once and wait for the whale to stop
```

**Trouble — the two most common failures**

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot connect to the Docker daemon` | Desktop isn't running | `open -a Docker`, wait ~30s |
| `permission denied ... docker.sock` | Not in the docker group | Restart terminal; on macOS Desktop usually handles this |

**Alternative if you don't want Docker Desktop:** OrbStack or Colima (`brew install colima colima-docker` then `colima start`).
</details>

<details>
<summary><b>4. FalkorDB</b> — the graph database · everyone</summary>

**Why:** the mandatory technology. Rule 2 — must be the primary graph DB. Rule 3 — the graph must do real work, not decorate.

**Check**
```bash
docker ps | grep falkordb
```

**Install & run**
```bash
docker pull falkordb/falkordb:latest
docker run -d --name falkordb -p 6379:6379 falkordb/falkordb:latest
```

**Verify — should print `1`**
```bash
docker exec falkordb redis-cli GRAPH.QUERY g "RETURN 1 AS ok"
```

**Useful commands**
```bash
docker ps                                   # is it up?
docker logs falkordb                        # problems
docker restart falkordb                     # hung?
docker rm -f falkordb                       # reset, then re-run the run command
```

**Connect from Python**
```python
from falkordb import FalkorDB
db = FalkorDB(host="localhost", port=6379)
g  = db.select_graph("helio")
print(g.query("RETURN 1 AS ok").result_set)   # -> [[1]]
```

> ⚠️ **`.result_set` is required.** `g.query()` returns a `QueryResult` that is **not iterable**. `for row in g.query(...)` raises `TypeError`. This silently costs the first hour if nobody knows — mention it in your first group call.

**⚠️ Port conflict:** FalkorDB uses `6379`; its **Browser uses `3000`**. If Ujwal starts a JS dev server on 3000 they will collide — use `5173` or similar for the frontend.

**Clear the graph between generator runs** — never load twice into a dirty graph:
```bash
docker exec falkordb redis-cli GRAPH.LIST
docker exec falkordb redis-cli GRAPH.DELETE helio
```
</details>

<details>
<summary><b>5. FalkorDB Browser</b> — visual explorer · everyone</summary>

**Why:** this is the main dev loop — run Cypher, inspect the model, see connections, debug why a query returns nothing.

**Install:** nothing. It ships inside the container.

**Open**
```
http://localhost:3000
```

**Useful commands inside Browser**
```cypher
:reset                     // wipe the graph
MATCH (n) RETURN labels(n), count(*)
MATCH (n:Person) RETURN n.name LIMIT 10
```
</details>

<details>
<summary><b>6. Python</b> — the language · everyone</summary>

**Why:** one language end to end — generator, loader, graph layer, agent, API.

**Check**
```bash
python3 --version
```

**Install (3.11+ required)**
```bash
brew install python@3.12
```

**Point at it** if `python3 --version` still shows something older:
```bash
echo 'alias python3=python3.12' >> ~/.zprofile
```

**Alternative — pyenv, for multiple versions**
```bash
brew install pyenv
echo 'eval "$(pyenv init -)"' >> ~/.zprofile
pyenv install 3.12.7 && pyenv global 3.12.7
```

> **Verified working on 3.14.2.** Newer Pythons sometimes lack wheels for packages — if `pip install` fails to build, drop to 3.12 rather than debugging the build.
</details>

<details>
<summary><b>7. Virtual environment</b> — isolated deps · everyone</summary>

**Why:** keeps our packages out of system Python and off each other's toes.

**Create + activate**
```bash
cd ~/Life/graph-hacks
python3 -m venv .venv
source .venv/bin/activate
```
Windows: `.venv\Scripts\activate`

**Check** — prompt shows `(.venv)`
```bash
which python
```

**Deactivate:** `deactivate`

**Commit `.gitignore` first**
```gitignore
.venv/
.env
__pycache__/
*.pyc
.DS_Store
node_modules/
```
</details>

<details>
<summary><b>8. Python packages</b> — everyone, one command</summary>

**Install**
```bash
source .venv/bin/activate
pip install falkordb fastapi "uvicorn[standard]" anthropic pydantic faker python-dotenv httpx
```

| Package | Who | Why |
|---|---|---|
| `falkordb` | Bhushan, Soham | official driver (`falkordb-py`) — **not** old `ioredisgraph` |
| `fastapi` | Soham | the `/ask` endpoint |
| `uvicorn[standard]` | Soham | ASGI server + SSE streaming |
| `anthropic` | Soham | tool-use loop |
| `pydantic` | Soham | tool arg schemas for free |
| `faker` | Bhushan | synthetic people/services/docs |
| `python-dotenv` | Everyone | loads `.env` |
| `httpx` | Bhushan | calling the Anthropic API in the generator |

**Freeze them**
```bash
pip freeze > requirements.txt
```

**Optional extras**
```bash
pip install mcp                     # only if using the MCP route
pip install falkordb-bulk-loader    # faster CSV loads, if UNWIND feels slow
```

**Trouble:** `externally-managed-environment` on macOS → you skipped the venv. Go back to 7.
</details>

<details>
<summary><b>9. Anthropic API key</b> — the LLM · Soham, Bhushan</summary>

**Why:** the agent loop. Tool use is the product, so this needs a working tool-use model.

**Get a key**
1. Sign up at `console.anthropic.com`
2. **API Keys** → Create new key
3. Add credit under **Billing** — free tier won't cover a hackathon

**Add to `.env`**
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

**Verify**
```bash
source .venv/bin/activate
python -c "import anthropic; c=anthropic.Anthropic(); print(c.models.list().data[0].id)"
```

**Trouble**

| Symptom | Fix |
|---|---|
| `401` | key wrong or `.env` not loaded — restart uvicorn after editing `.env` |
| `credit balance is too low` | add billing credit |
| tool calls not firing | use a current model; confirm you pass `tools=` in the request |
</details>

<details>
<summary><b>10. FalkorDB Cloud</b> — hosted database · Ujwal creates, all use</summary>

**Why:** production deploy without babysitting a database. Rule 4 explicitly allows FalkorDB Cloud.

**Create:** sign up at `app.falkordb.cloud` → create an instance → copy credentials.

**Share with the team:** post host, username, password in the team chat.

```bash
FALKORDB_HOST=xxx.falkordb.cloud
FALKORDB_USERNAME=default
FALKORDB_PASSWORD=...
FALKORDB_GRAPH=helio
```

**Verify against Cloud** — if this fails locally, nothing will work in production:
```python
import os
from dotenv import load_dotenv
from falkordb import FalkorDB
load_dotenv()
db = FalkorDB(
    host=os.environ["FALKORDB_HOST"],
    username=os.environ["FALKORDB_USERNAME"],
    password=os.environ["FALKORDB_PASSWORD"],
)
g = db.select_graph("helio")
print(g.query("RETURN 1 AS ok").result_set)   # -> [[1]]
```

**Trouble:** cloud instances often need TLS on a non-default port — check the dashboard for the exact host and port, and whether your client needs `ssl=True`.
</details>

<details>
<summary><b>11. Environment variables</b> — everyone</summary>

**Why:** keeps API keys out of the repo. Never commit `.env`.

**Create**
```bash
cat > .env <<'EOF'
ANTHROPIC_API_KEY=sk-ant-...
FALKORDB_HOST=
FALKORDB_USERNAME=
FALKORDB_PASSWORD=
FALKORDB_GRAPH=helio
EOF

cp .env .env.example     # commit this one instead, keys left blank
```

**Load in Python**
```python
from dotenv import load_dotenv
load_dotenv()
```

**Confirm `.env` is ignored**
```bash
git check-ignore .env && echo "OK, ignored"
```
</details>

<details>
<summary><b>12. FastAPI + Uvicorn</b> — the backend · Soham</summary>

**Why:** serves `POST /ask` and streams the answer.

Already installed in step 8.

**Run**
```bash
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Check**
```bash
curl http://localhost:8000/health
```

**Browse the auto docs — free and very useful**
```
http://localhost:8000/docs
```

**Trouble**

| Symptom | Fix |
|---|---|
| `Address already in use` | another process on 8000 — `--port 8001`, or kill it |
| Changes not appearing | ensure `uvicorn`, not `python`, is the entry point so `--reload` works |
</details>

<details>
<summary><b>13. SSE</b> — streaming · Soham, Ujwal</summary>

**Why:** the answer streams token by token so the provenance trail builds live. Judgeable in the demo video — static output looks dead.

**No install.** `sse-starlette` makes it tidy if Soham wants it:
```bash
pip install sse-starlette
```

**Server side**
```python
from sse_starlette.sse import EventSourceResponse

@app.post("/ask")
async def ask(req: Ask):
    return EventSourceResponse(stream_answer(req.question))
```

**Frontend**
```javascript
const es = new EventSource("/ask");          // GET only — for POST, use fetch + ReadableStream
```

> Note: native `EventSource` is **GET-only**. Since our contract is `POST /ask`, the frontend needs `fetch()` + `response.body.getReader()`. Worth deciding once, early, so the frontend isn't surprised at Gate 2.

**Required headers**
```python
return StreamingResponse(gen(), media_type="text/event-stream",
                         headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
```

`X-Accel-Buffering: no` stops proxies buffering the stream into one lump — a common cause of "SSE works locally, not in production."
</details>

<details>
<summary><b>14. Docker Compose</b> — one-command local setup · Bhushan</summary>

**Why:** Rule 10 accepts complete local setup instructions if deploy fails. This is the insurance policy.

**Check**
```bash
docker compose version
```

**Write it** — `deploy/docker-compose.yml`
```yaml
services:
  falkordb:
    image: falkordb/falkordb:latest
    ports: ["6379:6379"]
  api:
    build: ..
    ports: ["8000:8000"]
    env_file: ../.env
    depends_on: [falkordb]
```

**Run**
```bash
docker compose up
```

**Test on a clean machine before Gate 5** — that's the whole point.
</details>

<details>
<summary><b>15. Fly.io</b> — deployment · Bhushan</summary>

**Why:** a live URL is stronger than local instructions for judging.

**Install**
```bash
brew install flyctl
fly auth login
```

**Deploy**
```bash
fly launch --no-deploy        # generates fly.toml, review it first
fly deploy
fly secrets set ANTHROPIC_API_KEY=sk-ant-...
fly secrets set FALKORDB_PASSWORD=...
fly open
```

**Logs — your main debugging tool when the deploy "works but is blank"**
```bash
fly logs
```

**Trouble**

| Symptom | Fix |
|---|---|
| Connection refused to FalkorDB | needs TLS on Cloud; the client must pass `ssl=True` |
| App works, stream doesn't | proxy buffering — the `X-Accel-Buffering: no` header from step 13 |
| Cold starts too slow | acceptable for a demo; pre-warm right before recording |
</details>

<details>
<summary><b>16. Vercel</b> — alternative deployment · Bhushan</summary>

Use this **instead of** Fly, not alongside. Serverless needs the TLS endpoint from FalkorDB Cloud.

**Install**
```bash
npm i -g vercel
vercel
```

Deploy from the repo root. Add the FalkorDB Cloud credentials as encrypted env vars in the dashboard.

**Trouble:** serverless functions have short timeouts and can't hold TCP connections open — FalkorDB Cloud over TLS is required, not the local Docker instance.
</details>

<details>
<summary><b>17. VS Code</b> — editor · everyone</summary>

**Install**
```bash
brew install --cask visual-studio-code
```

**Extensions**
```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension redhat.vscode-docker
```
Python + Pylance for autocomplete, Docker for container inspection. Add whichever AI assistant you use — **but Rule 11 requires you disclose AI use.**

**Select the interpreter:** `Cmd+Shift+P` → *Python: Select Interpreter* → `.venv`.
Without this the linter will complain about every import.
</details>

<details>
<summary><b>18. Node.js</b> — optional</summary>

**Why:** only if you run a JS frontend dev server, the Vercel CLI, or the MCP inspector. **Not required** — this is a Python-only stack.

**Check**
```bash
node --version
```

**Install**
```bash
brew install node
```

**Trouble:** if Ujwal's dev server grabs port 3000 it collides with the **FalkorDB Browser** (step 4).
</details>

<details>
<summary><b>19. MCP</b> — optional, sponsor-recommended</summary>

**Why:** the sponsor lists MCP as a first-class integration path and Track 01 rewards tool selection through MCP. Useful if we already have working tools — **not a dependency.**

**Install**
```bash
pip install mcp
```

**Inspect tools interactively**
```bash
npx @modelcontextprotocol/inspector
```

**Decision point:** if wrapping three working Cypher functions in MCP costs more than ~30 minutes, skip it and use plain Python tool calls. The rubric rewards MCP, but it rewards a *working agent* more. Don't let this become the thing that breaks at 1am.
</details>

<details>
<summary><b>20. Bulk loader</b> — optional · Bhushan</summary>

**Why:** `UNWIND` creates are fine for a few thousand rows. This is much faster if the load crawls.

**Try plain Cypher first** — probably good enough:
```cypher
CREATE INDEX ON :Service(name)
```
```cypher
UNWIND $rows AS row
CREATE (s:Service {name: row.name, team: row.team})
```

**Only if slow:** the `falkordb-bulk-loader` utility imports CSVs in efficient binary batches.
```bash
pip install falkordb-bulk-loader
```
Docs: `docs.falkordb.com/integration/bulk-loader`

**Measure first:** `g.query(...).run_time_ms` is returned on every result — use it before optimising.
</details>

<details>
<summary><b>21. Deadline timezone check</b> — everyone, do this once</summary>

**Why:** submissions close **Oct 18, 11:59 PM IST**. Not local time. Not midnight GMT.

**Check what IST says right now**
```bash
TZ=Asia/Kolkata date
```

**Countdown**
```bash
echo "Deadline: $(TZ=Asia/Kolkata date -v+2d '+%a %d %b %H:%M IST')"
```

> Set an alarm for **Oct 18, 14:00 IST** — the hard freeze — and a second for **17:00 IST**, the submit. Both are buffer targets, not the real deadline.
</details>

---

## Quickstart

Once steps 1–8 are done, this is the whole local environment:

```bash
git clone <repo-url> && cd graph-hacks
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker run -d --name falkordb -p 6379:6379 falkordb/falkordb:latest
python scripts/generate.py
python scripts/load.py
uvicorn app.main:app --reload
```

Then: Browser at `http://localhost:3000` · API at `http://localhost:8000` · API docs at `http://localhost:8000/docs`

---

## FalkorDB: verified vs unsupported

Everything here was **executed** against FalkorDB `latest`. Don't rediscover these.

### Works — use freely

| Feature | Result |
|---|---|
| Variable-length `[:TYPE*1..4]` | ✅ |
| Variable-length + `OPTIONAL MATCH` + `collect(DISTINCT)` | ✅ → `[['ledger','Platform',['Ravi']]]` |
| `length(path)` for hop depth | ✅ |
| `count()` / `max()` + `ORDER BY` | ✅ |
| `MERGE … ON CREATE SET` | ✅ |
| `CREATE INDEX ON :Label(prop)` | ✅ |
| `db.indexes()` | ✅ |
| `WHERE x CONTAINS 'y'` text search | ✅ |
| Directed `shortestPath((a)-[*]->(b))` | ✅ |

### Does not work — avoid

| Feature | Use instead |
|---|---|
| `shortestPath((a)-[*]-(b))` **undirected** | Throws *"does not support undirected shortestPath traversals"* — directed form only |
| `db.idx.fulltext.createNodeIndex` / `.query` | Procedure not registered in the default image — use `WHERE x CONTAINS 'y'` |
| `type(node)` in the same `RETURN` as an optional node | *"expected Edge or Null but was Node"* — return `labels(node)` instead |

### Gotchas

- **Subset of OpenCypher** with proprietary extensions. Don't assume Neo4j-only syntax — check `/cypher/known-limitations` in the docs.
- Speaks **Redis protocol** (`GRAPH.QUERY` / `GRAPH.RO_QUERY`), not Bolt, by default. Bolt exists via the `BOLT_PORT` config param but is experimental.
- **Cypher cannot traverse an edge backwards.** Any relationship needed in both directions must be written twice under different names.
- **RedisGraph hit end-of-life Jan 2025.** Never present old RedisGraph clients or behaviour as current.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `TypeError: 'QueryResult' object is not iterable` | missing `.result_set` | `g.query(...).result_set` |
| Query returns `[]` but the data is there | wrong arrow direction, or unloaded graph | check with `MATCH (a)-[r]->(b) RETURN a,b` first |
| `Cannot connect to the Docker daemon` | Docker Desktop not running | `open -a Docker`, wait 30s |
| `Address already in use` | port taken | `lsof -i :8000` then kill, or change `--port` |
| Stream works locally, dead in production | proxy buffering | `X-Accel-Buffering: no` header |
| `externally-managed-environment` | venv not active | `source .venv/bin/activate` |
| 401 from Anthropic | key or `.env` | restart uvicorn after editing `.env` |
| Graph has doubled data | loaded twice into a dirty graph | `GRAPH.DELETE helio`, reload |
| Linter can't find imports | wrong interpreter selected | VS Code → Select Interpreter → `.venv` |
| Port 3000 conflict | FalkorDB Browser vs JS dev server | move the dev server |

---

## Who needs what

| Member | Must complete |
|---|---|
| **Bhushan** | 1,2,3,4,5,6,7,8,11,**14**,**15**,21 |
| **Soham** | 1,2,3,4,6,7,8,**9**,11,**12**,**13**,21 |
| **Ujwal** | 1,2,3,4,6,7,8,11,**21** |

**Steps 3–8 are worth doing as a 20-minute group call.** Three people independently discovering the `.result_set` gotcha is three wasted hours, and it's the single thing most likely to block someone silently.

> **Deployment moved.** `deploy/` and `video/` are **Bhushan's**, so steps 14–16 are his. Ujwal still creates the FalkorDB Cloud account (step 10) because two people are blocked on credentials only he can make — but he doesn't deploy against it.

---

## File ownership — who touches what

One file, one owner. With three people and two days, an unowned file is how you lose a night to a bad merge.

| Path | Owner | Contents |
|---|---|---|
| `GROUND_TRUTH.md` | **Bhushan** | The 20 hand-planted facts |
| `data/` · `scripts/` | **Bhushan** | Generator + loader |
| `app/graph.py` | **Bhushan** | **The only Cypher in the repo** |
| `README.md` | **Bhushan** | Data model, Cypher appendix, AI disclosure |
| `deploy/` | **Bhushan** | Dockerfile · compose · `fly.toml` |
| `video/` | **Bhushan** | Script, recording, upload |
| `app/agent.py` · `app/main.py` | **Soham** | The tool-use loop and the frozen API contract |
| `web/` | **Ujwal** | The interface |
| `mock/` | **Ujwal** | `mock/trail.json` — the shared fixture everyone builds against |

**`mock/` is Ujwal's and it is load-bearing.** Soham's fake API branch and Ujwal's frontend both read it. One file, two consumers — that's deliberate. Two independently-written mock sets drift, and the drift only shows up at Gate 2 when real data lands and the renderer breaks on a shape it had never seen.

> **Never edit someone else's file to unblock yourself.** Ping them. Being blocked 20 minutes is much cheaper than a merge conflict at 22:00.