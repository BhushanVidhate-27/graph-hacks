# Compaction / handoff — Helio frontend

Paste everything below into the new session. Working tree is clean and the
captured HTML is fully restored, so the new session starts from a known state.

---

## 1. What this is

**Helio** — a company knowledge-graph agent (FalkorDB graph traversal + LLM
tool-use loop) built for a hackathon.

- Backend live at `https://helio-brain.onrender.com` (Render service
  `helio-brain`, id `srv-db9l2uom7kps73dq32q0`)
- Frontend in `front/` — a reverse-engineered Webflow capture, rebranded to
  Helio, plus a real `/demo` route that hits the deployed backend
- `front/` is its **own git repo**, cloned from `sourav9823/heronaiapp`.
  Do **not** push there — it is someone else's template repo. It needs a new
  remote under our account.

## 2. Repo state

```
repo root:  /Users/bhushan/Life/graph-hacks-bhushan/front
branch:     master
HEAD:       d259b10  feat: Helio copy, live /demo route, and a cascade that stops fighting itself
            241189e  fix(clone): make the captured site actually work
```

Untracked (not yet committed):
- `TODO.md` — the task list, all items open
- `scripts/html_spans.py` — the byte-range finder (see §4, this is load-bearing)

A pre-commit hook (`ponytail`) runs lint → typecheck → build on every commit.

## 3. CRITICAL — the captured HTML is not balanced

`front/public/sites/heronaiapp.com-e0b5c319/root-8a5edab2/heron-body.html`
(232,657 bytes) has **several unclosed `<div>`s**.

Consequence, already paid for once: the obvious cut — count `<div` / `</div>`
from an element's start until depth returns to zero — **runs past the element's
real end and eats the rest of the document**. That silently deleted the footer
and the `home-map` / `home-platform` / `home-why` / `home-usecase` sections in
one go. The cut looked balanced and was not.

The file was restored with `git checkout HEAD -- <path>` and is verified intact:

```
bytes: 232657   </main>: 1   <footer: 2
home-map-wrap: 2   home-why-wrap: 3   home-usecase-wrap: 3
```

**Rule: never edit that file without `scripts/html_spans.py`.** It exposes:

```python
import sys; sys.path.insert(0, "scripts")
import html_spans as H

H.find_element(src, 'class="awwwards"')   # -> (start, end) byte range
H.cut(src, 'class="awwwards"', "label")   # cut + sentinel guard, returns new src
H.Guard(src).ok(candidate)                # raises if </main>, <footer>,
                                          # home-*-wrap counts would drop
```

Always call `H.Guard(src).ok(out)` before writing. `SENTINELS` in that file is
the tripwire.

Note: `handle_endtag` was just fixed (the nesting-prune line removed — it was
deleting inner spans, so plain divs never appeared). It has **not yet been
re-tested**; verify `find_element` returns sane ranges before trusting a cut.

## 4. Section order in the captured file

```
loading overlay → home-hero → home-intro → home-problem
→ home-map → home-platform → home-why → home-usecase → cta → footer
```

Only `home-hero`, `home-intro` and `home-problem` are `<section>` tags; the rest
sit inside `<*-wrap>` custom elements.

## 5. The cascade — do not undo this

Two stylesheets, and **load order is the entire mechanism**:

1. `.../root-8a5edab2/heron.css` — captured Webflow CSS. **Must stay unlayered.**
   Its markup is Webflow output using class names Tailwind also owns
   (`.grid`, `.container`, `.hidden`, `.block`, `.flex`). Give it a layer and
   Tailwind's utilities outrank it *by layer order, not specificity*, and every
   full-width section on the landing page halves. That regression was observed
   and reverted.
2. `front/public/helio.css` — our own. Also unlayered, loads **after** the
   captured sheet, so source order decides.

The captured sheet ships normalize.css, which is unlayered, and an unlayered
rule beats every layered rule regardless of specificity. That is why
`text-[10px]` on a `<button>` was rendering at 25.6px instead of 10px —
`button,input{font:inherit}` was silently winning. Helio components therefore
use plain classes (`.hc-btn`, `.helio-route`, …), **not** Tailwind utilities.

Both `src/app/page.tsx` and `src/components/site-header.tsx` carry
`eslint-disable @next/next/no-css-tags` with that reasoning attached. Leave them.

## 6. Header offset is measured, not hardcoded

`src/components/header-offset.tsx` writes `--header-h` at runtime. The captured
header is `position: fixed` and is **two rows on desktop (121px), one on mobile
(93px)** — no constant works. `public/helio.css` reserves the space, and that
rule must stay **after** the `@media` block, because that query uses the
`padding` shorthand and would otherwise reset `padding-top`.

## 7. Removed third-party scripts — this was the big one

The capture loaded 12 scripts that are not ours: jQuery, Webflow runtime, Lenis,
GSAP + ScrollTrigger/SplitText/TextPlugin, Barba, Swiper,
`heronai-bp.netlify.app/config.js` (the original site's config, pulled from
*their* domain), and a `resources-saver` branding script.

Consequences, all now understood:
- `resources-saver` deleted DOM nodes **during parse**, before React hydrated →
  the hydration mismatch.
- `heronai-bp.netlify.app/config.js` → `main.js` → `TypeError: Cannot read
  properties of undefined (reading 'parentElement')`, which is also the most
  likely cause of the **problems-pagination-only-advancing-two-steps** bug: their
  scroll controller against our DOM.

All 12 were removed; `0 console errors` after. **These removals were lost by the
restore and need redoing.**

