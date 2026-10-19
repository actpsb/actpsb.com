# Contact backend: exception and operating runbook

This is the current state of the contact delivery integration. The supplied brief (`project-brief.md`) is unchanged; this document records the one backend exception the owner authorised: cPanel hosting, PHP, and authenticated SMTP for the contact form only. The rest of the site stays plain HTML, CSS and vanilla JavaScript with no frontend framework or build step. Visitors need no build; only the server needs `composer install`.

## What exists and what has been verified

Verified locally by `tests/test_contact_backend.py` against `php -S` and a local SMTP sandbox (`tests/smtp_sandbox.py`) that uses synthetic messages, a throwaway certificate and relays nothing:

- acceptance over STARTTLS and over implicit TLS; From is the configured mailbox, recipient is the configured value, the visitor address is Reply-To only
- rejected authentication, rejected recipient, unreachable server, untrusted certificate and host-name mismatch all give a generic "not sent" response and no success
- fail-closed behaviour with no configuration and with the placeholder template
- validation, header-injection rejection, size, method, content-type and same-origin checks, honeypot
- per-address and global rate limits, file-locked, including concurrent requests and the proxy trust boundary
- private log lines hold only a time, a request id and a fixed code

Not verified, because it has not been authorised or configured: a real cPanel account, the real mail server, real certificate chain, real DNS (SPF, DKIM, DMARC), and delivery to a real inbox. SMTP acceptance means the mail server took the message. It is not proof of inbox delivery, and the site says so. Until the checklist below is done and an authorised end-to-end test succeeds, live contact is not operational and the form reports itself unavailable.

## Behaviour

`contact.html` contains a real `<form method="post" action="contact-submit.php">`. Without JavaScript the browser posts natively and the server renders the result inside the normal contact page (`noindex`). With `assets/js/contact-form.js` the form posts with `fetch`, shows the server's result in the `#form-status` region and moves focus to it; field errors are linked and set `aria-invalid`. The script never decides success itself.

Responses: 200 accepted by SMTP; 422 validation errors; 429 rate limited (with `Retry-After`); 502 SMTP refused or unreachable; 503 not configured; 400 honeypot; 403 wrong origin; 405 wrong method; 413 too large; 415 wrong content type. Errors never include server names, credentials, library text or message content.

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
- Still unconfirmed: absolute home path, PHP version, exact live origin (`https://actpsb.com` is the template value; confirm www handling)

## Server layout (cPanel)

Everything except the public files lives outside `public_html`:

    /home/CPANELUSER/public_html/actpsb.com/   site files incl. contact.html, contact-submit.php, assets/ (document root shown by cPanel)
    /home/CPANELUSER/actp-backend/       backend/ contents: src/, vendor/, composer.json, composer.lock
    /home/CPANELUSER/actp-private/       config.php (chmod 600), var/ (rate-limit state, log; created 0700)

`contact-submit.php` resolves both from the account home. When the document root sits directly under a folder named `public_html` (as `/public_html/actpsb.com`), that home is two levels up, because `public_html` itself is web-served; otherwise they are siblings of the document root. Override with the `ACTP_BACKEND_DIR` and `ACTP_PRIVATE_DIR` environment variables if the layout differs. Do not upload `backend/` anywhere under `public_html`.

## Configuration

Copy `backend/config/config.example.php` to `actp-private/config.php`, chmod 600, replace every value. Any key can instead come from an `ACTP_*` environment variable, which takes precedence: `ACTP_SMTP_HOST`, `ACTP_SMTP_PORT`, `ACTP_SMTP_SECURE` (`tls` or `ssl`), `ACTP_SMTP_USER`, `ACTP_SMTP_PASS`, `ACTP_MAIL_FROM`, `ACTP_MAIL_FROM_NAME`, `ACTP_MAIL_TO`, `ACTP_ALLOWED_ORIGINS`, `ACTP_TRUSTED_PROXIES`, `ACTP_STATE_DIR`, `ACTP_SMTP_CA_FILE`, and `ACTP_RATE_IP_MAX/WINDOW`, `ACTP_RATE_GLOBAL_MAX/WINDOW`. Defaults: 5 per address per 600 s, 100 overall per 3600 s.

Rules the code enforces: TLS is always on with certificate and host-name verification; plaintext SMTP and `mail()` are not available; the recipient and From come only from configuration; `allowed_origins` must be https except localhost; `trusted_proxies` stays empty unless a proxy sits directly in front of PHP, in which case only the right-most untrusted `X-Forwarded-For` hop is used.

## Install steps (when authorised)

1. On a workstation: `cd backend && composer install --no-dev --optimize-autoloader` (PHP 8.1 or newer, `openssl` and `mbstring` extensions). Review `git status`: `vendor/` is ignored and must not be committed.
2. Upload `backend/{src,vendor,composer.json,composer.lock,licenses}` to `~/actp-backend/` and the site files plus `contact-submit.php` to `public_html`.
3. Create `~/actp-private/config.php` from the template with real values, `chmod 600`. Do not paste credentials into chat, tickets or git.
4. In cPanel, select PHP 8.1+ and confirm `openssl` and `mbstring` are enabled.
5. Run the authorised end-to-end test with a mailbox the owner controls, then read the message in that inbox. Record the result in the task, not in this file.

## Deployment configuration checklist (open items)

These are not confirmed and are not invented here:

- [ ] cPanel URL and account; PHP version available; whether SSH/Composer exists on the host (otherwise install on a workstation and upload `vendor/`)
- [ ] Confirm live origin (scheme and host, www or not) for `allowed_origins`; also unlocks canonical URLs and sitemap (see `seo.md`)
- [x] Mailbox, SMTP host/port/TLS and recipient: confirmed by owner (see above); password to be set by the owner on the server
- [ ] Absolute home path and PHP version
- [ ] DNS authentication for the sending domain (SPF, DKIM, DMARC), owner action
- [ ] Privacy notice wording and retention statement from ACTP. None is published; do not add placeholder claims.
- [ ] Whether a proxy or CDN sits in front of PHP (sets `trusted_proxies`)
- [ ] Authorised end-to-end inbox test and its recorded outcome

## Local development and tests

    cd backend && composer install
    ACTP_PHP=/path/to/php python3 -m unittest discover -s tests -v

PHP tests are skipped when `php` or `backend/vendor` is missing; CI installs both, lints the PHP files and runs everything.

## Limits worth knowing

CSRF protection is same-origin enforcement (`Origin` must match `allowed_origins`, `Sec-Fetch-Site` must be same-origin when sent) plus no cookies or sessions, so there is no ambient credential to forge. The rate limit is per client address and global, not a CAPTCHA; a determined distributed sender is bounded by the global cap rather than stopped. Messages are not stored on the server.
