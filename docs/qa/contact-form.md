# Contact Page Verification

Updated 22 October 2026 for the Contact redesign. Chromium browser checks used a real local PHP server and the existing synthetic SMTP sandbox, which captures messages locally and relays nothing. No production mailbox, credentials or deployment were used. This is not a screen-reader, cross-browser or formal accessibility conformance audit.

| State | Result |
|---|---|
| Unconfigured or disabled | JavaScript reveals all fields for local preview; backend preflight, native form route and POST still fail closed. Submission does not fabricate success. |
| Configured and enabled, JS on | Fields appear immediately with all five enquiry categories, without waiting for preflight. |
| Empty submission | Four linked field errors for name, email, category and message; `role="alert"`, status focus and `aria-invalid` associations. |
| Two immediate submit attempts | One POST. Button is disabled while processing and restored afterward. |
| Accepted synthetic SMTP submission | Exact server-confirmed success message, `role="status"`, form reset, browser remains on Contact. No inbox-delivery claim. |
| Network failure | Entered message/category retained; button restored; submission status explicitly unconfirmed, with published contact alternatives. |
| JavaScript disabled | Static page keeps the inert template; availability link renders the native form. Invalid email preserves name/category and renders linked field errors. Corrected POST renders the success view without a form. |
| Keyboard/mobile menu | Visible 3px input focus outline; menu opens and closes with Escape. |

Both available and unavailable layouts were checked at 320, 390, 768, 1024 and 1440 pixels: no horizontal overflow; contact details stack above the form below 768 pixels. Fields and submission controls have at least 44px touch height. Desktop and mobile screenshots were reviewed. The existing header, logo and footer layout remain; public footer contact details consistently use the attributed NSX group listing.

All 51 tests in `test_contact_backend` pass, including TLS acceptance/refusal, category allowlisting and array/header-injection rejection, safe native output, honeypot, same-origin, rate limits, private logs and packaged cPanel layout. Existing valid configurations without the newer enable flag remain operational; explicit disablement and missing configuration still fail closed. Six focused footer/Contact/shared-shell tests also pass. No real inbox delivery is verified. The example configuration stays explicitly disabled until an authorised staging/maintenance inbox test. See `contact-backend.md`.
