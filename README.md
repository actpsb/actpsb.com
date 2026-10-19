# actpsb.com

ACTP website — actpsb.com. Plain HTML5, CSS3 and vanilla JavaScript for the site itself: no frontend framework, package manager or build step. The one approved backend exception is the contact form's PHP endpoint (`contact-submit.php`, `backend/`), which sends mail through authenticated SMTP with PHPMailer; see `docs/contact-backend.md`. The contact form fails closed: `contact.html` shows an unavailable notice and keeps the form inert inside a `<template>`; the form is revealed only when the server preflight (`contact-submit.php?preflight=1`) reports valid private configuration. Contact is not operational until the runbook checklist and an owner-run inbox test are done.

## Structure

    index.html            semantic homepage shell (skip link, header, main, footer)
    assets/actp-logo.png  original logo, unmodified (841x284); pages serve assets/actp-logo-432.png (432x146)
    assets/css/
      tokens.css          design tokens (palette, type scale, 8px spacing, breakpoints)
      base.css            reset, element defaults, focus, reduced motion
      layout.css          container, reading measure, section blocks, skip link
      components.css      header/logo, eyebrow, lead, buttons, footer
    assets/js/main.js     progressive-enhancement entry (deferred; site works without it)
    assets/js/contact-form.js, assets/css/contact-form.css   contact page only: availability preflight and fetch submit
    contact-submit.php    same-origin POST endpoint for the contact form (PHP, wiring only)
    backend/              PHP contact backend: src/, composer.json + lock, config template, licences
    docs/                 brief, content sources, design system, architecture, contact-backend runbook
    tests/test_site.py    stdlib unittest harness

New pages reuse the same four stylesheets and shell. Add new tokens to `tokens.css`, new patterns to `components.css`.

## Test

    python -m unittest discover -s tests -v

The suite checks metadata, landmarks, one H1, logo integrity, token values against `docs/design-system.md`, stylesheet/script wiring, local link resolution, absence of framework tooling, repo hygiene, CI triggers (push to main and pull_request) and serves the site over a local HTTP server.

PHP-driven backend tests need `php` and `backend/vendor` (set `ACTP_PHP`); otherwise they are skipped and CI runs them. Rendered responsive/browser QA at 320/375/768/1024/1440px is not covered by these tests; see `docs/qa/`.
