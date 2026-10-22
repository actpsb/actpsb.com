"""Scenario tests run against the BUILT upload ZIPs extracted into a simulated /home/arriscom layout.

Only synthetic values and a local SMTP sandbox are used; nothing here talks to a real host or mailbox.
Covers: success, SMTP failure, invalid message, origin rejection, unavailable config, and what the
client script shows for a malformed/HTML response.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import socket
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from smtp_sandbox import Sandbox  # noqa: E402
from test_contact_backend import (GOOD, OPENER, PHP, ROOT, SKIP, VENDOR, client_view, free_port)  # noqa: E402


@unittest.skipUnless(PHP and VENDOR.is_file() and (os.environ.get("ACTP_COMPOSER") or shutil.which("composer")), SKIP)
class PackageScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "scripts"))
        import build_packages
        cls.tmp = Path(tempfile.mkdtemp(prefix="actp-scn-"))
        cls.dist = cls.tmp / "dist"
        build_packages.build(cls.dist)
        cls.home = cls.tmp / "home" / "arriscom"
        cls.docroot = cls.home / "public_html" / "actpsb.com"
        for name, dest in (("public", cls.docroot), ("backend", cls.home / "actpsb-backend"),
                           ("private", cls.home / "actpsb-private")):
            dest.mkdir(parents=True)
            zipfile.ZipFile(cls.dist / f"actpsb-{name}.zip").extractall(dest)
        cls.priv = cls.home / "actpsb-private"
        cls.priv.chmod(0o700)
        cls.sb = Sandbox(cls.tmp)
        cls.port = free_port()
        cls.proc = None

    @classmethod
    def tearDownClass(cls):
        if cls.proc:
            cls.proc.terminate()
            cls.proc.wait(5)
        cls.sb.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def write_config(self, **over):
        cfg = {"smtp_host": "localhost", "smtp_port": self.sb.port, "smtp_secure": "tls", "smtp_user": self.sb.user,
               "smtp_pass": self.sb.password, "smtp_ca_file": str(self.sb.crt), "mail_from": "mailbox@sandbox.test",
               "mail_to": "inbox@sandbox.test", "form_enabled": True,
               "allowed_origins": [f"http://127.0.0.1:{self.port}", "http://localhost:%d" % self.port]}
        cfg.update(over)
        (self.priv / "config.php").write_text("<?php return " + _php(cfg) + ";")
        (self.priv / "config.php").chmod(0o600)

    def serve(self):
        cls = type(self)
        if cls.proc:
            cls.proc.terminate()
            cls.proc.wait(5)
        env = {k: v for k, v in os.environ.items() if not k.startswith("ACTP_")}
        cls.proc = subprocess.Popen([PHP, "-S", f"127.0.0.1:{self.port}", "-t", str(self.docroot)], env=env,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(self.docroot))
        for _ in range(200):
            try:
                socket.create_connection(("127.0.0.1", self.port), timeout=0.2).close()
                return
            except OSError:
                time.sleep(0.05)

    def post(self, data=None, origin="same"):
        headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
        if origin == "same":
            headers["Origin"] = f"http://127.0.0.1:{self.port}"
        elif origin:
            headers["Origin"] = origin
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/contact-submit.php",
                                     data=urllib.parse.urlencode(data or GOOD).encode(), headers=headers, method="POST")
        try:
            r = OPENER.open(req, timeout=30)
        except urllib.error.HTTPError as e:
            r = e
        body = r.read().decode()
        return r.status, body

    def fresh(self, **over):
        shutil.rmtree(self.priv / "var", ignore_errors=True)
        self.write_config(**over)
        self.serve()
        self.sb.messages.clear()

    def test_01_template_only_private_zip(self):
        names = zipfile.ZipFile(self.dist / "actpsb-private.zip").namelist()
        self.assertEqual(names, ["config.example.php"])
        self.assertFalse((self.priv / "config.php").exists())
        # a pre-existing real config survives extracting the private ZIP again
        (self.priv / "config.php").write_text("<?php return ['REAL'=>1];")
        zipfile.ZipFile(self.dist / "actpsb-private.zip").extractall(self.priv)
        self.assertEqual((self.priv / "config.php").read_text(), "<?php return ['REAL'=>1];")
        (self.priv / "config.php").unlink()

    def test_02_manifest_hashes_and_version_mapping(self):
        m = json.loads((self.dist / "MANIFEST.json").read_text())
        for name, info in m["packages"].items():
            self.assertEqual(hashlib.sha256((self.dist / name).read_bytes()).hexdigest(), info["sha256"])
            self.assertEqual(sorted(zipfile.ZipFile(self.dist / name).namelist()), info["members"])
        sums = (self.dist / "SHA256SUMS.txt").read_text().split("\n")
        self.assertIn(f"{m['packages']['actpsb-public.zip']['sha256']}  actpsb-public.zip", sums)
        lock = json.loads((ROOT / "backend/composer.lock").read_text())
        self.assertEqual(m["dependencies"], {p["name"]: p["version"] for p in lock["packages"]})
        self.assertIn("vendor/phpmailer/phpmailer/src/PHPMailer.php", m["packages"]["actpsb-backend.zip"]["members"])
        self.assertNotIn("config.php", m["packages"]["actpsb-public.zip"]["members"])
        self.assertFalse([n for z in m["packages"].values() for n in z["members"]
                          if n.startswith((".git", "tests/", "docs/", "scripts/", "dist/", "deploy/"))
                          or n in {"README.md", ".htaccess"} or n.endswith((".env", ".pem", ".key"))])

    def test_03_success_sends_exactly_one_message(self):
        self.fresh()
        status, body = self.post()
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["status"], "accepted")
        self.assertEqual(len(self.sb.messages), 1)
        v = client_view(status, body)
        self.assertEqual(v["state"], "accepted")

    def test_04_smtp_auth_failure_is_not_reported_as_sent(self):
        self.fresh(smtp_pass="wrong-password")
        status, body = self.post()
        self.assertNotEqual(status, 200)
        self.assertNotEqual(json.loads(body)["status"], "accepted")
        self.assertEqual(self.sb.messages, [])
        self.assertNotIn("wrong-password", body)
        self.assertNotEqual(client_view(status, body)["state"], "accepted")

    def test_05_recipient_rejected_is_not_reported_as_sent(self):
        self.fresh(mail_to="elsewhere@sandbox.test")
        status, body = self.post()
        self.assertNotEqual(status, 200)
        self.assertEqual(self.sb.messages, [])

    def test_06_invalid_message_is_422_and_sends_nothing(self):
        self.fresh()
        status, body = self.post({**GOOD, "message": "hi"})
        self.assertEqual(status, 422)
        self.assertEqual(self.sb.messages, [])
        v = client_view(status, body)
        self.assertEqual(v["state"], "invalid")
        self.assertIn("message", v["errors"])

    def test_07_origin_rejection(self):
        self.fresh()
        for origin in ("https://evil.example", "http://127.0.0.1:1", None):
            status, body = self.post(origin=origin)
            self.assertEqual(status, 403, origin)
            self.assertEqual(self.sb.messages, [])

    def test_08_unavailable_config_fails_closed(self):
        self.fresh(smtp_pass="CONFIRM_SET_PASSWORD_ON_SERVER_ONLY")
        status, body = self.post()
        self.assertEqual(status, 503)
        self.assertEqual(json.loads(body)["status"], "unavailable")
        self.assertEqual(self.sb.messages, [])
        self.assertEqual(client_view(status, body)["state"], "unavailable")
        self.fresh(form_enabled=False)
        self.assertEqual(self.post()[0], 503)
        (self.priv / "config.php").unlink()
        self.serve()
        self.assertEqual(self.post()[0], 503)
        self.assertEqual(self.sb.messages, [])

    def test_09_malformed_or_html_responses_are_never_success(self):
        for status, body in ((200, "<html>proxy page</html>"), (200, ""), (502, "<html>Bad gateway</html>"),
                             (500, "<br />PHP Fatal error"), (200, "not json")):
            self.assertNotEqual(client_view(status, body)["state"], "accepted", (status, body))

    def test_10_public_package_serves_pages_and_assets(self):
        self.fresh()
        for path in ("/", "/index.html", "/contact.html", "/favicon.ico", "/assets/css/base.css", "/assets/js/contact-form.js"):
            with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=10) as r:
                self.assertEqual(r.status, 200, path)


def _php(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, list):
        return "[" + ",".join(_php(i) for i in v) + "]"
    if isinstance(v, dict):
        return "[" + ",".join(f"{_php(k)}=>{_php(i)}" for k, i in v.items()) + "]"
    return "'" + str(v).replace("\\", "\\\\").replace("'", "\\'") + "'"


if __name__ == "__main__":
    unittest.main()
