# Upgrade and rollback (cPanel File Manager only)

No hosting Terminal is needed or used. Every step is a File Manager action. Nothing here changes the live site until the owner performs it.

## Packages

CI publishes the artifact `actpsb-cpanel-<commit SHA>` containing three ZIPs, `MANIFEST.json` and `SHA256SUMS.txt`. Use ZIPs from one artifact only, so public and backend code come from the same commit.

| ZIP | Extract into | Notes |
| --- | --- | --- |
| `actpsb-backend.zip` | `/home/arriscom/actpsb-backend` | `src/`, `vendor/` (PHPMailer), `licenses/` |
| `actpsb-public.zip` | `/home/arriscom/public_html/actpsb.com` | pages, `assets/`, `favicon.ico`, `robots.txt`, `contact-submit.php`. No `.htaccess`. |
| `actpsb-private.zip` | `/home/arriscom/actpsb-private` | contains only `config.example.php`. It never contains `config.php`, so extracting cannot overwrite the real configuration. |

Verify a download before uploading: compare the SHA-256 of each ZIP with `SHA256SUMS.txt` (for example `shasum -a 256 actpsb-*.zip` on your computer).

## Prerequisites

- An existing working `/home/arriscom/actpsb-private/config.php` (real SMTP password, `allowed_origins`, `mail_to`). It is not touched by an upgrade. Open it in File Manager and confirm `allowed_origins` lists every origin visitors use, including both `https://actpsb.com` and `https://www.actpsb.com` if both serve the site.
- `/home/arriscom/actpsb-private` is 0700 and `config.php` is 0600.
- PHP 8.3 with `openssl` and `mbstring` (MultiPHP Manager / PHP extensions).
- A confirmed way to see the contact form working afterwards (a mailbox you control).

## Fresh install (first time only)

1. Extract the backend ZIP, then the public ZIP.
2. Create `actpsb-private` (0700). Extract `actpsb-private.zip`, copy `config.example.php` to `config.php`, edit it (replace only `CONFIRM_SET_PASSWORD_ON_SERVER_ONLY`, check `allowed_origins`), set 0600. Never put the password in chat, tickets or git.

## Upgrade

1. Back up. In File Manager, select these and use Compress (ZIP) into `/home/arriscom/actpsb-rollback/<date>/` (create the folder, 0700, outside `public_html`):
   - `/home/arriscom/actpsb-backend` -> `backend-before.zip`
   - the site files in `/home/arriscom/public_html/actpsb.com` (pages, `assets`, `favicon.ico`, `robots.txt`, `contact-submit.php`) -> `public-before.zip`
   - Download `/home/arriscom/actpsb-private/config.php` to your computer as a backup. Keep it private.
   - Download the current `.htaccess` (enable Show Hidden Files).
2. Do not delete anything and do not touch `actpsb-private/config.php`.
3. Upload and Extract `actpsb-backend.zip` into `/home/arriscom/actpsb-backend`, overwriting existing files. Order matters: backend first, so the old public entry point never runs against missing code.
4. Upload and Extract `actpsb-public.zip` into `/home/arriscom/public_html/actpsb.com`, overwriting existing files.
5. Skip `actpsb-private.zip` on upgrade. Open `config.example.php` only if the release notes say a new key was added, then add that key to your real `config.php` by hand.
6. Merge `.htaccess` (once, or when the snippet changes): follow `docs/htaccess-protection.md`. Append the block between `# BEGIN ACTP access denial` and `# END ACTP access denial`; replace only an older ACTP block; leave the cPanel-generated PHP handler block and every other line alone.
7. Remove exposed leftovers from `public_html/actpsb.com` if present: `backend/`, `docs/`, `tests/`, `scripts/`, `README.md`, `dist/`. These are not part of the packages. Move them to the rollback folder rather than deleting.
8. Check in a private window: `/`, `/about.html`, `/services.html`, `/insights.html`, `/contact.html` and the logo/favicon load; `/docs/`, `/backend/composer.json`, `/README.md` return 403 or 404.
9. Contact check. Send ONE test enquiry and wait for the on-page result and for the mail to arrive. Do not click Send again while waiting: the form never retries by itself, and a second click sends a second message. If the page shows "unavailable", "could not confirm" or an error, check the inbox before trying again, because "could not confirm" may mean the message was delivered. Record what you saw.

## Rollback

1. Extract `backend-before.zip` into `/home/arriscom/actpsb-backend`, overwriting.
2. Extract `public-before.zip` into `/home/arriscom/public_html/actpsb.com`, overwriting. Files added only by the new release remain; remove them by name if they matter.
3. If `config.php` was changed by mistake, upload your backup copy over it and set 0600.
4. If the site returns a 500 after the `.htaccess` merge, upload the saved `.htaccess` backup over it.
5. Repeat the page and contact checks above (one test message only).

## Avoiding duplicates and ambiguity

- Extract each ZIP once; if an extract is interrupted, extract it again over the same folder (overwrite is safe and idempotent).
- One test message per attempt; wait for the outcome. The server rate-limits repeats, and a "could not confirm" result needs the inbox checked before any retry.
- Public and backend ZIPs must come from the same artifact (same SHA in `MANIFEST.json`).
