# Contact form states (ACTP-022)

Local lab check, Chromium (CDP) against two `php -S` instances serving the repo root: one with no private configuration (production-like unconfigured) and one with synthetic `ACTP_*` environment values pointing at an unreachable SMTP port. No real mailbox, mail server or deployment was used, and no message was delivered. This is not a conformance claim, not a screen reader or cross-browser test, and not evidence that production contact works.

| State | 375 and 1440 result |
|---|---|
| Unconfigured, JS on | Notice shown; no `form`, input, textarea or submit button in the rendered DOM |
| Unconfigured, JS off | Same notice; "Check whether the form is available" goes to `contact-submit.php?form=1`, which renders the 503 unavailable alert and no form |
| Configured, JS on | Preflight returns available; form revealed |
| Configured, JS off | Notice stays (the form is inert in the template); the check link renders the form server-side, with no stray status text |
| Configured, JS on, empty submit | `#form-status` (`role="alert"`) takes focus; three linked errors; name, email and message set `aria-invalid` |
| Configured, JS on, valid submit, SMTP unreachable | `#form-status` takes focus with "not sent ... Nothing has been delivered"; no success |

No horizontal overflow at 375 or 1440. `<main id="main" tabindex="-1">` and the 432x146 logo are present on the contact page.

SMTP acceptance, if it occurs in production, means only that the mail server accepted the message; it is not inbox delivery. An owner-run inbox test is still outstanding (`contact-backend.md`).
