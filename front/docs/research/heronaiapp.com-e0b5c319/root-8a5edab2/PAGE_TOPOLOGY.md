# Heron AI Home Page

- **Source:** `https://heronaiapp.com/`
- **Destination:** `/`
- **Viewport references:** `desktop-full.png`, `tablet-full.png`, `mobile-full.png`
- **Implementation:** local snapshot of the target's rendered body markup and Webflow stylesheet.

## Section order

1. Loading/initialization overlay and header navigation.
2. Hero with architectural illustration, percentage/Awwwards decoration, and company metadata.
3. Animated initialization/core-system list.
4. Building-code violation visualizer and discovery link.
5. Repeating marquee benefits: faster iterations, fewer mistakes, less busywork.
6. Intro statement and client/tool logos.
7. Problems section with four numbered problem cards.
8. Model/code-compliance visual section with violation callouts.
9. Introduction scroll narrative.
10. Connected-tools/platform section with Heron Chat Widget and Dashboard states.
11. Observe/Advise/Act/Learn process section.
12. Use cases and audience list.
13. Contact CTA, newsletter form, company/product/resource footer, and legal links.

The source uses a full-page scroll experience with Lenis/GSAP/Webflow behavior. The static snapshot preserves the exact DOM/CSS and visual states at load; external interaction scripts are intentionally not executed inside React markup.
