# Setup — Windows

Windows equivalent of [`setup.md`](setup.md). **Same step numbers**, so any reference in [`bhushan.md`](bhushan.md), [`soham.md`](soham.md) or [`ujwal.md`](ujwal.md) still points at the right place.

> Commands target **PowerShell 5.1+** unless stated. Run them from PowerShell, not CMD — the quoting differs.
>
> ⚠️ **These commands were not executed on this machine** (macOS). The FalkorDB behaviour table at the bottom **was** verified against a live instance, and is identical on both platforms. Everything else is standard Windows procedure — expect to hit one PATH gotcha, covered in step 6.

---

## Index

| # | Tool | Needed by |
|---|---|---|
| 1 | [winget](#) | Everyone |
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
<summary><b>1. winget</b> — package manager · everyone</summary>

**Why:** everything else installs through it. Built into Windows 10 1809+ and Windows 11.

**Check**
```powershell
winget --version
```

**Install / update it**
```powershell
winget source update
```

**Accept agreements once, so nothing prompts mid-install**
```powershell
winget config --accept-source-agreements
```

**If winget is missing** — older Windows build. Either update Windows, or use [Scoop](https://scoop.sh):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```

**Trouble:** `winget` not found after install — open a **new** terminal. PATH changes don't apply to an already-open shell.
</details>

<details>
<summary><b>2. Git + GitHub</b> — version control · everyone</summary>

**Why:** Rule 10 requires a **public** repository.

**Check**
```powershell
git --version
gh --version
```

**Install**
```powershell
winget install --id Git.Git -e
winget install --id GitHub.cli -e
```

**First-time setup**
```powershell
git config --global user.name "Bhushan"
git config --global user.email "you@example.com"
gh auth login
```

**Create the shared repo — Bhushan**
```powershell
cd $HOME\Life
gh repo create graph-hacks --public --clone
cd graph-hacks
gh repo add-collaborator soham -f Reader
gh repo add-collaborator ujwal -f Reader
```

> **Install Git Bash** (comes with Git). If you and a teammate get different results on the same command, that's usually PowerShell vs Bash.
</details>

<details>
<summary><b>3. Docker Desktop</b> — runs FalkorDB · everyone</summary>

**Why:** FalkorDB runs in Docker.

**Check**
```powershell
docker --version
docker ps
```

**Install**
```powershell
winget install --id Docker.DockerDesktop -e
```

**⚠️ WSL2 is required.** Docker Desktop on Windows needs the WSL2 backend:

```powershell
wsl --install
```

Then **reboot**, launch Docker Desktop, and confirm *Use the WSL 2 based engine* is checked in Settings → General.

**Trouble — the most common failures**

| Symptom | Cause | Fix |
|---|---|---|
| `error during connect: ... pipe/docker_engine` | Desktop not running | start Docker Desktop, wait 30s |
| `cannot connect to the Docker daemon` | WSL2 backend off | Settings → General → WSL2 → restart |
| `requires Windows 10 build 19045+` | old Windows | update Windows |

**Alternative — WSL2 with Docker Engine inside:**
```powershell
wsl --install -d Ubuntu
wsl
# inside Ubuntu:
sudo apt update && sudo apt install -y docker.io
sudo service docker start
```
</details>

<details>
<summary><b>4. FalkorDB</b> — the graph database · everyone</summary>

**Why:** the mandatory technology. Rule 2 — primary graph DB. Rule 3 — the graph must do real work.

**Check**
```powershell
docker ps | Select-String falkordb
```

**Install & run**
```powershell
docker pull falkordb/falkordb:latest
docker run -d --name falkordb -p 6379:6379 falkordb/falkordb:latest
```

**Verify — should print `1`**
```powershell
docker exec falkordb redis-cli GRAPH.QUERY g "RETURN 1 AS ok"
```

**Useful commands**
```powershell
docker ps                                   # is it up?
docker logs falkordb                        # problems
docker restart falkordb                     # hung?
docker rm -f falkordb                       # reset, then re-run
```

**Connect from Python**
```python
from falkordb import FalkorDB
db = FalkorDB(host="localhost", port=6379)
g  = db.select_graph("helio")
print(g.query("RETURN 1 AS ok").result_set)   # -> [[1]]
```

> ⚠️ **`.result_set` is required.** `g.query()` returns a `QueryResult` that is **not iterable**. `for row in g.query(...)` raises `TypeError`. This silently costs the first hour — mention it in your first group call.

**⚠️ Port conflicts are more common on Windows.** Find what's holding one:
```powershell
netstat -ano | findstr :6379
```
Kill by PID (last column):
```powershell
taskkill /PID 12345 /F
```
Same for `3000` (Browser) and `8000` (API).

**Clear the graph between generator runs** — never load twice into a dirty graph:
```powershell
docker exec falkordb redis-cli GRAPH.LIST
docker exec falkordb redis-cli GRAPH.DELETE helio
```
</details>

<details>
<summary><b>5. FalkorDB Browser</b> — visual explorer · everyone</summary>

**Why:** the main dev loop — run Cypher, inspect the model, debug why a query returns nothing.

**Install:** nothing. Ships inside the container.

**Open**
```
http://localhost:3000
```

**Useful inside Browser**
```cypher
:reset                     // wipe the graph
MATCH (n) RETURN labels(n), count(*)
MATCH (n:Person) RETURN n.name LIMIT 10
```

> If a dev server has taken port 3000, Browser won't load — check with `netstat -ano | findstr :3000`.
</details>

<details>
<summary><b>6. Python</b> — the language · everyone</summary>

**Why:** one language end to end — generator, loader, graph layer, agent, API.

**Check**
```powershell
py --version
```

**Install (3.11+)**
```powershell
winget install --id Python.Python.3.12 -e
```

> ⚠️ **Close and reopen your terminal after installing.** Python adds itself to PATH at install time; an already-open PowerShell won't see it, so `py` looks missing when it isn't.

**Confirm the launcher sees it**
```powershell
py -0p            # lists all installed Pythons
py -3.12 --version
```

> **Use `py`, not `python`.** Windows often has a Microsoft Store stub named `python` that opens the Store instead of running anything. `py` always resolves.

**Need several versions:** [pyenv-win](https://github.com/pyenv-win/pyenv-win) instead.
</details>

<details>
<summary><b>7. Virtual environment</b> — isolated deps · everyone</summary>

**Why:** keeps our packages out of system Python and off each other's toes.

**Create + activate**
```powershell
cd $HOME\Life\graph-hacks
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**If activation is blocked by the execution policy:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Check** — prompt shows `(.venv)`
```powershell
python --version
pip --version
```

**Deactivate:** `deactivate`

> **Git Bash / CMD users:** activate with `.venv\Scripts\activate` (no `.ps1`) — different file.

**Commit `.gitignore` first**
```gitignore
.venv/
.env
__pycache__/
*.pyc
Thumbs.db
desktop.ini
node_modules/
```
</details>

<details>
<summary><b>8. Python packages</b> — everyone, one command</summary>

**Install**
```powershell
.\.venv\Scripts\Activate.ps1
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
| `httpx` | Bhushan | calling the Anthropic API |

**Freeze them**
```powershell
pip freeze > requirements.txt
```

**Optional**
```powershell
pip install mcp                     # only if using the MCP route
pip install falkordb-bulk-loader    # faster CSV loads
```

**Trouble**

| Symptom | Fix |
|---|---|
| `'python' is not recognized` | venv not activated, or terminal not reopened |
| `externally-managed-environment` | same — activate the venv |
| Build fails on a dependency | very new Python — drop to 3.12 |
</details>

<details>
<summary><b>9. Anthropic API key</b> — the LLM · Soham, Bhushan</summary>

**Why:** the agent loop. Tool use is the product.

**Get a key**
1. Sign up at `console.anthropic.com`
2. **API Keys** → Create new key
3. Add credit under **Billing** — free tier won't cover a hackathon

**Set it (this session)**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

**Or permanently, for your user account**
```powershell
[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-...", "User")
```
Then open a new terminal.

> **Still create a `.env`** (step 11) for the repo. The Windows env var is a convenience; `.env` is what travels with the project and what `python-dotenv` reads.

**Verify**
```powershell
.\.venv\Scripts\Activate.ps1
python -c "import anthropic; c=anthropic.Anthropic(); print(c.models.list().data[0].id)"
```

**Trouble**

| Symptom | Fix |
|---|---|
| `401` | key wrong or `.env` not loaded — restart uvicorn after editing `.env` |
| `credit balance is too low` | add billing credit |
| tool calls not firing | use a current model; confirm you pass `tools=` |
</details>

<details>
<summary><b>10. FalkorDB Cloud</b> — hosted database · Ujwal creates, all use</summary>

**Why:** production deploy without babysitting a database. Rule 4 allows FalkorDB Cloud.

**Create:** sign up at `app.falkordb.cloud` → create an instance → copy credentials.

**Share with the team** in the group chat. In `.env`:
```
FALKORDB_HOST=xxx.falkordb.cloud
FALKORDB_USERNAME=default
FALKORDB_PASSWORD=...
FALKORDB_GRAPH=helio
```

**Verify against Cloud before building the deploy** — if this fails locally, nothing works in production:
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

**Trouble:** cloud instances often need **TLS on a non-default port**. Check the dashboard for the exact host/port, and whether your client needs `ssl=True`.
</details>

<details>
<summary><b>11. Environment variables</b> — everyone</summary>

**Why:** keeps API keys out of the repo. Never commit `.env`.

**Create — a here-string is safer than `echo` on Windows**
```powershell
@"
ANTHROPIC_API_KEY=sk-ant-...
FALKORDB_HOST=
FALKORDB_USERNAME=
FALKORDB_PASSWORD=
FALKORDB_GRAPH=helio
"@ | Set-Content .env

Copy-Item .env .env.example      # commit this one, keys blank
```

**Load in Python**
```python
from dotenv import load_dotenv
load_dotenv()
```

**Confirm `.env` is ignored**
```powershell
git check-ignore .env; if ($LASTEXITCODE -eq 0) { "OK, ignored" }
```

> ⚠️ **PowerShell `curl` is not curl.** In PowerShell 5.1 `curl` is an alias for `Invoke-WebRequest` with different flags. Use `curl.exe` when you actually want curl:
> ```powershell
> curl.exe https://example.com
> ```
</details>

<details>
<summary><b>12. FastAPI + Uvicorn</b> — the backend · Soham</summary>

**Why:** serves `POST /ask` and streams the answer.

Already installed in step 8.

**Run**
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**Check**
```powershell
Invoke-RestMethod http://localhost:8000/health
```

**Auto docs — free and very useful**
```
http://localhost:8000/docs
```

**Trouble**

| Symptom | Fix |
|---|---|
| `Address already in use` | `netstat -ano \| findstr :8000` → `taskkill /PID <pid> /F` |
| Changes not appearing | launch via `uvicorn`, not `python`, so `--reload` works |
| `Execution of .ps1 is blocked` | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
</details>

<details>
<summary><b>13. SSE</b> — streaming · Soham, Ujwal</summary>

**Why:** the answer streams token by token so the trail builds live. Static output looks dead in a demo video.

**No install.** `sse-starlette` makes it tidy:
```powershell
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
const es = new EventSource("/ask");   // GET only — see below
```

> Native `EventSource` is **GET-only**. Our contract is `POST /ask`, so the frontend needs `fetch()` + `response.body.getReader()`. Decide this once early so Ujwal isn't surprised at Gate 2.

**Required headers**
```python
return StreamingResponse(gen(), media_type="text/event-stream",
                         headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
```

`X-Accel-Buffering: no` stops proxies buffering the stream into one lump — a common cause of "works locally, dead in production."
</details>

<details>
<summary><b>14. Docker Compose</b> — one-command local setup · Bhushan</summary>

**Why:** Rule 10 accepts complete local setup instructions if deploy fails. This is the insurance policy.

**Check**
```powershell
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
```powershell
docker compose up
```

**Test on a clean machine before Gate 5** — use a teammate's laptop that has never seen the repo.
</details>

<details>
<summary><b>15. Fly.io</b> — deployment · Bhushan</summary>

**Why:** a live URL is stronger than local instructions for judging.

**Install**
```powershell
iwr https://fly.io/install.ps1 | iex
```
If that fails, download the binary from `fly.io/docs/hands-on/install-flyctl/`.

**Deploy**
```powershell
fly auth login
fly launch --no-deploy        # generates fly.toml, review it first
fly deploy
fly secrets set ANTHROPIC_API_KEY=sk-ant-...
fly secrets set FALKORDB_PASSWORD=...
fly open
```

**Logs — your main debugging tool when the deploy "works but is blank"**
```powershell
fly logs
```

**Trouble**

| Symptom | Fix |
|---|---|
| Connection refused to FalkorDB | needs TLS on Cloud; client must pass `ssl=True` |
| App works, stream doesn't | proxy buffering — the `X-Accel-Buffering: no` header |
| `fly: command not found` | terminal not reopened after install |
| Cold starts slow | acceptable; pre-warm before recording |
</details>

<details>
<summary><b>16. Vercel</b> — alternative deployment · Bhushan</summary>

Use **instead of** Fly, not alongside. Serverless needs the TLS endpoint from FalkorDB Cloud.

**Install**
```powershell
npm install -g vercel
vercel
```

Add the FalkorDB Cloud credentials as encrypted env vars in the dashboard.

**Trouble:** serverless functions have short timeouts and can't hold TCP connections open — FalkorDB Cloud over TLS is required, not the local Docker instance.
</details>

<details>
<summary><b>17. VS Code</b> — editor · everyone</summary>

**Install**
```powershell
winget install --id Microsoft.VisualStudioCode -e
```

**Extensions**
```powershell
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-azuretools.vscode-docker
```

**Select the interpreter:** `Ctrl+Shift+P` → *Python: Select Interpreter* → `.venv`.
Without this the linter flags every import.

**Two settings worth changing**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}\\.venv\\Scripts\\python.exe",
  "files.eol": "\n"
}
```
`files.eol` matters — a repo mixing CRLF and LF gives three people noisy diffs for no reason.

> **Want a Unix-like shell?** Install [Git Bash](https://gitforwindows.org/) (ships with Git) or [Windows Terminal](https://learn.microsoft.com/windows/terminal/). It removes most PowerShell-vs-Bash differences.
</details>

<details>
<summary><b>18. Node.js</b> — optional</summary>

**Why:** only for a JS frontend dev server, the Vercel CLI, or the MCP inspector. **Not required** — this is a Python-only stack.

**Check**
```powershell
node --version
```

**Install**
```powershell
winget install --id OpenJS.NodeJS.LTS -e
```

**Trouble:** a dev server on port 3000 collides with the **FalkorDB Browser** (step 5).
</details>

<details>
<summary><b>19. MCP</b> — optional, sponsor-recommended</summary>

**Why:** the sponsor lists MCP as a first-class integration path. Useful if you already have working tools — **not a dependency.**

**Install**
```powershell
pip install mcp
```

**Inspect tools interactively**
```powershell
npx @modelcontextprotocol/inspector
```

**Decision point:** if wrapping three working Cypher functions in MCP costs more than ~30 minutes, skip it and use plain Python tool calls. The rubric rewards MCP, but it rewards a *working agent* more. Don't let this be the thing that breaks at 1am.
</details>

<details>
<summary><b>20. Bulk loader</b> — optional · Bhushan</summary>

**Why:** `UNWIND` creates are fine for a few thousand rows. Much faster if the load crawls.

**Try plain Cypher first**
```cypher
CREATE INDEX ON :Service(name)
```
```cypher
UNWIND $rows AS row
CREATE (s:Service {name: row.name, team: row.team})
```

**Only if slow:** `falkordb-bulk-loader` imports CSVs in binary batches.
```powershell
pip install falkordb-bulk-loader
```
Docs: `docs.falkordb.com/integration/bulk-loader`

**Measure first:** every result carries `run_time_ms` — use it before optimising.
</details>

<details>
<summary><b>21. Deadline timezone check</b> — everyone, do this once</summary>

**Why:** submissions close **Oct 18, 11:59 PM IST**. Not local time. Not midnight GMT.

**What IST says right now**
```powershell
[System.TimeZoneInfo]::ConvertTimeBySystemTimeZoneId((Get-Date), "India Standard Time")
```

> ⚠️ The ID is the **Windows** name, `"India Standard Time"`. On Linux/macOS it's `"Asia/Kolkata"`. Using the wrong one throws.

**Short form — define once, reuse**
```powershell
function Get-IST { [System.TimeZoneInfo]::ConvertTimeBySystemTimeZoneId((Get-Date), "India Standard Time") }
Get-IST
```

> Set alarms for **Oct 18, 14:00 IST** (hard freeze) and **17:00 IST** (submit). Both are buffer targets, not the real deadline.
</details>

---

## Quickstart

```powershell
git clone <repo-url>
cd graph-hacks
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker run -d --name falkordb -p 6379:6379 falkordb/falkordb:latest
python scripts\generate.py
python scripts\load.py
uvicorn app.main:app --reload
```

Then: Browser `http://localhost:3000` · API `http://localhost:8000` · API docs `http://localhost:8000/docs`

---

## FalkorDB: verified vs unsupported

Everything here was **executed** against FalkorDB `latest` and is platform-independent — identical on Windows, macOS and Linux.

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
| `shortestPath((a)-[*]-(b))` **undirected** | Throws *"does not support undirected shortestPath traversals"* — directed only |
| `db.idx.fulltext.createNodeIndex` / `.query` | Procedure not registered in the default image — use `WHERE x CONTAINS 'y'` |
| `type(node)` in the same `RETURN` as an optional node | *"expected Edge or Null but was Node"* — return `labels(node)` |

### Gotchas

- **Subset of OpenCypher** with proprietary extensions. Don't assume Neo4j-only syntax.
- Speaks **Redis protocol** (`GRAPH.QUERY`), not Bolt, by default.
- **Cypher cannot traverse an edge backwards** — write the relationship twice under different names if you need both directions.
- **RedisGraph hit end-of-life Jan 2025.** Never present old RedisGraph clients as current.

---

## Windows troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `python` not recognized | Store stub, or terminal not reopened | use `py -3.12`; open a new terminal |
| `py` not found after install | PATH not refreshed | close and reopen the terminal |
| `.venv\Scripts\Activate.ps1` blocked | execution policy | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `curl` behaves oddly | PowerShell alias for `Invoke-WebRequest` | use `curl.exe` |
| `'externally-managed-environment'` | venv not active | `.\.venv\Scripts\Activate.ps1` |
| Docker won't start | WSL2 backend not enabled | Settings → General → WSL2 → restart |
| `Address already in use` | port taken | `netstat -ano \| findstr :PORT` → `taskkill /PID <pid> /F` |
| Query returns `[]` but data is there | wrong arrow direction, or unloaded graph | check with `MATCH (a)-[r]->(b) RETURN a,b` |
| Noisy cross-machine diffs | CRLF/LF mixing | set `"files.eol": "\n"` in VS Code |
| `.env` set in PowerShell but Python doesn't see it | Python doesn't read shell env for the repo | use `python-dotenv` — that's what `.env` is for |

---

## Who needs what

| Member | Must complete |
|---|---|
| **Bhushan** | 1,2,3,4,5,6,7,8,11,**14**,**15**,21 |
| **Soham** | 1,2,3,4,6,7,8,**9**,11,**12**,**13**,21 |
| **Ujwal** | 1,2,3,4,6,7,8,11,**21** |

**Steps 3–8 are worth doing as a 20-minute group call.** Three people independently discovering the `.result_set` gotcha is three wasted hours, and it's the one thing most likely to block someone silently.

> **Deployment moved.** `deploy/` and `video/` are **Bhushan's**, so steps 14–16 are his. Ujwal still creates the FalkorDB Cloud account (step 10) because two people are blocked on credentials only he can make — but he doesn't deploy against it.
>
> **File ownership:** Bhushan owns `GROUND_TRUTH.md` · `data/` · `scripts/` · `app/graph.py` · `README.md` · `deploy/` · `video/`. Soham owns `app/agent.py` · `app/main.py`. Ujwal owns `web/` · `mock/`. See [`setup.md`](setup.md) for the full table.