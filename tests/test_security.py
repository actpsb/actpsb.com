"""Security hygiene checks: access-denial rules, tracked-file secret patterns, link safety."""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNIPPET = ROOT / "deploy" / "public-access-denial.htaccess"

ALLOWED = [
    "index.html", "about.html", "services.html", "insights.html", "contact.html", "robots.txt",
    "favicon.ico", "contact-submit.php", "assets/css/base.css", "assets/js/contact-form.js",
    "assets/images/actp-logo.png", "assets/documents/nuren-group-nsx-admission.pdf",
    ".well-known/acme-challenge/token", ".well-known/security.txt",
]
DENIED = [
    ".git/config", ".git/HEAD", ".github/workflows/ci.yml", ".gitignore", ".env", ".htpasswd", "assets/.env",
    "backend/src/Handler.php", "backend/composer.lock", "backend/config/config.php", "vendor/autoload.php",
    "docs/contact-backend.md", "docs/qa/screenshots/home-1440.png", "scripts/build_packages.py",
    "tests/test_site.py", "dist/actpsb-public.zip", "deploy/public-access-denial.htaccess",
    "README.md", "composer.json", "composer.lock", "config.php", "backup.zip", "site.sql", "x.PHP",
    "assets/old.php", "contact-submit.php.bak", "contact-submit.php~.swp", "notes.log", "BACKEND/src/a.php",
]


def rules():
    out = []
    for line in SNIPPET.read_text(encoding="utf-8").splitlines():
        m = re.match(r"RewriteRule\s+(\S+)\s+-\s+\[([A-Z,]+)\]$", line)
        if m:
            out.append((m.group(1), m.group(2).split(",")))
    return out


def denied(path: str) -> bool:
    for pattern, flags in rules():
        if re.search(pattern, path, re.I if "NC" in flags else 0):
            return True
    return False


class AccessDenialTests(unittest.TestCase):
    def test_snippet_structure_preserves_host_directives(self):
        text = SNIPPET.read_text(encoding="utf-8")
        self.assertIn("# BEGIN ACTP access denial", text)
        self.assertIn("# END ACTP access denial", text)
        self.assertEqual(text.count("<IfModule"), text.count("</IfModule>"))
        for forbidden in ("AddHandler", "SetHandler", "suPHP", "php_value", "php_flag", "AuthType", "Options"):
            self.assertIsNone(re.search(rf"^\s*{forbidden}\b", text, re.M), forbidden)
        self.assertTrue(rules())

    def test_public_site_paths_stay_reachable(self):
        for p in ALLOWED:
            self.assertFalse(denied(p), p)

    def test_private_and_repository_paths_are_denied(self):
        for p in DENIED:
            self.assertTrue(denied(p), p)

    def test_every_public_file_in_the_upload_package_is_reachable(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import build_packages
        files = list(build_packages.PUBLIC_FILES)
        for d in build_packages.PUBLIC_DIRS:
            files += [p.relative_to(ROOT).as_posix() for p in (ROOT / d).rglob("*") if p.is_file()]
        self.assertEqual([f for f in files if denied(f)], [])

    def test_snippet_is_never_shipped_as_an_active_htaccess(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import build_packages
        self.assertNotIn(".htaccess", build_packages.PUBLIC_FILES)
        self.assertFalse((ROOT / ".htaccess").exists())
        self.assertFalse(list((ROOT / "assets").rglob(".htaccess")))


class TrackedFileHygieneTests(unittest.TestCase):
    PATTERNS = [
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"AKIA[0-9A-Z]{16}", r"gh[pousr]_[A-Za-z0-9]{30,}",
        r"github_pat_[A-Za-z0-9_]{20,}", r"xox[abp]-[A-Za-z0-9-]{10,}", r"AIza[0-9A-Za-z_-]{35}",
    ]

    def tracked(self):
        try:
            out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("not a git checkout")
        return [ROOT / p for p in out.splitlines() if p]

    def test_no_private_files_tracked(self):
        bad = []
        for p in self.tracked():
            rel = p.relative_to(ROOT)
            if (p.name in {"config.php", ".env", ".htpasswd"} or p.suffix in {".pem", ".key", ".p12", ".sqlite"}
                    or "vendor" in rel.parts or rel.parts[0] == "dist"):
                bad.append(rel.as_posix())
        self.assertEqual(bad, [])

    def test_no_credential_patterns_in_tracked_text(self):
        hits = []
        for p in self.tracked():
            if p.suffix in {".png", ".pdf", ".ico"}:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            hits += [p.relative_to(ROOT).as_posix() for pat in self.PATTERNS if re.search(pat, text)]
        self.assertEqual(hits, [])

    def test_example_config_is_disabled_placeholder(self):
        text = (ROOT / "backend/config/config.example.php").read_text(encoding="utf-8")
        self.assertIn("'form_enabled' => false", text)
        self.assertIn("CONFIRM_", text)

    def test_external_new_tab_links_use_noopener(self):
        for page in ROOT.glob("*.html"):
            for tag in re.findall(r"<a\b[^>]*>", page.read_text(encoding="utf-8"), re.S):
                if 'target="_blank"' in tag:
                    self.assertIn("noopener", tag, f"{page.name}: {tag[:80]}")


class RequiredExtensionTests(unittest.TestCase):
    """ext-ctype is a declared requirement and its absence fails closed without detail."""

    def test_composer_declares_ctype_in_json_and_lock(self):
        import json
        j = json.loads((ROOT / "backend/composer.json").read_text(encoding="utf-8"))
        lock = json.loads((ROOT / "backend/composer.lock").read_text(encoding="utf-8"))
        self.assertEqual(j["require"]["ext-ctype"], "*")
        self.assertEqual(lock["platform"]["ext-ctype"], "*")

    def test_missing_ctype_fails_closed_without_leaking(self):
        import os
        import shutil
        import tempfile
        php = os.environ.get("ACTP_PHP") or shutil.which("php")
        if not php:
            self.skipTest("php unavailable")
        with tempfile.TemporaryDirectory() as d:
            env = {**os.environ, "HTTP_ACCEPT": "application/json", "ACTP_SMTP_PASS": "s3cret-value"}
            r = subprocess.run([php, "-d", "disable_functions=ctype_digit", str(ROOT / "contact-submit.php")],
                               capture_output=True, text=True, cwd=d, env=env, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('"status":"unavailable"', r.stdout)
        for text in (r.stdout, r.stderr):
            self.assertNotIn("ctype", text.lower())
            self.assertNotIn("s3cret-value", text)


if __name__ == "__main__":
    unittest.main()
