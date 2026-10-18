"""Locate exact byte ranges of elements in the captured HTML.

Why this exists
---------------
The captured file is NOT balanced — it carries several unclosed <div>s. So the
obvious approach, counting "<div" and "</div>" from an element's start until the
depth returns to zero, silently runs past that element's real end and eats the
rest of the document. That is exactly how the footer and the map / platform /
why / usecase sections got deleted from this file: the cut looked balanced and
was not, and nothing complained.

html.parser reports real positions and knows void elements, so a range derived
from it matches what a browser builds. Every cut is then checked against
SENTINELS before anything is written — if the footer or </main> would disappear,
the operation raises instead of shipping a truncated page.
"""

from __future__ import annotations

from html.parser import HTMLParser

# Structural things that must survive every edit. Losing any of these is how the
# page silently loses half its sections.
SENTINELS = {
    "</main>": 1,
    "<footer": 2,
    "home-map-wrap": 2,
    "home-why-wrap": 3,
    "home-usecase-wrap": 2,
    "home-problem-wrap": 3,
    "home-hero-wrap": 3,
}

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class Spans(HTMLParser):
    def __init__(self, src: str) -> None:
        super().__init__(convert_charrefs=False)
        self.src = src
        self.line_start = [0]
        for i, ch in enumerate(src):
            if ch == "\n":
                self.line_start.append(i + 1)
        self.spans: list[tuple[str, int, int]] = []
        self._stack: list[tuple[str, int]] = []

    # absolute offset of the parser's current position
    def _at(self) -> int:
        line, col = self.getpos()
        if line - 1 < len(self.line_start):
            return min(self.line_start[line - 1] + col, len(self.src))
        return len(self.src)

    def handle_starttag(self, tag, attrs):
        o = self._at()
        self._stack.append((tag, o))
        if tag in VOID:
            self.spans.append((tag, o, o))

    def handle_startendtag(self, tag, attrs):
        o = self._at()
        self.spans.append((tag, o, o))

    def handle_endtag(self, tag):
        o = self._at()
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                _, start = self._stack.pop(i)
                end = min(o + len(tag) + 3, len(self.src))
                # Record this element's own range. Inner elements are recorded
                # too and are NOT pruned — pruning them meant an ancestor's
                # close wiped every span inside it, which is why a plain div
                # never showed up in the results at all.
                self.spans.append((tag, start, end))
                return

    def parse(self) -> "Spans":
        self.feed(self.src)
        self.close()
        return self


CONTAINERS = {"div", "section", "footer", "main", "span", "a", "p", "li", "ul", "ol"}


def find_element(src: str, attr_marker: str, occurrence: int = 0) -> tuple[int, int]:
    """Byte range of the element whose opening tag contains attr_marker."""
    spans = Spans(src).parse().spans
    hits = 0
    for tag, start, end in spans:
        if tag not in CONTAINERS:
            continue
        if attr_marker in src[start : start + 500]:
            if hits == occurrence:
                return start, end
            hits += 1
    raise LookupError(f"{attr_marker!r} occurrence {occurrence} not found")


class Guard:
    """Aborts a write if a cut would take out anything structural."""

    def __init__(self, src: str) -> None:
        self.src = src

    def ok(self, candidate: str) -> None:
        bad = [
            f"{k} {self.src.count(k)}->{candidate.count(k)}"
            for k, v in SENTINELS.items()
            if candidate.count(k) < v
        ]
        if bad:
            raise AssertionError("refusing to write: cut would truncate -> " + "; ".join(bad))


def cut(src: str, attr_marker: str, label: str, occurrence: int = 0) -> str:
    start, end = find_element(src, attr_marker, occurrence)
    out = src[:start] + src[end:]
    Guard(src).ok(out)
    print(f"  cut {label:32} {start:>7}..{end:<7} {end - start:>7,}b  -> {len(out):,}")
    return out