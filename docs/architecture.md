# ACTP architecture, IA and delivery gates

As of 2026-10-19, the repository contains a coming-soon static page and CI; the following is the approved target, not a claim of implementation. Canonical request is `docs/project-brief.md`; installed implementer `dev-dexter` resolves brief's `dex-dexter`, and no shooshy profile exists.

## Information architecture

`index.html` (hero, company introduction, verified services/NSX explanation, illustrative approach, authentic empty insights, contact CTA, footer); `about.html` (verified identity/group relationship); `services.html` (verified ACTP role, qualify broader group offerings); `nsx-adviser.html` (role and NSX citation, no guarantee); `insights.html` (empty state until real approved publications); `contact.html` (verified NSX-listed group contact, accessible form only when delivery configured). Header links Home/About Us/Services/NSX Adviser/Insights/Contact. Never present unverified business copy as fact; source-check against `docs/content-sources.md`.

## Implementation contract

Plain HTML5, CSS3, modular vanilla JS without framework/build system. Keep flat HTML paths and existing logo; organize CSS/JS only where useful. Shared semantic navigation/footer pattern repeated in static pages, with automated link/headings/asset checks to catch drift. Progressive enhancement, keyboard/focus/Escape and reduced-motion. Contact form must not claim delivery without approved backend. On unavailable endpoint provide truthful unavailable/error state and verified contact links; defer only delivery integration, not other pages. No paid service enrollment or test enquiries. SEO titles/meta/OG, sitemap/robots with canonical URLs only when hosting origin confirmed. Document deployment instructions without deploying.

## Milestones and ordering

1. ACTP-001 evidence/brief; 002 IA; 003 palette; 004 typography. Planning gates precede code.
2. 005 structure/tests, 006 nav, 007–013 homepage sections, 014 interaction polish, then homepage functional/visual checkpoint in 018 before 015 secondary pages. Single linear dependency chain serializes shared CSS/HTML and main pushes.
3. 015 secondary pages, 016 isolated contact integration (may be blocked for backend while 017 SEO and later independent QA proceed), 017 SEO, 019 accessibility, 020 performance, 021 final visual/evidence review. Exact graph in cards; 018 performs first homepage QA before secondary pages.

## QA and integration

Every writing worker fetches origin/main and fast-forwards before editing; worktree base `/home/hermes/projects/actpsb.com`, no force push. Run configured stdlib tests/lint/type/build where configured, extend CI tests for pages, local links/assets/headings/nav/SEO; replace obsolete coming-soon assertions, remove tracked pycache and ignore generated caches. Push main only if allowed, confirm authenticated remote SHA and required CI passing for exactly that SHA. Dexter hands off evidence via review state to Chase, which is an evidence gate, not code/PR approval. Browser QA at 320/375/768/1024/1440 widths, JS disabled, keyboard, reduced motion, forms/errors; capture real measurements and limitations. Lighthouse target P90/A95/BP95/SEO95, never fabricate actual score. Accessibility target WCAG 2.2 AA. No publication/deployment/DNS change without required approval.

Business lanes map to Hermes native states: Backlog=`todo`; Ready for Development=`ready`; In Progress=`running`; Testing/QA=`review` (evidence verification only); Completed=`done`; Blocked=`blocked`. Additional runtime states remain system-defined. No Hermes core changes.
