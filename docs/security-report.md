# Security audit report (ACTP-024)

Audited commit: 48d2a7d (main) plus this change. Audit date: 2026-10-22. No secret values appear here, only paths, types and commit IDs. No production writes were made.

## Summary

| # | Finding | Severity | Status |
|---|---------|----------|--------|
| 1 | Production serves `/backend/`, `/docs/`, `/tests/`, `/scripts/`, `/README.md` (HTTP 200) | High (information exposure) | Open. Owner action; rules and guide supplied |
| 2 | PHP runtime patch level, SAPI and OS unknown | Unresolved | Owner/provider |
| 3 | GitHub security alerts could not be read | Unavailable, not clean | Owner |
| 4 | Credentials in tracked files or history | None found | Clean (pattern and tool scan) |
| 5 | PHPMailer 6.12.0: no advisory in the Packagist database for this version | Info | Newer 7.x exists |
| 6 | Contact PHP, JS and HTML review | No exploitable issue found | Clean |

## 1. Exposed repository folders on production

Status-only HEAD requests (bodies not read) on the owner domain. A nonexistent path returned 404 as the control.

    /.git/HEAD 403      /.github/ 403
    /backend/ 200       /backend/composer.json 200 (application/json, 566 bytes)
    /docs/ 200          /tests/ 200      /scripts/ 200
    /README.md 200 (18,696 bytes)         /contact-submit.php 405 (GET, expected)

The 403 on `.git` and `.github` is host default dot-file protection. The other folders are web-readable, so the backend source, tests, build script and docs are public. The packaged backend (`actpsb-backend.zip`) is meant to live in `/home/arriscom/actpsb-backend`. A `backend/` directory under `public_html/actpsb.com` suggests the repository was uploaded to the document root. Private configuration lives in `/home/arriscom/actpsb-private`; its exposure was not tested and no private path was requested.

Impact: source, dependency versions and documentation are exposed (information disclosure). That is not a credential leak by itself, but it helps an attacker. If `backend/config/config.php` was ever created under `public_html` it would be exposed. The owner should check that it does not exist there.

Fix (owner, hosting is owner-controlled): remove `docs/`, `tests/`, `scripts/`, `backend/`, `README.md` and any `.git` from `public_html/actpsb.com`, and merge `deploy/public-access-denial.htaccess` as described in `htaccess-protection.md`. Re-check the status codes afterwards.

## 2. PHP advisories and runtime applicability

Official sources:
- PHP release and ChangeLog: https://www.php.net/ChangeLog-8.php and https://www.php.net/releases/
- PHP 8.3.36 (22 Oct 2026): Core GHSA-w8hw-w9fx-j79w, GHSA-6wmf-4rv5-p3rp (state corruption via bailout)
- PHP 8.3.35 (24 Sep 2026): OpenSSL GHSA-vvx9-73fr-5jjx (TLS hostname verification falls back to CN after SAN mismatch, CVE-2026-91769) and GHSA-xr7j-rvgx-xq5p (wildcard CN heap overflow, CVE-2026-91767); Standard GHSA-fpwc-w8rq-cr92 and GHSA-7875-c8px-7q5f (HTTP stream wrapper); Phar, SOAP, FPM IPv6 ACL, MySQLnd, Filter fixes
- Earlier 8.3.x: 8.3.33 (30 Jul), 8.3.32 (2 Jul), 8.3.31 (7 May)

Relevance to this site: the contact backend uses PHP streams over TLS through PHPMailer (`openssl`), so the OpenSSL hostname-verification fix in 8.3.35 is the most relevant to SMTP certificate checking. The code does not use SOAP, Phar, MySQLnd or the HTTP stream wrapper. FPM fixes apply only if the SAPI is FPM.

Applicability depends on the exact patch version, SAPI (LiteSpeed LSAPI, FPM, CGI), the OS and the provider's backports. cPanel's "PHP 8.3 (ea-php83)" selection alone does not show that 8.3.35 or later is running. Distribution and cPanel EasyApache builds may backport fixes without changing the version number, or lag behind.

Unresolved runtime facts (not verifiable from this host; the owner or hosting provider must confirm):
1. The exact PHP patch version and build for actpsb.com (for example, from cPanel MultiPHP Manager or a temporary `phpversion()` view that is not left on the server).
2. The SAPI in use and whether `openssl` and `mbstring` are enabled.
3. The provider's patch cadence for ea-php83 and whether the fixes above are backported.

Responsibility: the hosting provider patches the server PHP build and OS; the owner chooses the PHP version in cPanel and keeps it on the latest available 8.3 build; the repository owner updates dependencies. Nothing here guarantees that the site is free of vulnerabilities.

## 3. PHPMailer

