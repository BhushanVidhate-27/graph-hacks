# Helio — A Company Brain (`angy-fronted`)

**Track 03: Company Brain · Graph Hacks**

An award-winning CAD/Knowledge Graph HUD interface for **Helio** — an enterprise organizational knowledge graph powered by **FalkorDB** and Cypher.

---

## 🎯 The Core Philosophy

Existing enterprise search answers *"where is the doc about X"*. Helio answers:
* **Who knows about X?** (Volume vs. recency separated — no Priya Sharma trap)
* **What breaks if it dies?** (Multi-hop `HAS_DEPENDENT` cascade blast radius)
* **Where was that decided?** (`SUPERSEDES` decision provenance — e.g. D-19 Adyen primary, Stripe fallback)
* **How current is that answer?** (Automated 90-day edge freshness decay)
* **Honest Negatives**: When no `OWNED_BY` edge exists for `config-service`, Helio explicitly returns *"No team owns it"* instead of hallucinating.

---

## 🖥️ Interactive Modules & Views

1. **Full Company Brain Showcase**:
   - Real-time cursor coordinates HUD (`X: [px] / Y: [px]`) with live FalkorDB Cypher diagnostic logs.
   - Replicated signature sliding split-text hover buttons (`HeronButton`).
   - SVG noise displacement shaders and hairline CAD grid markers.

2. **Interactive Blast Radius & Dependency Inspector**:
   - Compare naive flat search (stale documents & hallucinations) with deterministic graph traversal.
   - Interactive nodes for `payments-gateway`, `config-service`, `decision-d19`, and `ledger-service`.
   - Real Cypher statements and ground-truth citations.

3. **Helio Natural Language Cypher Agent**:
   - Pre-loaded with test questions from `GROUND_TRUTH.md`.
   - Live Cypher query execution and visual path traversal chips.

4. **Helio FalkorDB Graph Console**:
   - Microservices inventory table with SLA, tier, on-call assignments, and staleness metrics.
   - 5 Teams filters: Platform, Ledger, Payments, Risk, Growth.

5. **Responsive Viewport Simulator**:
   - Test the interface across Desktop (1440px), iPad (820px), and iPhone (390px) frames.

---

## 🚀 Quick Start

```bash
npm install
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)**.

### Production Build
```bash
npm run build
npm run preview
```
Open **[http://localhost:4173](http://localhost:4173)**.
