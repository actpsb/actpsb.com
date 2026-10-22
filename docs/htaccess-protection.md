# Public access-denial rules (.htaccess)

`deploy/public-access-denial.htaccess` is a merge snippet. It is not an active `.htaccess` and the upload packages do not contain one, so extracting a package never overwrites cPanel's own directives.

## What it does

- Returns 403 for dot files and folders (`.git`, `.github`, `.env`, `.htpasswd`), except `/.well-known/`.
- Returns 403 for repository folders: `backend`, `docs`, `scripts`, `tests`, `vendor`, `dist`, `deploy`, `node_modules`.
- Returns 403 for `README.md`, `composer.json/lock`, `package*.json`, and source, data and backup extensions (`md py lock log bak old orig swp sql sqlite zip tar gz ini conf yml yaml sh inc phps`).
- Returns 403 for every `.php` file except `contact-submit.php`.
- Adds `X-Content-Type-Options: nosniff` and `Referrer-Policy: strict-origin-when-cross-origin` where `mod_headers` exists.
- Does not touch handler, PHP version, `AuthType`, `Options` or any other cPanel directive. Rules sit inside `<IfModule>` so a missing module cannot cause a 500.

The host reports `Server: LiteSpeed`, which reads `.htaccess` rewrite rules.

## Safe merge (owner, cPanel File Manager)

1. In `/home/arriscom/public_html/actpsb.com` enable "Show Hidden Files" and open the existing `.htaccess` (create an empty one if absent).
2. Download a copy first as a backup.
3. Leave everything already there unchanged, especially any block between `# php -- BEGIN cPanel-generated handler` and `# php -- END cPanel-generated handler`.
4. Paste the snippet at the end of the file, from `# BEGIN ACTP access denial` to `# END ACTP access denial`. If the file already contains an ACTP block, replace only that block.
5. Save, then check in a private window: `/`, `/contact.html` and the contact form still work; `/docs/`, `/backend/composer.json`, `/tests/` and `/README.md` return 403 or 404.
6. If the site returns a 500 error, restore the backup copy.

Moving or deleting `docs/`, `tests/`, `scripts/`, `backend/` and `README.md` from `public_html/actpsb.com` removes the exposure completely and is the stronger fix. The rules are defence in depth. `backend/` belongs in `/home/arriscom/actpsb-backend`, outside the web root (see `contact-backend.md`).

## Verification

`tests/test_security.py` evaluates each rewrite pattern against allowed and denied paths and checks that no active `.htaccess` is shipped. It simulates the patterns in Python. No Apache or LiteSpeed server was available, so server behaviour is verified only by the owner's step 5 above.
