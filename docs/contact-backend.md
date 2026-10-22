# Contact backend: exception and operating runbook

This is the current state of the contact delivery integration. The supplied brief (`project-brief.md`) is unchanged; this document records the one backend exception the owner authorised: cPanel hosting, PHP, and authenticated SMTP for the contact form only. The rest of the site stays plain HTML, CSS and vanilla JavaScript with no frontend framework or build step. Visitors need no build; only the server needs `composer install`.

## What exists and what has been verified

Verified locally by `tests/test_contact_backend.py` against `php -S` and a local SMTP sandbox (`tests/smtp_sandbox.py`) that uses synthetic messages, a throwaway certificate and relays nothing:

- acceptance over STARTTLS and over implicit TLS; From is the configured mailbox, recipient is the configured value, the visitor address is Reply-To only
- rejected authentication, rejected recipient, unreachable server, untrusted certificate and host-name mismatch all give a generic "not sent" response and no success
- fail-closed behaviour with no configuration and with the placeholder template
- validation, a required five-value enquiry category allowlist, header-injection rejection, size, method, content-type and same-origin checks, honeypot
- per-address and global rate limits, file-locked, including concurrent requests and the proxy trust boundary
- private log lines hold only a time, a request id and a fixed code

Not verified, because it has not been authorised or configured: a real cPanel account, the real mail server, real certificate chain, real DNS (SPF, DKIM, DMARC), and delivery to a real inbox. SMTP acceptance means the mail server took the message. It is not proof of inbox delivery, and the site says so. Until the checklist below is done and an authorised end-to-end test succeeds, live contact is not operational and the form reports itself unavailable.

## Behaviour

`contact.html` holds the real `<form method="post" action="contact-submit.php">` inside `<template id="enquiry-form-template">`. JavaScript reveals its fields immediately, even in a local preview without SMTP configuration. Without JavaScript, the availability notice (`#form-availability`) links to the server-rendered form. Sending still fails closed on the backend when configuration is missing, invalid or explicitly disabled.

- Preflight: `GET contact-submit.php?preflight=1` returns `{"available": true}` (200) when private configuration loads, validates and does not explicitly disable the form, else `{"available": false}` (503). Existing configurations without `form_enabled` remain enabled for backward compatibility. Setting `form_enabled: false` or `ACTP_FORM_ENABLED=0` disables submission; the example template is explicitly disabled until an authorised end-to-end test. Preflight never contacts the mail server, sends visitor data or reveals configuration values; it is not a live health check.
- With JavaScript, `assets/js/contact-form.js` immediately replaces the notice with the form fields; displaying the form does not depend on SMTP availability. Submission uses `fetch`, shows the server's result in `#form-status` and moves focus to it; field errors are linked and set `aria-invalid`. The script never decides success itself. The preflight endpoint remains available for diagnostics.
- Without JavaScript, the notice links to `contact-submit.php?form=1`. That route renders the contact page with the form when configured, or with the 503 unavailable alert and no form when not. Native POSTs render the result inside the normal contact page (`noindex`).

The required Nature of Enquiry choices are NSX Nominated Adviser, IPO & Capital Markets, Corporate Advisory, Mergers & Acquisitions and General Enquiry. The validated choice is included in the plain-text UTF-8 email, never used to select a recipient or create a visitor-controlled header. Native error responses preserve the selected option. Successful SMTP acceptance returns "Thank you. Your enquiry has been submitted successfully." This does not claim inbox arrival or human review. Network/transport uncertainty asks visitors to use the published channels before resubmitting; it does not claim nothing was delivered.

Response contract (JSON, requested with `Accept: application/json`): `{status, message, errors, reference}`, where `status` is `accepted` (HTTP 200 only), `invalid` (422, per-field `errors`), `failed` (502, SMTP stage), `rejected` (400/403/405/413/415), `rate_limited` (429) or `unavailable` (503). The script (`interpret()` in `contact-form.js`, unit-tested under node) treats a body as an answer only when it is JSON with a known `status`. Success needs HTTP 200 plus `accepted`. A non-JSON or HTML body with HTTP 4xx or 503 (an older deployed endpoint, a missing backend, a proxy refusal) is shown as not sent, with the HTTP status. Network errors, timeouts and every other unreadable response (including HTTP 200 HTML) show "We could not confirm your submission" with the published channels. The script validates input with the server's rules before sending (10 to 5000 character message, valid email, allowed category), submits at most once per click, and never retries automatically. The server revalidates every field, so native no-JS posts and older cached scripts get the same 422 errors. Older deployed backends are compatible because the script reads only `status`, `message`, `errors` and `reference`, and tolerates the last two being absent.

