"""Contract tests for the contact form script's pure logic (validation and response interpretation).

They run assets/js/contact-form.js under node with no DOM, network or mail server. The PHP-driven
tests in test_contact_backend.py feed real backend responses through the same functions.
Skipped when node is unavailable (CI provides it).
"""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")
JS = ROOT / "assets" / "js" / "contact-form.js"

DRIVER = """
const api = require(process.argv[1]);
const cases = JSON.parse(process.argv[2]);
const out = cases.map(c => c.fn === "validate" ? api.validate(c.v) : api.interpret(c.status, c.body, !!c.net));
process.stdout.write(JSON.stringify(out));
"""

GOOD = {"name": "Synthetic Tester", "email": "visitor@example.test", "organisation": "",
        "category": "General Enquiry", "message": "This is a synthetic test message."}


def run(cases):
    p = subprocess.run([NODE, "-e", DRIVER, str(JS), json.dumps(cases)], capture_output=True, text=True, timeout=30)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)


def interpret(status, body, net=False):
    return run([{"fn": "interpret", "status": status, "body": body, "net": net}])[0]


@unittest.skipUnless(NODE, "node unavailable")
class ClientValidationTests(unittest.TestCase):
    def test_valid_submission_has_no_errors(self):
        self.assertEqual(run([{"fn": "validate", "v": GOOD}])[0], {})

    def test_short_message_is_a_validation_error_not_a_delivery_problem(self):
        e = run([{"fn": "validate", "v": {**GOOD, "message": "test"}}])[0]
        self.assertEqual(list(e), ["message"])
        self.assertIn("at least 10", e["message"])

    def test_whitespace_padding_does_not_satisfy_minimum(self):
        e = run([{"fn": "validate", "v": {**GOOD, "message": "   test      \r\n  "}}])[0]
        self.assertIn("message", e)

    def test_required_fields_email_category_and_limits(self):
        e = run([{"fn": "validate", "v": {"name": "", "email": "nope", "organisation": "o" * 151,
                                            "category": "Other", "message": "x" * 5001}}])[0]
        self.assertEqual(sorted(e), ["category", "email", "message", "name", "organisation"])


@unittest.skipUnless(NODE, "node unavailable")
class ResponseInterpretationTests(unittest.TestCase):
    def test_accepted_requires_200_and_json(self):
        r = interpret(200, json.dumps({"status": "accepted", "message": "Thank you.", "reference": "abc"}))
        self.assertEqual((r["state"], r["message"]), ("accepted", "Thank you."))

    def test_accepted_body_with_error_status_is_not_success(self):
        self.assertEqual(interpret(500, json.dumps({"status": "accepted", "message": "x"}))["state"], "unconfirmed")

    def test_server_validation_errors_are_shown_per_field(self):
        r = interpret(422, json.dumps({"status": "invalid", "message": "Fix.", "errors": {"message": "Too short"}, "reference": "r1"}))
        self.assertEqual(r["state"], "invalid")
        self.assertEqual(r["errors"], {"message": "Too short"})
        self.assertEqual(r["reference"], "r1")

    def test_older_backend_json_without_errors_or_reference(self):
        r = interpret(503, json.dumps({"status": "unavailable", "message": "Not available. Not submitted."}))
        self.assertEqual((r["state"], r["message"]), ("unavailable", "Not available. Not submitted."))

    def test_json_without_message_gets_truthful_default(self):
        r = interpret(422, json.dumps({"status": "invalid"}))
        self.assertIn("not sent", r["message"])

    def test_html_error_page_is_not_success_and_names_status(self):
        r = interpret(404, "<html><body>Not Found</body></html>")
        self.assertEqual(r["state"], "rejected")
        self.assertIn("not sent", r["message"])
        self.assertIn("404", r["message"])

    def test_plain_text_503_from_older_endpoint_is_not_sent(self):
        r = interpret(503, "The enquiry form is not available yet, so no message was sent.\n")
        self.assertEqual(r["state"], "rejected")
        self.assertIn("not sent", r["message"])

    def test_ambiguous_cases_say_unconfirmed_and_never_not_sent(self):
        for status, body in ((200, "<html>proxy page</html>"), (200, ""), (200, "null"), (200, "[]"),
                             (500, "<h1>Fatal error</h1>"), (502, "Bad gateway"), (504, ""),
                             (200, json.dumps({"message": "no status"}))):
            r = interpret(status, body)
            self.assertEqual(r["state"], "unconfirmed", (status, body))
            self.assertIn("could not confirm", r["message"])
            self.assertNotIn("was not sent", r["message"])

    def test_network_error_or_timeout_is_unconfirmed(self):
        r = interpret(0, "", net=True)
        self.assertEqual(r["state"], "unconfirmed")
        self.assertIn("before resubmitting", r["message"])

    def test_script_never_retries_automatically(self):
        js = JS.read_text(encoding="utf-8")
        self.assertEqual(js.count("fetch(form.getAttribute"), 1)
        self.assertNotRegex(js, r"setTimeout\([^)]*submit|\bretry\(")


if __name__ == "__main__":
    unittest.main()
