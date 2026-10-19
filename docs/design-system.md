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
| `--color-muted` | `#667570` | Secondary text on canvas only |
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

Manrope headings, Inter body, font-display swap, preconnect only if remote font loading is chosen, robust system sans fallbacks and no render-blocking imports. Hero clamp(42px, 6vw, 80px), section titles clamp(32px, 4vw, 56px), card titles 22–28px, body 16–18px, labels 12–14px with sufficient contrast. Scale 8/16/24/32/48/64/80/96/120px; content max 1280px, reading measure ~680px. Vertical section padding 48–72 mobile, 72–96 tablet, 96–128 desktop. Break based on composition rather than arbitrary devices; no overflow at 320px.

## Interaction

Floating bounded sticky navigation, logo left, links/CTA right; mobile native button with aria-expanded and controlled menu; Escape closes, focus returns to trigger, outside dismissal and logical focus order; keep links accessible without JS. Visible focus, 44px touch targets. Hover 180–250ms, section reveal 500–700ms only on enhancement class activated by JS; content visible by default. `prefers-reduced-motion: reduce` removes movement and smooth scrolling. No scroll hijack or essential content obscured. Consistent accessible responsive header/footer across pages.