Public contact details now consistently use NSX's published group email `contact@arris.com.my`, phone `+60 3 8076 3063` and the Puchong address, with group attribution. The owner-supplied `contact@actpsb.com` remains the intended private SMTP mailbox, not a verified operational public channel. No existing privacy-policy page was found; the Contact page includes only a brief enquiry-purpose notice, without an invented URL or retention promise.

Tests: `tests/test_contact_backend.py` `PreflightTests` (PHP-driven) and `tests/test_site.py` `test_contact_accessible_and_truthful`.

Responses: 200 accepted by SMTP; 422 validation errors; 429 rate limited (with `Retry-After`); 502 SMTP refused or unreachable; 503 not configured (also the preflight and `?form=1` response); 400 honeypot; 403 wrong origin; 405 wrong method; 413 too large; 415 wrong content type. Errors never include server names, credentials, library text or message content.

## Files

- `contact-submit.php`: public entry point, wiring only, no secrets
- `backend/src/`: `Handler`, `Config`, `Validator`, `RateLimiter`, `ClientIp`, `SmtpSender` (PHPMailer), `Page`, `EventLog`
- `backend/composer.json`, `backend/composer.lock`: PHPMailer pinned to 6.12.0 (LGPL-2.1; licence copy in `backend/licenses/`)
- `backend/config/config.example.php`: non-secret placeholder template. Placeholders fail validation by design.
- `assets/js/contact-form.js`, `assets/css/contact-form.css`: contact-page-only enhancement and styles

## Owner-confirmed mail settings (non-secret)

- SMTP host `mail.actpsb.com`, port 465, implicit TLS/SMTPS with certificate verification, authentication required
- Username `contact@actpsb.com`; the same mailbox is both From and the enquiry recipient; the visitor address is Reply-To only
- The owner sets the mailbox password directly on the server; it is never in chat, git or this repository
- Domain exists in cPanel; its document root is shown as `/public_html/actpsb.com`
- PHP: owner reports actpsb.com is set to PHP 8.3 (ea-php83) in cPanel, replacing an inherited 7.2. This is owner-reported and not independently verified; confirm during installation (step 4)
- Owner-created paths: home `/home/arriscom`, backend `/home/arriscom/actpsb-backend`, private `/home/arriscom/actpsb-private`, document root `/home/arriscom/public_html/actpsb.com`. Use these exact names; no renaming or environment variables are needed because `contact-submit.php` defaults to them
- Owner reports `/home/arriscom/actpsb-private` is set to mode 0700 (owner-reported). The owner performs cPanel setup manually; no cPanel access is given to the agent
- Still unconfirmed: exact live origin (`https://actpsb.com` is the template value; confirm www handling)

## Server layout (cPanel)

Everything except the public files lives outside `public_html`:

    /home/arriscom/public_html/actpsb.com/   site files incl. contact.html, contact-submit.php, assets/ (document root shown by cPanel)
    /home/arriscom/actpsb-backend/       backend/ contents: src/, vendor/, composer.json, composer.lock
    /home/arriscom/actpsb-private/       config.php (chmod 600), var/ (rate-limit state, log; created 0700)

`contact-submit.php` resolves both from the account home. When the document root sits directly under a folder named `public_html` (as `/public_html/actpsb.com`), that home is two levels up, because `public_html` itself is web-served; otherwise they are siblings of the document root. Override with the `ACTP_BACKEND_DIR` and `ACTP_PRIVATE_DIR` environment variables if the layout differs. Do not upload `backend/` anywhere under `public_html`.

## Configuration

Copy `backend/config/config.example.php` to `actpsb-private/config.php`, chmod 600, replace every placeholder and keep `form_enabled` false until the authorised test is complete. Set it to the boolean `true` only after verification. Any key can instead come from an `ACTP_*` environment variable, which takes precedence: `ACTP_FORM_ENABLED` (`1` enables, `0` disables), `ACTP_SMTP_HOST`, `ACTP_SMTP_PORT`, `ACTP_SMTP_SECURE` (`tls` or `ssl`), `ACTP_SMTP_USER`, `ACTP_SMTP_PASS`, `ACTP_MAIL_FROM`, `ACTP_MAIL_FROM_NAME`, `ACTP_MAIL_TO`, `ACTP_ALLOWED_ORIGINS`, `ACTP_TRUSTED_PROXIES`, `ACTP_STATE_DIR`, `ACTP_SMTP_CA_FILE`, and `ACTP_RATE_IP_MAX/WINDOW`, `ACTP_RATE_GLOBAL_MAX/WINDOW`. Defaults: 5 per address per 600 s, 100 overall per 3600 s.

Rules the code enforces: TLS is always on with certificate and host-name verification; plaintext SMTP and `mail()` are not available; the recipient and From come only from configuration; `allowed_origins` must be https except localhost; `trusted_proxies` stays empty unless a proxy sits directly in front of PHP, in which case only the right-most untrusted `X-Forwarded-For` hop is used.