## 8. Remaining TODOs

Full list in `TODO.md`. All open. Priority order:

**Redo first (were done, then lost in the restore):**
1. Remove `<div class="awwwards">` — third-party "Site of the Day" badge
2. Remove `<div id="heron-cookie-root">` — we set no cookies, run no analytics;
   a consent banner for nothing claims a data practice we don't have
3. Remove the 12 script tags (§7)
4. Remove `class="home-hero-img-inner"` — 47KB inline SVG of architectural
   facade elevations with X/Y callouts (use `html_spans.py`)

**Then:**
5. Replace the hero artwork with a graph visual — a working node-link SVG was
   drafted and is in the transcript; nodes mirror the real graph
   (`payments-gateway` → `checkout-api` / `config-service` / `dispute-service`,
   `OWNED_BY` → Payments). `config-service` has **no** `OWNED_BY` edge and is
   drawn dashed to an open marker, because the refusal is the product's most
   interesting row.
6. Problems section — heading overlapping the image (may now be resolved once
   their scripts are gone; re-check before changing anything)
7. Problems pagination — four items, scroll only advances two
8. `home-why` — "FOR THE WHOLE DESIGN" / "RIGHT THERE WITH YOU" sit in one dead
   zone. Each should own **100vh** and swap on scroll
9. Floor-plan imagery + the IBC 1020.2 code panel (`home-platform`) — remove
10. **Footer** — rewrite wholesale. Currently the reference site's sitemap,
    address and policy links with our words dropped in. Also still links to
    `thefwa.com/profiles/bear-plus`, `awwwards.com/bearplus`,
    `instagram.com/bearplus.agency`. Remove all of it; nothing inherited.
11. **Navbar** — oversized. ~120px tall, two rows, eats a third of a laptop
    viewport. Rebuild as a single compact row.
12. Remaining foreign copy (from the audit subagent):
    - `bear.plus` link + "Bhushan, Soham and Ujwal" in the hero paragraph
    - `1801 California St. Suite 2400 Denver, CO 80202` in the loader
    - `Click and drag your mouse to see violations` in the hero
    - `Design software is powerful but passive.` in problems
    - `your model` ×2, `your project` ×1
    - `AI Practices`, `Design Workflows` nav dropdown labels
    - the `home-intro` H2 tail `SO YOU CAN STAY FOCUSED ON THE DESIGN, NOT THE SOFTWARE`
    - the 5KB blockout SVG in `.loading-img-inner` with **Vietnamese comments**
    - two `.avif` files in `home-intro` (`image-20345`, `image-20330`) — likely
      original product renders
13. `assets/` still holds unused original architecture imagery
    (`Architects-*.jpg`, `BIM-20MANAGERS-*.jpg`, `DRAFTERS-*.jpg`,
    `ENGINEERS-*.jpg`, `footer1-*.avif`, `cta-20image-*.webp`, `Dimensions-*.png`)
    — prune once nothing references it.
14. Known latent bug: unterminated `<div id="w-node-..."` tag around the
    `home-intro-partner-wrap` area (~byte 115000 in the HEAD version).

**Ship:**
15. Deploy with a domain, then add that origin to the backend's
    `CORS_ALLOW_ORIGINS` or `/demo` fails cross-origin.
16. Point `front/` at a remote under our account.

## 9. Backend context (not being worked on)

- Groq, free tier, 1,000 req/day. Model `openai/gpt-oss-120b`
  (`llama-3.3-70b-versatile` is NOT available). OpenRouter/Anthropic fully removed.
- Frozen contract: `{answer, trail[], stale[]}`; `trail[].date` must be `str`.
- **The server sends a FULL SNAPSHOT per SSE frame — handlers must REPLACE, not
  append.** (Already handled in `src/lib/api.ts`.)
- Agent results are **not stable run-to-run** (sampled model). Never trust a
  single gate sweep. 10/20 questions fail at the agent layer; the refusal-vocabulary
  fix is unmerged on `fix/grader-refusal-vocabulary` (7b576db).
- 1021 tests pass; 21/21 ground-truth checks, 0 FAIL.

## 10. Model recommendation

Only **10 models** are available on this `opencode` provider, all free, no
context/pricing metadata exposed:

```
nemotron-3.5-super-vl-free    beam-free          longcat-2.5-preview-free
space-bunny-free              mimo-v2.6-flash-free   deepseek-v4.1-flash-free
glm-5.3-flash-free            nemotron-3.5-lightning-free
nemotron-3-ultra-free         big-pickle
```

There is no Claude / GPT / Gemini here, so the usual "Sonnet for code, GPT for
reasoning" advice does not apply. For **this** work specifically — careful
multi-step surgery on a 232KB malformed HTML file where one wrong cut silently
deletes half the page — the priority is **edit precision and instruction
following over raw speed**:

1. **`glm-5.3-flash-free`** — best default here. Strong at structured,
   instruction-heavy refactors and at *not* improvising; the failure mode that
   cost us the footer was an agent optimising past a malformed structure.
2. **`nemotron-3-ultra-free`** — pick this if the remaining work turns into real
   diagnosis (the pagination bug is still unexplained) rather than mechanical
   cuts.
3. **`space-bunny-free`** — keep only if you want the current behaviour; fine on
   routine edits, but it is the model that was running when the truncation
   happened, so give it a smaller blast radius, not the whole file.

Whatever you pick: the failure mode to guard against is an agent "fixing"
malformed markup by rewriting it. **Use `html_spans.py` for every cut in that
file and keep the `SENTINELS` guard on.**