# ACTP design direction (2026-10-19)

Design authority: supplied logo at `assets/actp-logo.png` (841×284); preserve the original. Shooshy unavailable; Chase specifies and Dexter implements. Editorial corporate advisory, not a generic card grid: open off-white canvas, asymmetrical two-column hero, forest services field, restrained typographic NSX explainer, timeline, honest insights empty state, teal contact field. Original logo-inspired geometric linework is preferable to unlicensed stock or invented people/offices. No gold/navy. Alternate scale, rhythm and composition across sections.

## Color evidence and tokens

### Reproducible logo sampling and provisional palette

The original `assets/actp-logo.png` is 841×284, 8-bit sRGB RGB. To reproduce the sample, decode PNG IDAT with zlib, reverse each PNG scanline filter (or read pixels with browser canvas `getImageData`), select `g > 1.25*r && b > 1.1*r && r < 175`, and quantise each selected channel using `Math.floor(channel / 16) * 16`. The original asset yields 72,047 selected pixels out of 238,844, with leading buckets `(0,144,128): 8,362`, `(0,112,112): 8,296`, `(0,96,96): 6,740`, `(0,128,112): 6,111`, `(0,128,128): 4,761`. White background accounts for 136,709 exact-white pixels. These gradient/antialias samples establish a hue family, not official ACTP swatches. UI colours below are provisional accessibility adaptations, not a claimed official brand standard.

| CSS property | Hex | Role |
|---|---|---|
| `--color-forest` | `#004D45` | Deep section, primary CTA |
| `--color-forest-dark` | `#003B36` | Footer, CTA hover, dark ink |
| `--color-teal` | `#008F83` | Accent/contact field; not normal text on light |
| `--color-emerald` | `#00A896` | Decorative accent, not white-text button fill |
| `--color-bright-teal` | `#39BDAA` | Dark-field focus accent |
| `--color-canvas` | `#F8FAF9` | Main background |
| `--color-soft` | `#F1F5F3` | Alternate light surface |
| `--color-white` | `#FFFFFF` | White surface and reverse text |
| `--color-text` | `#1C2926` | Light-surface body |
| `--color-muted` | `#5f6e69` | Secondary text on canvas, soft and white surfaces (4.87:1 on soft, 5.11:1 on canvas) |
| `--color-line` | `#DCE6E2` | Decorative separator, not sole control boundary |

WCAG contrast computation: convert hex sRGB channels to fractions of 255; linearise at 0.04045 (divide by 12.92 below the threshold, otherwise `((c + 0.055)/1.055)^2.4`); luminance weights are 0.2126/0.7152/0.0722; ratio is `(lighter + 0.05)/(darker + 0.05)`. Values below are rounded to two decimals. WCAG 2.2 AA thresholds: normal text 4.5:1, large text (24px regular or 18.66px bold) 3:1, meaningful non-text UI and focus indicator against adjacent colours 3:1. Large-text eligibility does not include small button labels.

| Foreground / background | Ratio | Usage / exception |
|---|---:|---|
| Text / canvas | 14.37:1 | Normal text |
| Muted / canvas | 4.61:1 | Secondary normal text; do not reduce opacity |
| Forest / canvas | 9.33:1 | Light-field heading/link |
| White / forest | 9.78:1 | Solid CTA and dark-field body |
| White / forest-dark | 12.51:1 | Dark hover CTA/footer |
| Teal / canvas | 3.81:1 | Large text/non-text only; normal text fails |
| White / teal | 3.99:1 | Large text only; button labels/body fail |
| Forest-dark / teal | 3.13:1 | Large text/non-text only; body fails |
| White / emerald | 2.98:1 | Fails even large text |
| Forest-dark / emerald | 4.19:1 | Large text only |
| Forest-dark / bright-teal | 5.38:1 | Normal text passes |
| Bright-teal / forest-dark | 5.38:1 | Dark-field focus ring |
| Teal / white | 3.99:1 | Normal-size link fails |
| White / line | 1.28:1 | Never text or sole control border |

Button pairings: forest fill/white label, changing to forest-dark/white on hover. On forest or dark fields, white fill/forest-dark label or transparent fill with white label and white border. On teal fields, use forest-dark fill/white label; place normal-size field text on an opaque white or forest-dark panel, or change the field itself to forest-dark. Do not use white body text directly on teal. Light-field links use forest plus underline; dark-field links use white plus underline, so state is never colour-only. Verify disabled, hover, pressed and overlay surfaces separately.

Focus pairings: use a 3px solid forest-dark outline with 2px offset on canvas/white/soft light fields (forest-dark/white 12.51:1; forest-dark/canvas 11.93:1); a 3px bright-teal outline with 2px offset on forest/forest-dark fields (bright-teal/forest-dark 5.38:1; bright-teal/forest 4.21:1); and forest-dark outline with 2px offset on teal (3.13:1). The offset exposes the field between button edge and ring. On mixed imagery or overlays, supply an opaque backing or two-tone ring and remeasure adjacent colours; token-level contrast does not certify a finished component.

Editorial colour distribution guideline: approximately 70–80% white/off-white/soft, 15–25% forest/dark (services/footer), at most 5–10% teal/emerald accent including a deliberate contact moment. These are compositional targets, not pixel quotas. Avoid large bright gradients, gold and navy; keep the original logo untouched.

## Typography and spacing

The following roles and tokens replace the preliminary ranges. Keep the 1280px content cap, approximately 680px reading measure, and no horizontal overflow at 320px.