## Install steps (File Manager only; when authorised)

Download the `actpsb-cpanel-<commit SHA>` artifact from a successful [CI run](https://github.com/actpsb/actpsb.com/actions/workflows/ci.yml) and unzip that download on your computer to obtain the three upload ZIPs below. CI installs the locked dependencies, runs the backend/sandbox and extracted-package tests, then builds and publishes these packages. Artifacts expire after 30 days; the exact commit SHA identifies their source. The three ZIPs are also supplied as task attachments for the reviewed handoff.

The host has no cPanel Terminal, so nothing runs on the server except PHP serving the site. For a manual workstation build, use `ACTP_PHP=/path/to/php ACTP_COMPOSER=/path/to/composer.phar python3 scripts/build_packages.py`, which writes three ZIPs to `dist/` (git-ignored, contain no secrets, no `.git`, tests, docs or installers; Composer dependencies are already installed in the backend ZIP):

- `actpsb-public.zip`: site pages, `assets/`, `robots.txt`, `contact-submit.php`
- `actpsb-backend.zip`: `src/`, `vendor/` (PHPMailer 6.12.0, locked), `licenses/`
- `actpsb-private.zip`: `config.example.php` template only (password placeholder only; never `config.php`)

CI also publishes `MANIFEST.json` (source SHA, SHA-256 and members of each ZIP, locked dependency versions) and `SHA256SUMS.txt` beside the ZIPs. Upgrade and rollback: see [upgrade-rollback.md](upgrade-rollback.md).

Steps in cPanel File Manager:

1. Upload and Extract `actpsb-public.zip` into `/home/arriscom/public_html/actpsb.com`.
2. Upload and Extract `actpsb-backend.zip` into `/home/arriscom/actpsb-backend` (outside `public_html`).
3. First install only: Upload and Extract `actpsb-private.zip` into `/home/arriscom/actpsb-private` (keep the folder at 0700), copy `config.example.php` to `config.php`, open `config.php` in the editor, replace only `CONFIRM_SET_PASSWORD_ON_SERVER_ONLY` with the mailbox password, confirm `allowed_origins` matches the live origin, save, and set the file to 0600. Do not paste the password in chat, tickets or git.
4. In MultiPHP Manager confirm actpsb.com runs PHP 8.3 and in the PHP extensions list confirm `openssl` and `mbstring` are enabled. There is no browser-accessible installer and none is needed.
5. In a staging or maintenance environment, explicitly enable the form and run the authorised end-to-end test with a mailbox the owner controls; verify receipt in that inbox. Record the result in the task, not in this file. Enable `form_enabled` on the public site only after that test succeeds; disable it again if verification fails.

Until configuration is valid and is not explicitly disabled, the endpoint stays unavailable and sends nothing. Existing working configurations need no new enable flag. Local tests (`PackageTests`) extract the built ZIPs into a simulated `/home/arriscom` layout and verify fail-closed as shipped and acceptance after a synthetic config edit; the real host has not been touched.

## Deployment configuration checklist (open items)

These are not confirmed and are not invented here:

- [ ] cPanel URL and account; PHP version available; whether SSH/Composer exists on the host (otherwise install on a workstation and upload `vendor/`)
- [ ] Confirm live origin (scheme and host, www or not) for `allowed_origins`; also unlocks canonical URLs and sitemap (see `seo.md`)
- [x] Mailbox, SMTP host/port/TLS and recipient: confirmed by owner (see above); password to be set by the owner on the server
- [x] Home path `/home/arriscom` (owner-confirmed)
- [x] No cPanel Terminal (owner-confirmed); vendor/ ships inside the backend ZIP
- [ ] Verify PHP 8.3 and extensions on the live runtime (PHP 8.3 is owner-reported only)
- [ ] DNS authentication for the sending domain (SPF, DKIM, DMARC), owner action
- [ ] ACTP approval of the brief enquiry-purpose privacy notice and any fuller policy/retention statement. No existing privacy-policy page was found; no policy URL or retention period is invented.
- [ ] Whether a proxy or CDN sits in front of PHP (sets `trusted_proxies`)
- [ ] Authorised end-to-end inbox test and its recorded outcome

## Local development and tests

    cd backend && composer install
    ACTP_PHP=/path/to/php python3 -m unittest discover -s tests -v

PHP tests are skipped when `php` or `backend/vendor` is missing; CI installs both, lints the PHP files and runs everything.

## Limits worth knowing

CSRF protection is same-origin enforcement (`Origin` must match `allowed_origins`, `Sec-Fetch-Site` must be same-origin when sent) plus no cookies or sessions, so there is no ambient credential to forge. The rate limit is per client address and global, not a CAPTCHA; a determined distributed sender is bounded by the global cap rather than stopped. Messages are not stored on the server.
