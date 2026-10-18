# Helio site — TODO

Status legend: `[ ]` open · `[~]` in progress · `[x]` done

Ordered by "removes noise first", then the layout work, then the rewrite.

## 1. Remove what isn't ours

- [x] **"Site of the Day" badge** — awwwards widget, bottom-right, third-party.
      Not ours, not relevant, and it is a link to another site's profile.
      Remove the markup and the controller that injects it.
- [x] **Cookie banner** — we set no cookies and run no analytics. A consent
      banner for nothing is worse than no banner: it claims a data practice we
      do not have. Remove the markup and its controller.
- [ ] **Floor-plan imagery** (the "TOWER FLOOR PLAN / RESIDENTIAL FLOOR PLAN"
      sheets and the IBC 1020.2 code panel) — architectural drawings from the
      reference product. Says nothing about a company knowledge graph.
      Remove.
- [x] **Footer** — currently the reference site's sitemap, address and policy
      links with our words dropped in. Replace wholesale with our own: no
      copied structure, no inherited links, nothing pointing at their routes.
      (Done: removed Social column — bear.plus/dribbble/FWA/awwwards/instagram/
      linkedin — the Sydney address + maps/Direction links, and the Privacy/
      Terms/Cookie policy row (those routes don't exist). Address item rewritten
      to a neutral "Location: Distributed / remote". Zero external hrefs remain
      in the document. Kept the Helio Company/Product/Resources menus + copyright.)

## 2. Fix what is visibly broken

- [ ] **Problems section — overlapping text.** "A DIRECTORY TELLS YOU WHO
      EXISTS. IT NEVER TELLS YOU WHAT BREAKS." is rendering on top of the
      building image instead of below it. Heading, image and copy are fighting
      for the same grid cells.
- [ ] **Problems pagination only advances two steps.** Four items
      (MANUAL / DISJOINTED / BLIND / SLOW) and the scroll controller stops
      after the second — the last two are unreachable by scroll.
- [ ] **"FOR THE WHOLE DESIGN" / "RIGHT THERE WITH YOU"** — both headings sit in
      one enormous dead zone. Each should own a full viewport (100vh) and swap
      as you scroll, so the section reads as a sequence rather than a void.
- [ ] **Nav — oversized cells.** The desktop nav is a two-row grid roughly
      120px tall with oversized hit areas; the header eats a third of a laptop
      viewport and pushes every section down. Rebuild it as a single compact
      row.

## 3. Make it our product site

- [ ] **Replace the architecture imagery.** The hero is a photorealistic
      building and the sections are floor plans and material studies. All of it
      belongs to a different product. A company knowledge graph should look
      like a graph.
- [ ] **Replace the remaining reference copy.** Section headings and body text
      still describe architecture ("building code compliance", "hand the
      repetitive modelling"). Every section should describe what Helio actually
      does: traversal, provenance, refusal.
- [ ] **Section order should follow the argument.** Problem → how it works →
      proof → demo. Right now it follows the reference site's order.

## 4. Ship

- [ ] Deploy with a domain, then add that origin to the backend's
      `CORS_ALLOW_ORIGINS` or `/demo` will fail cross-origin.
- [ ] Point `front/` at a remote under our account. It is currently a clone of
      `sourav9823/heronaiapp` and must not be pushed there.