- Locked version: 6.12.0 (`backend/composer.lock`, sole package, no dev packages).
- Packagist security-advisory API (https://packagist.org/api/security-advisories/?packages[]=phpmailer/phpmailer) lists 14 advisories, all affecting versions below 6.5.0 or older ranges. None cover 6.12.0. OSV (https://api.osv.dev) returned no vulnerabilities for 6.12.0.
- GitHub advisories for the project (https://github.com/PHPMailer/PHPMailer/security/advisories) list only the same older entries (latest published 2021).
- Newer releases exist: 7.0.0 to 7.1.1 (7.1.1 published 2026-05-18, https://github.com/PHPMailer/PHPMailer/releases). `composer.json` pins 6.12.0 with platform PHP 8.1. A major-version upgrade is not routine; it is left as a planned change that needs its own SMTP-sandbox test run. No known advisory requires it.
- Installed code uses TLS peer and name verification, no `SMTPAutoTLS` fallback, no `mail()` fallback, `SMTPDebug = 0`.

## 4. Secrets and private data

- Tracked tree at 48d2a7d: 77 tracked files scanned with detect-secrets (all plugins, `--all-files`) and credential regexes (private keys, AWS, GitHub, Slack, Google). One detector hit: `tests/smtp_sandbox.py` (Secret Keyword), a fixed synthetic sandbox credential used only against a local test server. Not a real secret.
- Reachable history: all 37 commits on all refs scanned for the same patterns and for sensitive file types (`.env`, `.pem`, `.key`, `.sql`, `.log`, `.zip`, `config.php`, `vendor/`). No hits other than synthetic test values (`tests/test_contact_backend.py`, `tests/smtp_sandbox.py`) and placeholders `CONFIRM_MAILBOX_PASSWORD` and `CONFIRM_SET_PASSWORD_ON_SERVER_ONLY` in `backend/config/config.example.php` (commits 9507646 and later). The `Config.php` file name matches the config pattern but is source code.
- Author metadata: commits include a work email of the owner (`colin.loh+rhglobal@...`, 3 commits: 2ce908a, 1c4433e, 7f6483f). This is personal data in public history; rewriting history is out of scope, so it is reported only.
- `.gitignore` excludes `backend/config/config.php`, `backend/vendor/`, `.env`, `*.env`, `dist/`.
- Limits: pattern scanning cannot prove absence. Binary images and the PDF were not content-scanned. History in forks, closed PRs and GitHub caches was not examined.

## 5. GitHub visibility and alerts

- Anonymous API read (https://api.github.com/repos/actpsb/actpsb.com): repository is public (`private: false`, default branch `main`).
- Authenticated visibility: not checked. This session has no GitHub login (`gh auth status`: not logged in), so authenticated repository settings (visibility, branch protection, security_and_analysis) are unavailable.
- Dependabot, secret-scanning and code-scanning alerts: HTTP 401 without authentication. Unavailable, not clean. The owner should check Security > Alerts in the repository, and enable Dependabot alerts for `backend/composer.lock` if it is not on.

## 6. Contact backend review

- Header injection: `Validator` rejects control characters in name, email, organisation and category before trim; the email allows printable ASCII only, no `<>",;\`; category is allowlisted; subject is fixed; the visitor address is Reply-To only; From and recipient come from private config.
- Arrays and non-strings are rejected; messages are UTF-8 validated, with length limits and control characters rejected.
- Origin: POST needs an Origin header exactly matching `allowed_origins` (https except loopback) and rejects a cross-site `Sec-Fetch-Site`. Method, content type (form types only) and body size (16 KiB) are checked before work is done.
- Rate limiting: file-locked sliding windows per client (HMAC-hashed address) and globally (5/600 s, 100/3600 s). `X-Forwarded-For` is trusted only from configured proxies. The default `trusted_proxies` is empty. If the host puts a proxy or CDN in front of PHP, `REMOTE_ADDR` would be that proxy and all visitors would share one per-client bucket; the owner should confirm the topology.
- SMTP/TLS: implicit TLS or STARTTLS only, peer and host verification on, no self-signed, timeout 10 s, library error text never returned or logged.
- Output: native responses escape with `htmlspecialchars` (ENT_QUOTES); JSON responses are `application/json` with `nosniff`, `no-store`, `X-Frame-Options: DENY`, and a CSP on HTML responses.
- JS/HTML: `contact-form.js` writes server text with `textContent` (the only `innerHTML` use restores the button's own markup). No third-party scripts. All 13 `target="_blank"` links carry `noopener` (now enforced by a test).
- Logs: only time, request ID and fixed code; stored outside the web root with mode 0700.
- Dependencies: no JS dependencies. `pip-audit` was installed as the audit tool; no Python dependencies are declared, and Composer is unavailable locally. The lock file was checked against the Packagist and OSV advisory databases (section 3).
- Not exercised: PHP is not installed on this host; PHP-driven tests run in CI only.

## Changes in this commit

- `deploy/public-access-denial.htaccess` (merge snippet), `docs/htaccess-protection.md` (safe merge steps)
- `tests/test_security.py` (access-denial simulation, tracked-file hygiene, link safety)
- This report

Not changed by design: hosting folders, secrets, GitHub settings, history, PHPMailer version.
