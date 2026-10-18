"use client";

/**
 * Client for the frozen Helio API.
 *
 * The contract is POST /ask returning SSE frames of {answer, trail[], stale[]}.
 * It is frozen, so this mirrors it exactly rather than inventing a shape:
 *
 *   trail[] row -> {type, name, detail, date, via_edge}   every field, always
 *   via_edge    -> a closed 14-value vocabulary
 *
 * The one thing worth defending is the frame handling. The server sends a FULL
 * SNAPSHOT on every frame, not a delta. A handler that appends per frame renders
 * 12 chips where there are 6 — invisible against a fixture, and only visible
 * against the real backend. Hence: replace, never append.
 */

export const API_URL =
  process.env.NEXT_PUBLIC_HELIO_API ?? "https://helio-brain.onrender.com";

export interface TrailRow {
  type: string;
  name: string;
  detail: string;
  date: string;
  via_edge: string;
}

export interface StaleRow {
  type: string;
  name: string;
  detail?: string;
  date?: string;
  [k: string]: unknown;
}

export interface Frame {
  answer: string;
  trail: TrailRow[];
  stale: StaleRow[];
}

export interface AskState {
  status: "idle" | "streaming" | "done" | "error";
  answer: string;
  /** Full snapshot, replaced each frame. Never accumulated. */
  trail: TrailRow[];
  stale: StaleRow[];
  error?: string;
}

const IDLE: AskState = { status: "idle", answer: "", trail: [], stale: [] };

export async function ask(
  question: string,
  onFrame: (s: AskState) => void,
  signal?: AbortSignal,
): Promise<void> {
  onFrame({ ...IDLE, status: "streaming" });

  let res: Response;
  try {
    res = await fetch(`${API_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
      signal,
    });
  } catch {
    // A bare "Failed to fetch" here is almost always an origin/CORS mismatch
    // rather than a dead backend, so say so instead of showing a dead button.
    onFrame({
      ...IDLE,
      status: "error",
      error:
        "Could not reach the Helio API. If this is a browser origin problem, add this site's origin to the API's CORS allowlist.",
    });
    return;
  }

  if (!res.ok || !res.body) {
    onFrame({ ...IDLE, status: "error", error: `The API returned HTTP ${res.status}.` });
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let latest: AskState = { ...IDLE, status: "streaming" };

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE frames are separated by a blank line. A partial frame must stay in
      // the buffer — splitting on every chunk truncates JSON mid-object.
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        for (const line of part.split("\n")) {
          if (!line.startsWith("data:")) continue;
          const raw = line.slice(5).trim();
          if (!raw || raw === "[DONE]") continue;

          let payload: Frame;
          try {
            payload = JSON.parse(raw);
          } catch {
            continue; // a half-written frame; the next carries it
          }

          // REPLACE, not append. See the note at the top of this file.
          latest = {
            status: "streaming",
            answer: payload.answer ?? "",
            trail: payload.trail ?? [],
            stale: payload.stale ?? [],
          };
          onFrame(latest);
        }
      }
    }
  } catch (e) {
    if ((e as Error)?.name === "AbortError") {
      onFrame({ ...latest, status: "done" });
      return;
    }
    onFrame({ ...latest, status: "error", error: String(e) });
    return;
  }

  onFrame({ ...latest, status: "done" });
}

/**
 * Validate rows against the frozen contract.
 *
 * An unexpected via_edge renders wrong and nobody notices. This is a canary, not
 * a fix: it never corrects anything, it only tells the first person to hit drift
 * WHICH field is wrong.
 */
const VIA_EDGE_VOCABULARY = new Set([
  "OWNED_BY", "DEPENDS_ON", "HAS_DEPENDENT", "SUPERSEDES", "EVIDENCED_BY",
  "MENTIONS", "REPORTS_TO", "MEMBER_OF", "CONTRIBUTED_TO", "WORKED_ON",
  "PARTICIPATED_IN", "ON_CALL", "ROTATED_IN", "AUTHORED_BY",
]);

export function validateContract(trail: TrailRow[]): string[] {
  const problems: string[] = [];
  trail.forEach((row, i) => {
    // Index 0 is exempt: the chain start legitimately carries no edge.
    if (i > 0 && row.via_edge && !VIA_EDGE_VOCABULARY.has(row.via_edge)) {
      problems.push(`trail[${i}].via_edge "${row.via_edge}" is outside the vocabulary`);
    }
    for (const field of ["type", "name", "detail"] as const) {
      if (row[field] === undefined) problems.push(`trail[${i}].${field} is missing`);
    }
    if (row.date !== undefined && typeof row.date !== "string") {
      problems.push(`trail[${i}].date must be a string`);
    }
  });
  return problems;
}