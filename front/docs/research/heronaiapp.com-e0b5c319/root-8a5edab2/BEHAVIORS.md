# Heron AI Behavior Notes

## Navigation

- Desktop navigation exposes Product, nested product tools, Pricing, Resources, About, and Contact Us.
- Mobile navigation collapses behind `Menu` and expands to a full-screen menu.
- Link hover states are animated by the target Webflow/GSAP CSS.

## Page motion

- The target loads an initialization sequence before the main page settles.
- Lenis provides smooth scrolling.
- GSAP, ScrollTrigger, SplitText, and TextPlugin are loaded for scroll and text animation.
- The hero and model sections contain scroll-driven visual progress and code-violation callouts.
- The target includes a click-on-violation interaction in the model section.

## Responsive states

- `1440px`: desktop navigation and multi-column content layouts.
- `768px`: tablet layout with reduced typography and adjusted section widths.
- `390px`: menu button, stacked sections, expanded violation copy, and single-column footer.

## Snapshot behavior

The clone preserves the target's rendered markup, inline component CSS, downloaded stylesheet, text, SVGs, and visual assets. Browser-side third-party analytics and runtime scripts are not executed from the imported markup.
