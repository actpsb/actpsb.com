"""Backend tests for the PHP contact endpoint, driven over real HTTP against `php -S` and a local SMTP sandbox.

Everything here is synthetic and local: the sandbox accepts mail into memory and relays nothing.
These tests verify local behaviour only. They do not prove production SMTP delivery, cPanel
configuration or inbox arrival; see docs/contact-backend.md.

Set ACTP_PHP to a php binary if `php` is not on PATH. Without php and backend/vendor
(`composer install` in backend/) the PHP-driven tests are skipped; CI installs both.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from smtp_sandbox import Sandbox  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PHP = os.environ.get("ACTP_PHP") or shutil.which("php")
VENDOR = ROOT / "backend" / "vendor" / "autoload.php"
SKIP = "php or backend/vendor (composer install) unavailable"


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPENER = urllib.request.build_opener(NoRedirect)

GOOD = {"name": "Synthetic Tester", "email": "visitor@example.test", "organisation": "Test Org",
        "message": "This is a synthetic test message for the sandbox only."}


class Site:
    """php -S serving the repo root; backend and private dirs live outside the document root."""

    def __init__(self, tmp: Path, sb, port: int, env_over: dict):
        self.port = port
        self.origin = f"http://127.0.0.1:{port}"
        env = {
            "ACTP_SMTP_HOST": "localhost", "ACTP_SMTP_PORT": str(sb.port),
            "ACTP_SMTP_SECURE": "ssl" if sb.implicit_tls else "tls",
            "ACTP_SMTP_USER": sb.user, "ACTP_SMTP_PASS": sb.password, "ACTP_SMTP_CA_FILE": str(sb.crt),
            "ACTP_MAIL_FROM": "mailbox@sandbox.test", "ACTP_MAIL_TO": "inbox@sandbox.test",
            "ACTP_STATE_DIR": str(tmp / "state"), "ACTP_ALLOWED_ORIGINS": self.origin,
        }
        env.update(env_over)
        e = {k: v for k, v in os.environ.items() if not k.startswith("ACTP_")}
        e.update({"ACTP_BACKEND_DIR": str(ROOT / "backend"), "ACTP_PRIVATE_DIR": str(tmp / "private")})
        e.update(env)
        self.proc = subprocess.Popen([PHP, "-S", f"127.0.0.1:{port}", "-t", str(ROOT)], env=e,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(ROOT))
        for _ in range(200):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                return
            except OSError:
                time.sleep(0.05)
        raise RuntimeError("php server did not start")

    def stop(self):
        self.proc.terminate()
        self.proc.wait(5)

    def post(self, fields, headers=None, ctype="application/x-www-form-urlencoded", raw=None,
             json_accept=True, origin=True):
        body = raw if raw is not None else urllib.parse.urlencode(fields).encode()
        h = {"Content-Type": ctype}
        if origin:
            h["Origin"] = self.origin
        if json_accept:
            h["Accept"] = "application/json"
        h.update(headers or {})
        req = urllib.request.Request(self.origin + "/contact-submit.php", data=body, headers=h, method="POST")
        try:
            r = OPENER.open(req, timeout=30)
        except urllib.error.HTTPError as e:
            r = e
        return r.status, dict(r.headers), r.read().decode("utf-8", "replace")


@unittest.skipUnless(PHP and VENDOR.is_file(), SKIP)
class BackendBase(unittest.TestCase):
    sandbox_kwargs = {}
    env_over = {}

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="actp-test-"))
        self.sb = Sandbox(self.tmp, **self.sandbox_kwargs)
        self.site = None

    def start(self, **over):
        env = dict(self.env_over)
        env.update(over)
        self.site = Site(self.tmp, self.sb, free_port(), env)
        return self.site

    def tearDown(self):
        if self.site:
            self.site.stop()
        self.sb.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def log_text(self):
        return "".join(p.read_text() for p in self.tmp.rglob("*.log"))


class AcceptanceTests(BackendBase):
    def test_success_reported_only_after_smtp_acceptance(self):
        s = self.start()
        status, headers, body = s.post(GOOD)
        self.assertEqual(status, 200, body)
        d = json.loads(body)
        self.assertEqual(d["status"], "accepted")
        self.assertIn("not a confirmation", d["message"])
        self.assertEqual(len(self.sb.messages), 1)
        m = self.sb.messages[0]
        self.assertEqual(m["rcpts"], ["inbox@sandbox.test"])
        self.assertIn("mailbox@sandbox.test", m["mail_from"])
        self.assertRegex(m["data"], r"(?im)^From: .*<mailbox@sandbox\.test>")
        self.assertRegex(m["data"], r"(?im)^Reply-To: .*<visitor@example\.test>")
        self.assertNotRegex(m["data"], r"(?im)^(To|Cc|Bcc): .*visitor@example\.test")
        self.assertEqual(self.sb.plaintext_auth_attempts, 0)
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_implicit_tls_port_465_style(self):
        self.sb.close()
        self.sb = Sandbox(self.tmp, implicit_tls=True)
        s = self.start()
        status, _, body = s.post(GOOD)
        self.assertEqual(status, 200, body)
        self.assertEqual(len(self.sb.messages), 1)

    def test_native_post_without_js_renders_page_with_status(self):
        s = self.start()
        status, headers, body = s.post(GOOD, json_accept=False)
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn('id="form-status"', body)
        self.assertIn('role="status"', body)
        self.assertIn("accepted by our mail service", body)
        self.assertIn("<h1", body)
        self.assertIn('content="noindex"', body)
        self.assertNotIn("<form", body)

    def test_log_has_no_message_content_or_secrets(self):
        s = self.start()
        s.post(GOOD)
        s.post({**GOOD, "email": "bad"})
        log = self.log_text()
        self.assertIn("smtp_accepted", log)
        for secret in (self.sb.password, self.sb.user, GOOD["message"], GOOD["email"], GOOD["name"],
                       "inbox@sandbox.test"):
            self.assertNotIn(secret, log)


class FailureTests(BackendBase):
    def test_rejected_auth(self):
        s = self.start(ACTP_SMTP_PASS="wrong-synthetic-pass")
        status, _, body = s.post(GOOD)
        self.assertEqual(status, 502)
        d = json.loads(body)
        self.assertEqual(d["status"], "failed")
        self.assertIn("Nothing has been delivered", d["message"])
        self.assertEqual(self.sb.messages, [])
        self.assertGreaterEqual(self.sb.auth_failures, 1)
        for leak in ("wrong-synthetic-pass", "535", "Authentication", "localhost", str(self.sb.port)):
            self.assertNotIn(leak, body)
        self.assertIn("smtp_auth", self.log_text())
        self.assertNotIn("wrong-synthetic-pass", self.log_text())

    def test_rejected_recipient(self):
        s = self.start(ACTP_MAIL_TO="someone-else@sandbox.test")
        status, _, body = s.post(GOOD)
        self.assertEqual(status, 502)
        self.assertEqual(json.loads(body)["status"], "failed")
        self.assertEqual(self.sb.messages, [])
        self.assertGreaterEqual(self.sb.rcpt_rejections, 1)
        self.assertNotIn("someone-else", body)

    def test_smtp_unreachable(self):
        s = self.start(ACTP_SMTP_PORT=str(free_port()))
        status, _, body = s.post(GOOD)
        self.assertEqual(status, 502)
        self.assertEqual(json.loads(body)["status"], "failed")

    def test_untrusted_certificate_is_rejected_not_bypassed(self):
        s = self.start(ACTP_SMTP_CA_FILE="")  # system trust store does not know the sandbox CA
        status, _, _ = s.post(GOOD)
        self.assertEqual(status, 502)
        self.assertEqual(self.sb.messages, [])
        self.assertEqual(self.sb.auth_failures, 0)

    def test_hostname_mismatch_is_rejected(self):
        s = self.start(ACTP_SMTP_HOST="127.0.0.1")  # certificate is for "localhost"
        status, _, _ = s.post(GOOD)
        self.assertEqual(status, 502)
        self.assertEqual(self.sb.messages, [])

    def test_native_failure_page_is_truthful(self):
        s = self.start(ACTP_SMTP_PASS="wrong-synthetic-pass")
        status, _, body = s.post(GOOD, json_accept=False)
        self.assertEqual(status, 502)
        self.assertIn("was not sent", body)
        self.assertIn('role="alert"', body)
        self.assertNotRegex(body.lower(), r"message sent|thank you|accepted by our mail service")
        self.assertIn('value="visitor@example.test"', body)  # input preserved, escaped


class UnconfiguredTests(BackendBase):
    BLANK = dict(ACTP_SMTP_HOST="", ACTP_SMTP_PORT="", ACTP_SMTP_USER="", ACTP_SMTP_PASS="", ACTP_MAIL_FROM="",
                 ACTP_MAIL_TO="", ACTP_ALLOWED_ORIGINS="", ACTP_SMTP_CA_FILE="", ACTP_STATE_DIR="")

    def test_no_config_fails_closed(self):
        s = self.start(**self.BLANK)
        status, _, body = s.post(GOOD)
        self.assertEqual(status, 503)
        d = json.loads(body)
        self.assertEqual(d["status"], "unavailable")
        self.assertIn("not available", d["message"])
        self.assertEqual(self.sb.messages, [])
        self.assertNotRegex(body.lower(), r"accepted|thank you|message sent")

    def test_placeholder_template_fails_closed(self):
        priv = self.tmp / "private"
        priv.mkdir()
        shutil.copy(ROOT / "backend/config/config.example.php", priv / "config.php")
        s = self.start(**self.BLANK)
        status, _, _ = s.post(GOOD)
        self.assertEqual(status, 503)
        self.assertEqual(self.sb.messages, [])

    def test_valid_private_config_file_outside_web_root_is_used(self):
        priv = self.tmp / "private"
        priv.mkdir()
        sb = self.sb
        (priv / "config.php").write_text(
            "<?php return " + json.dumps({}) .replace("{}", "[") + "'smtp_host'=>'localhost','smtp_port'=>%d,"
            "'smtp_secure'=>'tls','smtp_user'=>'%s','smtp_pass'=>'%s','smtp_ca_file'=>'%s',"
            "'mail_from'=>'mailbox@sandbox.test','mail_to'=>'inbox@sandbox.test',"
            "'allowed_origins'=>['ORIGIN'],'state_dir'=>'%s'];" % (sb.port, sb.user, sb.password, sb.crt, self.tmp / "state"))
        port = free_port()
        text = (priv / "config.php").read_text().replace("ORIGIN", f"http://127.0.0.1:{port}")
        (priv / "config.php").write_text(text)
        self.site = Site(self.tmp, self.sb, port, self.BLANK)
        status, _, body = self.site.post(GOOD)
        self.assertEqual(status, 200, body)
        self.assertEqual(len(self.sb.messages), 1)
        self.assertFalse(str(priv).startswith(str(ROOT)))

    def test_native_unavailable_page(self):
        s = self.start(**self.BLANK)
        status, _, body = s.post(GOOD, json_accept=False, origin=False)
        self.assertEqual(status, 503)
        self.assertIn("not available yet", body)
        self.assertIn('role="alert"', body)
        self.assertNotIn("<form", body)

    def test_get_when_unconfigured_is_method_error_not_success(self):
        s = self.start(**self.BLANK)
        try:
            r = OPENER.open(s.origin + "/contact-submit.php", timeout=10)
        except urllib.error.HTTPError as e:
            r = e
        self.assertEqual(r.status, 405)


class PreflightTests(BackendBase):
    BLANK = UnconfiguredTests.BLANK

    def get(self, s, path):
        try:
            r = OPENER.open(s.origin + path, timeout=10)
        except urllib.error.HTTPError as e:
            r = e
        return r.status, dict(r.headers), r.read().decode("utf-8", "replace")

    def test_preflight_unconfigured_is_503_and_value_free(self):
        s = self.start(**self.BLANK)
        status, headers, body = self.get(s, "/contact-submit.php?preflight=1")
        self.assertEqual(status, 503)
        self.assertEqual(json.loads(body), {"available": False})
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(self.sb.messages, [])

    def test_preflight_placeholder_template_is_unavailable(self):
        priv = self.tmp / "private"
        priv.mkdir()
        shutil.copy(ROOT / "backend/config/config.example.php", priv / "config.php")
        s = self.start(**self.BLANK)
        self.assertEqual(self.get(s, "/contact-submit.php?preflight=1")[0], 503)

    def test_preflight_configured_is_200_without_contacting_mail_server(self):
        s = self.start()
        status, _, body = self.get(s, "/contact-submit.php?preflight=1")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"available": True})
        self.assertEqual(self.sb.messages, [])
        self.assertNotRegex(body, r"(?i)smtp|pass|host|mailbox|sandbox")

    def test_form_route_unconfigured_shows_notice_and_no_form(self):
        s = self.start(**self.BLANK)
        status, _, body = self.get(s, "/contact-submit.php?form=1")
        self.assertEqual(status, 503)
        self.assertIn("not available yet", body)
        self.assertIn('role="alert"', body)
        self.assertNotIn("<form", body)
        self.assertNotIn("enquiry-form-template", body)
        self.assertNotIn("Send enquiry", body)

    def test_form_route_configured_renders_working_form(self):
        s = self.start()
        status, _, body = self.get(s, "/contact-submit.php?form=1")
        self.assertEqual(status, 200)
        self.assertIn('<form class="contact-form" method="post" action="contact-submit.php"', body)
        self.assertNotIn('role="alert"', body)
        self.assertNotIn("Reference:", body)
        self.assertNotIn("form-availability", body.split("<!--ACTP:FORM-->")[1].split("<!--/ACTP:FORM-->")[0])
        self.assertIn('<main id="main" tabindex="-1">', body)

    def test_other_get_still_405(self):
        s = self.start()
        self.assertEqual(self.get(s, "/contact-submit.php?preflight=0")[0], 405)


class ValidationTests(BackendBase):
    env_over = {"ACTP_RATE_IP_MAX": "100"}

    def check(self, fields, field):
        status, _, body = self.site.post(fields)
        self.assertEqual(status, 422, body)
        self.assertIn(field, json.loads(body)["errors"])
        self.assertEqual(self.sb.messages, [])

    def test_required_and_format(self):
        self.start()
        self.check({**GOOD, "name": ""}, "name")
        self.check({**GOOD, "email": ""}, "email")
        self.check({**GOOD, "email": "not-an-email"}, "email")
        self.check({**GOOD, "message": "short"}, "message")
        self.check({**GOOD, "message": "x" * 5001}, "message")
        self.check({**GOOD, "name": "n" * 101}, "name")
        self.check({**GOOD, "message": "ok message\x00with nul"}, "message")

    def test_non_scalar_fields_rejected(self):
        s = self.start()
        status, _, body = s.post(None, raw=b"name[]=a&email=visitor%40example.test&message=long+enough+message+here")
        self.assertEqual(status, 422)
        self.assertIn("name", json.loads(body)["errors"])

    def test_header_injection_rejected(self):
        self.start()
        for bad in ("visitor@example.test\r\nBcc: attacker@evil.test", "visitor@example.test\nBcc: a@b.test",
                    "a@example.test,b@example.test", "<a@example.test>", '"x"@example.test',
                    "a@example.test\x00"):
            self.check({**GOOD, "email": bad}, "email")
        self.check({**GOOD, "name": "Bob\r\nBcc: attacker@evil.test"}, "name")
        self.check({**GOOD, "name": "Bob\nSubject: hijack"}, "name")
        self.check({**GOOD, "organisation": "Org\r\nX-Evil: 1"}, "organisation")
        self.assertEqual(self.sb.messages, [])

    def test_attacker_cannot_choose_recipient_or_subject(self):
        s = self.start()
        status, _, body = s.post({**GOOD, "to": "attacker@evil.test", "recipient": "attacker@evil.test",
                                  "subject": "hijack", "from": "x@evil.test", "cc": "attacker@evil.test"})
        self.assertEqual(status, 200, body)
        m = self.sb.messages[0]
        self.assertEqual(m["rcpts"], ["inbox@sandbox.test"])
        self.assertNotIn("evil.test", m["data"])
        self.assertNotIn("hijack", m["data"])

    def test_multiline_message_and_unicode_ok(self):
        s = self.start()
        status, _, body = s.post({**GOOD, "message": "Line one caf\u00e9 \u4f60\u597d\nLine two\n.\nLine four.",
                                  "name": "Zo\u00eb Ng"})
        self.assertEqual(status, 200, body)
        self.assertEqual(len(self.sb.messages), 1)

    def test_errors_are_escaped_in_native_page(self):
        s = self.start()
        evil = '"><script>alert(1)</script>'
        status, _, body = s.post({**GOOD, "name": evil, "email": "bad"}, json_accept=False)
        self.assertEqual(status, 422)
        self.assertNotIn("<script>alert(1)", body)
        self.assertIn("&lt;script&gt;", body)
        self.assertIn('role="alert"', body)
        self.assertIn('href="#field-email"', body)
        self.assertIn('aria-invalid="true"', body)


class RequestShapeTests(BackendBase):
    def test_method_constrained(self):
        s = self.start()
        for method in ("GET", "PUT", "DELETE"):
            req = urllib.request.Request(s.origin + "/contact-submit.php", method=method,
                                         data=b"x" if method != "GET" else None,
                                         headers={"Accept": "application/json"})
            try:
                r = OPENER.open(req, timeout=10)
            except urllib.error.HTTPError as e:
                r = e
            self.assertEqual(r.status, 405, method)
            self.assertEqual(r.headers["Allow"], "POST")
        self.assertEqual(self.sb.messages, [])

    def test_content_type_constrained(self):
        s = self.start()
        self.assertEqual(s.post(None, raw=json.dumps(GOOD).encode(), ctype="application/json")[0], 415)
        self.assertEqual(s.post(None, raw=b"hello", ctype="text/plain")[0], 415)
        self.assertEqual(self.sb.messages, [])

    def test_oversize_body_rejected(self):
        s = self.start()
        self.assertEqual(s.post({**GOOD, "message": "y" * 40000})[0], 413)
        self.assertEqual(self.sb.messages, [])

    def test_cross_origin_and_missing_origin_rejected(self):
        s = self.start()
        self.assertEqual(s.post(GOOD, headers={"Origin": "https://evil.example"})[0], 403)
        self.assertEqual(s.post(GOOD, origin=False)[0], 403)
        self.assertEqual(s.post(GOOD, headers={"Sec-Fetch-Site": "cross-site"})[0], 403)
        self.assertEqual(self.sb.messages, [])

    def test_honeypot_refused_without_sending(self):
        s = self.start()
        status, _, body = s.post({**GOOD, "website": "http://spam.example"})
        self.assertEqual(status, 400)
        self.assertNotEqual(json.loads(body)["status"], "accepted")
        self.assertEqual(self.sb.messages, [])

    def test_security_headers_on_html(self):
        s = self.start()
        _, headers, _ = s.post(GOOD, json_accept=False)
        h = {k.lower(): v for k, v in headers.items()}
        self.assertEqual(h["x-content-type-options"], "nosniff")
        self.assertEqual(h["x-frame-options"], "DENY")
        self.assertIn("form-action 'self'", h["content-security-policy"])


class RateLimitTests(BackendBase):
    env_over = {"ACTP_RATE_IP_MAX": "2", "ACTP_RATE_IP_WINDOW": "600"}

    def test_per_ip_limit_with_retry_after(self):
        s = self.start()
        self.assertEqual(s.post(GOOD)[0], 200)
        self.assertEqual(s.post(GOOD)[0], 200)
        status, headers, body = s.post(GOOD)
        self.assertEqual(status, 429)
        self.assertGreaterEqual(int(headers["Retry-After"]), 1)
        self.assertEqual(json.loads(body)["status"], "rate_limited")
        self.assertEqual(len(self.sb.messages), 2)

    def test_forwarded_header_ignored_without_trusted_proxy(self):
        s = self.start()
        for i in range(2):
            self.assertEqual(s.post(GOOD, headers={"X-Forwarded-For": f"203.0.113.{i}"})[0], 200)
        self.assertEqual(s.post(GOOD, headers={"X-Forwarded-For": "203.0.113.99"})[0], 429)

    def test_forwarded_header_used_only_from_trusted_proxy(self):
        s = self.start(ACTP_TRUSTED_PROXIES="127.0.0.1")
        for _ in range(2):
            self.assertEqual(s.post(GOOD, headers={"X-Forwarded-For": "203.0.113.5"})[0], 200)
        self.assertEqual(s.post(GOOD, headers={"X-Forwarded-For": "203.0.113.5"})[0], 429)
        # another real client behind the same trusted proxy has its own budget
        self.assertEqual(s.post(GOOD, headers={"X-Forwarded-For": "203.0.113.6"})[0], 200)
        # a spoofed leading hop does not mint a new identity: the right-most untrusted hop wins
        self.assertEqual(s.post(GOOD, headers={"X-Forwarded-For": "198.51.100.1, 203.0.113.5"})[0], 429)

    def test_global_limit(self):
        s = self.start(ACTP_RATE_IP_MAX="50", ACTP_RATE_GLOBAL_MAX="2", ACTP_TRUSTED_PROXIES="127.0.0.1")
        self.assertEqual(s.post(GOOD, headers={"X-Forwarded-For": "203.0.113.1"})[0], 200)
        self.assertEqual(s.post(GOOD, headers={"X-Forwarded-For": "203.0.113.2"})[0], 200)
        self.assertEqual(s.post(GOOD, headers={"X-Forwarded-For": "203.0.113.3"})[0], 429)

    def test_state_is_outside_web_root_and_private(self):
        s = self.start()
        s.post(GOOD)
        state = self.tmp / "state"
        self.assertTrue((state / "ratelimit.json").is_file())
        self.assertFalse(str(state).startswith(str(ROOT)))
        self.assertEqual(oct((state / "ratelimit.key").stat().st_mode & 0o777), "0o600")
        self.assertNotIn("127.0.0.1", (state / "ratelimit.json").read_text())

    def test_concurrent_requests_respect_limit(self):
        import concurrent.futures as cf
        s = self.start(ACTP_RATE_IP_MAX="3")
        with cf.ThreadPoolExecutor(8) as ex:
            codes = [f.result()[0] for f in [ex.submit(s.post, GOOD) for _ in range(8)]]
        self.assertEqual(codes.count(200), 3, codes)
        self.assertEqual(codes.count(429), 5, codes)


@unittest.skipUnless(PHP and VENDOR.is_file(), SKIP)
class DeploymentLayoutTests(unittest.TestCase):
    def test_default_owner_paths_without_env_overrides(self):
        tmp = Path(tempfile.mkdtemp(prefix="actp-layout-"))
        sb = Sandbox(tmp)
        proc = None
        try:
            home = tmp / "arriscom"
            docroot = home / "public_html" / "actpsb.com"
            docroot.mkdir(parents=True)
            (home / "actpsb-private").mkdir()
            shutil.copy(ROOT / "contact-submit.php", docroot)
            shutil.copy(ROOT / "contact.html", docroot)
            (home / "actpsb-backend").symlink_to(ROOT / "backend")
            port = free_port()
            (home / "actpsb-private" / "config.php").write_text(
                "<?php return ['smtp_host'=>'localhost','smtp_port'=>%d,'smtp_secure'=>'tls','smtp_user'=>'%s',"
                "'smtp_pass'=>'%s','smtp_ca_file'=>'%s','mail_from'=>'mailbox@sandbox.test',"
                "'mail_to'=>'inbox@sandbox.test','allowed_origins'=>['http://127.0.0.1:%d']];"
                % (sb.port, sb.user, sb.password, sb.crt, port))
            env = {k: v for k, v in os.environ.items() if not k.startswith("ACTP_")}
            proc = subprocess.Popen([PHP, "-S", f"127.0.0.1:{port}", "-t", str(docroot)], env=env,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(docroot))
            for _ in range(200):
                try:
                    socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                    break
                except OSError:
                    time.sleep(0.05)
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/contact-submit.php", data=urllib.parse.urlencode(GOOD).encode(),
                headers={"Origin": f"http://127.0.0.1:{port}", "Accept": "application/json",
                         "Content-Type": "application/x-www-form-urlencoded"}, method="POST")
            with OPENER.open(req, timeout=30) as r:
                self.assertEqual(json.loads(r.read())["status"], "accepted")
            self.assertEqual(len(sb.messages), 1)
            self.assertTrue((home / "actpsb-private" / "var").is_dir())
        finally:
            if proc:
                proc.terminate()
                proc.wait(5)
            sb.close()
            shutil.rmtree(tmp, ignore_errors=True)


@unittest.skipUnless(PHP and VENDOR.is_file(), SKIP)
class PackageTests(unittest.TestCase):
    def test_zips_install_into_owner_layout_and_work_without_composer(self):
        import zipfile
        cphar = os.environ.get("ACTP_COMPOSER") or shutil.which("composer")
        if not cphar:
            self.skipTest("composer unavailable for building packages")
        sys.path.insert(0, str(ROOT / "scripts"))
        import build_packages
        tmp = Path(tempfile.mkdtemp(prefix="actp-pkg-"))
        sb = Sandbox(tmp)
        proc = None
        try:
            build_packages.build(tmp / "dist")
            home = tmp / "home" / "arriscom"
            docroot = home / "public_html" / "actpsb.com"
            for name, dest in (("public", docroot), ("backend", home / "actpsb-backend"), ("private", home / "actpsb-private")):
                dest.mkdir(parents=True)
                zipfile.ZipFile(tmp / "dist" / f"actpsb-{name}.zip").extractall(dest)
            (home / "actpsb-private").chmod(0o700)
            names = [n for z in (tmp / "dist").glob("*.zip") for n in zipfile.ZipFile(z).namelist()]
            self.assertIn("vendor/autoload.php", names)
            self.assertFalse([n for n in names if n.startswith((".git", "tests/", "dist/", "docs/")) or n.endswith((".env", ".pem", ".key"))])
            self.assertFalse([n for n in names if "composer.phar" in n or "installer" in n.lower()])
            self.assertIn("contact-submit.php", names)
            port = free_port()

            def run(expect_status, expect_msg=None):
                nonlocal proc
                if proc:
                    proc.terminate()
                    proc.wait(5)
                env = {k: v for k, v in os.environ.items() if not k.startswith("ACTP_")}
                proc = subprocess.Popen([PHP, "-S", f"127.0.0.1:{port}", "-t", str(docroot)], env=env,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(docroot))
                for _ in range(200):
                    try:
                        socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                        break
                    except OSError:
                        time.sleep(0.05)
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/contact-submit.php", data=urllib.parse.urlencode(GOOD).encode(),
                    headers={"Origin": f"http://127.0.0.1:{port}", "Accept": "application/json",
                             "Content-Type": "application/x-www-form-urlencoded"}, method="POST")
                try:
                    r = OPENER.open(req, timeout=30)
                except urllib.error.HTTPError as e:
                    r = e
                self.assertEqual(r.status, expect_status)
                return json.loads(r.read())

            # as shipped: placeholder password => fails closed, nothing sent
            self.assertEqual(run(503)["status"], "unavailable")
            self.assertEqual(sb.messages, [])
            cfgp = home / "actpsb-private" / "config.php"
            cfg = cfgp.read_text()
            self.assertIn("contact@actpsb.com", cfg)
            self.assertIn("CONFIRM_SET_PASSWORD_ON_SERVER_ONLY", cfg)
            # simulate the owner's File Manager edit with synthetic sandbox values
            cfgp.write_text("<?php return ['smtp_host'=>'localhost','smtp_port'=>%d,'smtp_secure'=>'tls','smtp_user'=>'%s',"
                            "'smtp_pass'=>'%s','smtp_ca_file'=>'%s','mail_from'=>'mailbox@sandbox.test',"
                            "'mail_to'=>'inbox@sandbox.test','allowed_origins'=>['http://127.0.0.1:%d']];"
                            % (sb.port, sb.user, sb.password, sb.crt, port))
            self.assertEqual(run(200)["status"], "accepted")
            self.assertEqual(len(sb.messages), 1)
            self.assertTrue((home / "actpsb-private" / "var").is_dir())
        finally:
            if proc:
                proc.terminate()
                proc.wait(5)
            sb.close()
            shutil.rmtree(tmp, ignore_errors=True)


class PublicSurfaceTests(unittest.TestCase):
    def test_no_secrets_or_private_files_tracked(self):
        try:
            tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True,
                                     check=True).stdout.split()
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("git metadata unavailable")
        self.assertFalse([t for t in tracked if t.endswith("config.php")])
        self.assertFalse([t for t in tracked if t.startswith("backend/vendor/")])
        self.assertFalse([t for t in tracked if t.endswith((".env", ".key", ".pem"))])

    def test_public_js_has_no_server_values(self):
        js = (ROOT / "assets/js/contact-form.js").read_text(encoding="utf-8")
        self.assertNotRegex(js, r"(?i)smtp|password|[a-z0-9._-]+@[a-z0-9.-]+\.[a-z]{2,}")
        self.assertIn("contact-submit.php", (ROOT / "contact.html").read_text(encoding="utf-8"))

    def test_template_is_placeholder_only(self):
        text = (ROOT / "backend/config/config.example.php").read_text(encoding="utf-8")
        self.assertIn("CONFIRM_", text)
        self.assertNotRegex(text, r"(?i)pass'\s*=>\s*'(?!CONFIRM_)")

    def test_composer_lock_pins_phpmailer_and_license_present(self):
        lock = json.loads((ROOT / "backend/composer.lock").read_text())
        pkgs = {p["name"]: p for p in lock["packages"]}
        version = pkgs["phpmailer/phpmailer"]["version"]
        self.assertRegex(version, r"^v6\.\d+\.\d+$")
        req = json.loads((ROOT / "backend/composer.json").read_text())["require"]["phpmailer/phpmailer"]
        self.assertEqual(req, version.lstrip("v"))
        lic = (ROOT / "backend/licenses/PHPMailer-LGPL-2.1.txt").read_text()
        self.assertIn("GNU LESSER GENERAL PUBLIC LICENSE", lic)

    @unittest.skipUnless(PHP, "php unavailable")
    def test_php_lint(self):
        files = [*ROOT.glob("backend/src/*.php"), *ROOT.glob("backend/config/*.php"), ROOT / "contact-submit.php"]
        self.assertGreaterEqual(len(files), 10)
        for f in files:
            r = subprocess.run([PHP, "-l", str(f)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{f}: {r.stdout}{r.stderr}")


if __name__ == "__main__":
    unittest.main()
