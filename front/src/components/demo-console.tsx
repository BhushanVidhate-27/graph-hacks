"use client";

import { Fragment, useState, type ReactNode } from "react";
import { ask, validateContract, type AskState, type TrailRow } from "@/lib/api";

/**
 * The demo console.
 *
 * Speaks the frozen contract directly: POST /ask, SSE frames of
 * {answer, trail[], stale[]}. Two things are load-bearing:
 *
 * 1. The server sends a FULL SNAPSHOT on every frame, not a delta. A handler
 *    that appends renders 12 chips where there are 6. Replace, never append.
 * 2. An empty trail renders as an explicit "no path exists", not a blank area.
 *    The refusal is the feature — a demo that always answers is not a demo.
 *
 * Styling is plain classes from /helio.css rather than Tailwind utilities. On
 * this page a utility is a coin toss against the captured stylesheet's
 * unlayered normalize reset, which beats every layered rule regardless of
 * specificity. See the note at the top of helio.css.
 */

const EDGE_COLOR: Record<string, string> = {
  OWNED_BY: "#0f766e",
  DEPENDS_ON: "#4338ca",
  HAS_DEPENDENT: "#7c3aed",
  SUPERSEDES: "#be185d",
  EVIDENCED_BY: "#a16207",
  MENTIONS: "#0369a1",
  REPORTS_TO: "#4338ca",
  MEMBER_OF: "#0f766e",
  CONTRIBUTED_TO: "#a16207",
};

const SUGGESTIONS = [
  "What breaks if payments-gateway dies?",
  "Who owns ledger-core?",
  "Who owns config-service?",
];

export function DemoConsole() {
  const [state, setState] = useState<AskState>({
    status: "idle",
    answer: "",
    trail: [],
    stale: [],
  });
  const [q, setQ] = useState("");
  const [open, setOpen] = useState<number | null>(null);

  const drift = validateContract(state.trail);

  const run = async (question: string) => {
    const text = question.trim();
    if (!text || state.status === "streaming") return;
    setQ(text);
    setOpen(null);
    await ask(text, setState);
  };

  const busy = state.status === "streaming";

  return (
    <div className="hc">
      {/* Ask */}
      <div className="hc-ask">
        <div className="hc-ask-row">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void run(q)}
            placeholder="Who owns payments-gateway today?"
            aria-label="Ask the graph a question"
            className="hc-input"
          />
          <button
            onClick={() => void run(q)}
            disabled={busy || !q.trim()}
            className="hc-btn"
          >
            {busy ? "Traversing…" : "Ask"}
          </button>
        </div>
        <div className="hc-suggestions">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => void run(s)}
              disabled={busy}
              className="hc-chip"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Answer */}
      <div className="hc-body">
        {state.status === "idle" ? (
          <p className="hc-idle">Awaiting question</p>
        ) : state.error ? (
          <>
            <p className="hc-error-label">Unavailable</p>
            <p className="hc-error">{state.error}</p>
          </>
        ) : (
          <>
            <p className="hc-label">
              {busy ? "Traversing graph" : "Answer"}
            </p>
            <div className="hc-answer">
              {state.answer ? (
                <Markdown text={state.answer} />
              ) : (
                <span className="hc-chip">Thinking…</span>
              )}
            </div>

            {/* Contract canary — silent when healthy, by design. A warning that
                can appear during a recorded demo is worse than none. */}
            {drift.length > 0 && (
              <p className="hc-drift">contract drift: {drift[0]}</p>
            )}

            <Trail trail={state.trail} open={open} setOpen={setOpen} />
          </>
        )}
      </div>
    </div>
  );
}

/**
 * Renders the light markdown the agent actually emits.
 *
 * `**bold**` for service names, `* item` for list entries, blank line between
 * paragraphs. Anything else is left as literal text — the alternative is a
 * markdown parser for three constructs, and a parser is a larger attack surface
 * than the output warrants.
 */
function Markdown({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/);
  return (
    <>
      {blocks.map((block, bi) => {
        const lines = block.split("\n").filter((l) => l.trim());
        if (!lines.length) return null;

        const isList = lines.every((l) => /^\s*[*-]\s+/.test(l));
        if (isList) {
          return (
            <ul key={bi}>
              {lines.map((l, li) => (
                <li key={li}>
                  <Inline text={l.replace(/^\s*[*-]\s+/, "")} />
                </li>
              ))}
            </ul>
          );
        }

        return (
          <p key={bi}>
            {lines.map((l, li) => (
              <Fragment key={li}>
                {li > 0 && <br />}
                <Inline text={l} />
              </Fragment>
            ))}
          </p>
        );
      })}
    </>
  );
}

function Inline({ text }: { text: string }): ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
  return (
    <>
      {parts.map((p, i) =>
        p.startsWith("**") && p.endsWith("**") ? (
          <strong key={i}>{p.slice(2, -2)}</strong>
        ) : (
          <Fragment key={i}>{p}</Fragment>
        ),
      )}
    </>
  );
}

function Trail({
  trail,
  open,
  setOpen,
}: {
  trail: TrailRow[];
  open: number | null;
  setOpen: (i: number | null) => void;
}) {
  if (!trail.length) {
    return (
      <p className="hc-trail-empty">
        No path exists — the agent found nothing and said so.
      </p>
    );
  }
  const edges = trail.filter((r) => r.via_edge).length;

  return (
    <div className="hc-trail">
      <p className="hc-label">
        Provenance trail — {trail.length} node{trail.length === 1 ? "" : "s"},{" "}
        {edges} edge{edges === 1 ? "" : "s"}
      </p>
      <ol className="hc-chain">
        {trail.map((row, i) => {
          const color = EDGE_COLOR[row.via_edge] ?? "#8a8578";
          const expanded = open === i;
          return (
            <li key={`${row.type}-${row.name}-${i}`} className="hc-node">
              <button
                onClick={() => setOpen(expanded ? null : i)}
                aria-expanded={expanded}
                className="hc-node-btn"
                style={{ borderColor: expanded ? color : undefined }}
              >
                <span className="hc-node-type">{row.type}</span>
                <span className="hc-node-name">{row.name}</span>
              </button>
              {row.via_edge && i < trail.length - 1 && (
                <span className="hc-edge" style={{ color }}>
                  ─{row.via_edge}→
                </span>
              )}
              {expanded && (
                <pre className="hc-raw">
                  {JSON.stringify(row, null, 2)}
                </pre>
              )}
            </li>
          );
        })}
      </ol>
      <p className="hc-hint">Click any node to see the raw row.</p>
    </div>
  );
}