### Type implementation contract

Use Manrope 500/600/700 for headings and Inter 400/500/600 for text. Prefer locally hosted, licensed WOFF2 subsets when available, with `@font-face` and `font-display: swap`; declare actual weight descriptors to avoid synthetic bold. Do not commit downloaded font files without checking redistribution rights. If local fonts are unavailable, use a provider stylesheet link with `display=swap`, preconnect to stylesheet and font origins (`crossorigin` on the font origin), and avoid CSS `@import`. Preload only a locally hosted above-the-fold Manrope face if measurement warrants it. Fallback immediately to `Arial, Helvetica, sans-serif` for headings and `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif` for body. Test wrapping in both states, without hiding text during loading.

| Role | Fluid size | Weight / line-height | Tracking / measure |
|---|---|---|---|
| Hero H1 | `clamp(42px, 5.6vw, 80px)` | 700 / 1.08–1.14 | `-0.035em`; approximately 12–15ch |
| Section H2 | `clamp(32px, 3.8vw, 56px)` | 600–700 / 1.14–1.22 | `-0.025em`; approximately 18–22ch |
| Subheading H3 | `clamp(22px, 2vw, 28px)` | 600 / 1.25–1.35 | `-0.015em`; no fixed-height cards |
| Lead | `clamp(17px, 1.4vw, 18px)` | 400 / 1.6 | normal; max 680px |
| Body | `clamp(16px, 1.2vw, 18px)` | 400 / 1.6–1.7 | normal; max 680px |
| Eyebrow / metadata | `clamp(12px, 1vw, 14px)` | 600 / 1.4–1.5 | `0.06em` optional; short labels only |

Interactive labels are at least 16px/1.4; 12–14px is reserved for short nonessential metadata. Keep paragraph measure roughly 45–75 characters where space permits; at 320px accept shorter lines rather than shrinking type. Use 16–24px between paragraphs and from headings to copy, 16px between eyebrow and heading. Allow 200% text zoom and font-size overrides: avoid fixed-height text containers, forced line breaks and nowrap prose; wrap long URLs instead of shrinking text.

### Layout tokens and responsive composition

Use the 8px rhythm: `--space-1: 8px`, `--space-2: 16px`, `--space-3: 24px`, `--space-4: 32px`, `--space-6: 48px`, `--space-8: 64px`, `--space-10: 80px`, `--space-12: 96px`, `--space-15: 120px`. Reserve 4px for optical adjustment, not major layout. Set `--container-max: 1280px` and `--reading-max: 680px`. Container inner width is `min(1280px, 100% - 2 * gutter)` with auto inline margins; reading blocks use width 100% and max-width 680px. Gutters: 16px below 480px, 24px at 480px, 32px at 768px, 40px at 1280px. At 320px the inner width is 288px. Use `minmax(0, 1fr)` for flexible columns and constrain images to their containers.

Mobile-first section block padding: 48px at 320–479px, 64px at 480–767px, 80px at 768–1023px, 96px at 1024–1279px, 120px at 1280px and wider. Adjacent backgrounds may alternate without redundant spacer blocks. Column gaps: 24px mobile, 32px tablet, 48–64px desktop. Use Grid for major columns and Flexbox for CTA rows.

Break at 480/768/1024/1280px only when composition needs it. Below 768px stack editorial pairs with text before decorative imagery in DOM order; let CTA rows wrap and provide 44px minimum target height. At 768–1023px retain stacking unless both text measure and imagery have room. At 1024px use an asymmetric approximately 55/45 hero; alternate image placement visually without changing reading order. Above 1280px cap inner content while background fields span the viewport. Avoid viewport-width elements plus gutters. Check 320, 375, 768, 1024 and 1440px and 200% zoom for heading/menu/button wrapping, imagery clipping, focus visibility and horizontal overflow.

Homepage composition follows `architecture.md`: bounded floating navigation; off-white hero with H1 “ACTP Sdn Bhd”, conservative NSX role copy, two real route CTAs and optional logo-derived abstract visual; airy company introduction with a reading-width copy column; forest services field showing verified role information in editorial rows, not an unverified service catalogue; restrained NSX explainer with official source link; optional clearly labelled illustrative process in horizontal desktop/vertical mobile sequence; honest insights empty state; teal contact moment with opaque high-contrast text panel and real contact route; dark footer. Keep one H1 and sequential H2 headings. Do not visually reverse DOM reading order.

### Motion and progressive enhancement

Under `prefers-reduced-motion: reduce`, remove smooth scrolling, reveal transforms and animated navigation/imagery, but keep immediate state changes and visible focus. Essential text and links remain visible without JavaScript; apply reveal classes only after enhancement initializes and restore visible state if observation fails. Never animate layout-changing font size or hijack scrolling. Rendered QA must cover fallback-font reflow, reduced motion and keyboard focus. This is a testable specification, not a claim that the current coming-soon page already meets it.

## Interaction

Floating bounded sticky navigation, logo left, links/CTA right; mobile native button with aria-expanded and controlled menu; Escape closes, focus returns to trigger, outside dismissal and logical focus order; keep links accessible without JS. Visible focus, 44px touch targets. Hover 180–250ms, section reveal 500–700ms only on enhancement class activated by JS; content visible by default. `prefers-reduced-motion: reduce` removes movement and smooth scrolling. No scroll hijack or essential content obscured. Consistent accessible responsive header/footer across pages.
