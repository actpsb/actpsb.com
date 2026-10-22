# ACTP Website

This folder contains ACTP Sdn Bhd's five-page website and its enquiry form.

The pages are ordinary HTML files: they hold the words, images and links visitors see. CSS files control how the pages look. JavaScript adds the mobile menu, gentle animations and form interactions. PHP runs on the web server and sends enquiries through the company's mail server.

There is no frontend framework, database or website compilation step. You do not need Node.js or npm to preview or publish the pages.

## Where To Make Changes

| What you want to change | Where to look |
| --- | --- |
| Words, links or pictures on a page | The matching HTML file in the next section. |
| Colours, fonts or standard spacing | [assets/css/tokens.css](assets/css/tokens.css). |
| Shared header, footer, cards or page layouts | [assets/css/components.css](assets/css/components.css). |
| Contact form appearance | [assets/css/contact-form.css](assets/css/contact-form.css). |
| Mobile menu behaviour | [assets/js/main.js](assets/js/main.js). |
| What happens after pressing Send Enquiry | [assets/js/contact-form.js](assets/js/contact-form.js) and the PHP files listed below. |
| Mail login, sender or receiving address | The hosting account's private configuration, outside the public website folder. Do not put passwords in HTML or JavaScript. |

Each HTML page has its own copy of the header and footer. When changing shared navigation or footer wording, update all five pages. Automated checks help catch differences.

## Pages And Public Files

These files belong in the public website folder on the hosting account.

| File | What it does |
| --- | --- |
| [index.html](index.html) | Home page: introduces ACTP, its services, approach and selected company milestones. |
| [about.html](about.html) | About Us page: explains ACTP's background, credentials and approach. |
| [services.html](services.html) | Services page: describes the NSX adviser role and advisory capabilities. |
| [insights.html](insights.html) | Insights page: presents company milestones and adviser relationships, with source links. It is not an empty news page. |
| [contact.html](contact.html) | Contact details and the enquiry form's labels, fields and choices. |
| [contact-submit.php](contact-submit.php) | Receives enquiries and hands them to the private PHP backend. It contains no mail password. |
| [robots.txt](robots.txt) | Tells search engines that they may visit the site. It does not secure private files. |
| [favicon.ico](favicon.ico) | Small website icon shown in browser tabs. |

The former standalone NSX adviser page is no longer part of the site. Its relevant information is on Home and Services; do not restore old navigation links to it.

## Appearance And Browser Behaviour

All pages load the first four stylesheets in the order listed. Contact also loads its own stylesheet and script.

| File | What it does |
| --- | --- |
| [assets/css/tokens.css](assets/css/tokens.css) | The site's shared settings: colour values, font choices, spacing and screen-size adjustments. |
| [assets/css/base.css](assets/css/base.css) | Basic rules for text, links, images, keyboard focus and reduced animation. |
| [assets/css/layout.css](assets/css/layout.css) | Page widths, section backgrounds and spacing, plus the keyboard skip link. |
| [assets/css/components.css](assets/css/components.css) | Shared navigation, buttons, footer, company cards and the current page layouts. |
| [assets/css/contact-form.css](assets/css/contact-form.css) | Contact panels, textboxes, dropdown, button and form messages. |
| [assets/js/main.js](assets/js/main.js) | Opens and closes the mobile menu and reveals selected sections as visitors scroll. Content remains readable without these animations. |
| [assets/js/contact-form.js](assets/js/contact-form.js) | Makes the enquiry fields visible immediately, sends the form to PHP, shows returned errors or confirmation, and prevents repeated clicks while sending. |

## Pictures And Documents

These are real project assets, not disposable code. Keep the original logo even though the smaller version is normally shown in navigation. Similarly named files can serve different purposes.

| File | What it is used for |
| --- | --- |
| [assets/actp-logo.png](assets/actp-logo.png) | Original supplied ACTP logo, retained as the source and checked by tests. |
| [assets/actp-logo-432.png](assets/actp-logo-432.png) | Smaller ACTP logo used in the shared header. |
| [assets/images/actp-logo.png](assets/images/actp-logo.png) | Large transparent ACTP logo used in the About page's opening section. |
| [assets/hero-growth.png](assets/hero-growth.png) | Home page's opening illustration. |
| [assets/hero-teammwork.png](assets/hero-teammwork.png) | Home page's company-introduction illustration. The filename keeps its existing spelling to avoid breaking links. |
| [assets/section-discover.png](assets/section-discover.png) | Discover-stage illustration, also used in the Insights opening section. |
| [assets/section-strategy.png](assets/section-strategy.png) | Strategy-stage illustration, also used in the Services opening section. |
| [assets/section-execution.png](assets/section-execution.png) | Execute-stage illustration on Home. |
| [assets/section-support.png](assets/section-support.png) | Support-stage illustration on Home. |
| [assets/images/nuren-group-logo.png](assets/images/nuren-group-logo.png) | Nuren company logo for Home and Insights. |
| [assets/images/actelerate-international-group-logo.png](assets/images/actelerate-international-group-logo.png) | Supplied Actcelerate company logo for Home and Insights. The filename keeps its existing spelling. |
| [assets/images/arris-holding-logo.png](assets/images/arris-holding-logo.png) | Arris company logo on Insights. |
| [assets/images/sydney-sunny-glass-logo.png](assets/images/sydney-sunny-glass-logo.png) | Sydney Sunny Glass company logo on Insights. |
| [assets/documents/nuren-group-nsx-admission.pdf](assets/documents/nuren-group-nsx-admission.pdf) | Supporting NSX admission letter retained as evidence for Nuren's milestone dates; not currently linked from a public page. |

## Contact Form: Display Versus Sending

Seeing the textboxes does not require mail settings. With JavaScript enabled, they appear immediately, including on a local preview. Without JavaScript, the page provides a link to the form rendered by PHP.

Actually sending an enquiry needs PHP, the installed email library and valid private mail settings. SMTP means the mail server the website logs into to send messages. The browser never receives that login information.

The backend checks the enquiry, blocks obvious spam and sends only to the configured recipient. It reports success only when the mail server accepts the message. Acceptance is not proof that the message reached an inbox; check the receiving mailbox when testing the hosted website.

Existing valid mail configurations do not need the newer `form_enabled` setting added. An explicit `false`, or `ACTP_FORM_ENABLED=0`, still switches sending off. The supplied example is deliberately disabled and has a placeholder password; it must not replace an already-working private configuration.

The local preview has no real mail configuration. Automated mail tests use a local test server and do not send enquiries to anyone. A public availability-check address remains for troubleshooting, but showing the fields no longer waits for that check.

### Private PHP Backend

These files run on the server, not in the visitor's browser. In the hosted layout, the backend and private configuration stay outside the public website folder. Do not delete them just because no HTML page links directly to them.

| File | What it does |
| --- | --- |
| [backend/composer.json](backend/composer.json) | Lists PHP requirements and the email library the backend needs. Composer is the tool that downloads that library. |
| [backend/composer.lock](backend/composer.lock) | Records the exact library version so installs use the same tested code. Keep it. |
| [backend/config/config.example.php](backend/config/config.example.php) | Non-secret example of the private mail settings. It is a starting point for a new setup, not a working login. |
| [backend/src/Handler.php](backend/src/Handler.php) | Coordinates an enquiry: configuration, request checks, spam checks, validation, sending and the final response. |
| [backend/src/Config.php](backend/src/Config.php) | Loads and checks the private mail settings. |
| [backend/src/ConfigException.php](backend/src/ConfigException.php) | Signals a configuration problem using a safe error code, without exposing passwords. |
| [backend/src/Validator.php](backend/src/Validator.php) | Checks required fields, email format, enquiry category and message length. |
| [backend/src/ClientIp.php](backend/src/ClientIp.php) | Identifies the visitor's network address safely, including when an approved proxy sits in front of the site. |
| [backend/src/RateLimiter.php](backend/src/RateLimiter.php) | Limits repeated submissions to reduce spam and abuse. |
| [backend/src/SmtpSender.php](backend/src/SmtpSender.php) | Sends the enquiry through an authenticated, encrypted mail connection. |
| [backend/src/SendFailure.php](backend/src/SendFailure.php) | Signals a sending problem without showing private mail-server details to visitors. |
| [backend/src/EventLog.php](backend/src/EventLog.php) | Writes short troubleshooting codes privately, without saving enquiry text or credentials in the log. |
| [backend/src/Response.php](backend/src/Response.php) | Holds the response status, headers and content sent back to the browser. |
| [backend/src/Page.php](backend/src/Page.php) | Builds the form/results page for visitors who submit without JavaScript, using the site's existing Contact layout. |
| [backend/licenses/PHPMailer-LGPL-2.1.txt](backend/licenses/PHPMailer-LGPL-2.1.txt) | Licence notice for the external email library. Retain it when distributing the backend. |

Composer also creates `backend/vendor/`, containing the downloaded library and its automatic loader. Those generated files are not maintained by hand or committed to this repository. They are included in the backend upload package.

## Project Notes

These Markdown files are guidance for people maintaining the site, not pages visitors see.

| File | What it explains |
| --- | --- |
| [README.md](README.md) | This plain-language project guide. |
| [docs/project-brief.md](docs/project-brief.md) | The supplied project requirements and original design brief. |
| [docs/architecture.md](docs/architecture.md) | The original page plan and development process. Some headings and layouts describe an earlier version; use the current HTML and this guide for today's file map. |
| [docs/design-system.md](docs/design-system.md) | The design decisions behind colours, fonts, spacing and interactions, including earlier design notes. Actual settings live in CSS. |
| [docs/content-sources.md](docs/content-sources.md) | Where company claims and public contact details came from, and what needs confirmation. |
| [docs/insights-pattern.md](docs/insights-pattern.md) | Sources for the company profiles and rules for adding approved articles later. |
| [docs/contact-backend.md](docs/contact-backend.md) | Detailed mail setup, private folder locations, troubleshooting and deployment instructions. |
| [docs/seo.md](docs/seo.md) | Search-engine titles, descriptions, sharing information and hosting-dependent items still to confirm. SEO means making pages understandable to search engines. |
| [docs/qa/contact-form.md](docs/qa/contact-form.md) | Contact form test results and the limits of local mail testing. |
| [docs/qa/homepage-qa.md](docs/qa/homepage-qa.md) | Recorded homepage checks on different screen sizes. |
| [docs/qa/accessibility-audit.md](docs/qa/accessibility-audit.md) | Earlier checks for keyboard access, readable contrast and other accessibility concerns. |
| [docs/qa/performance.md](docs/qa/performance.md) | Earlier loading-speed measurements and hosting recommendations. |

QA means quality assurance: checking that the site behaves as intended. The dated reports and screenshots are historical evidence, not a guarantee about the latest version. Older reports mention the removed NSX page because it existed when those checks were done.

### Saved Screenshots

These files record earlier browser checks. They are not loaded by the website.

| File | What it records |
| --- | --- |
| [docs/qa/screenshots/home-320.png](docs/qa/screenshots/home-320.png) | Home at a very narrow mobile width. |
| [docs/qa/screenshots/home-375.png](docs/qa/screenshots/home-375.png) | Home at a typical mobile width. |
| [docs/qa/screenshots/home-768.png](docs/qa/screenshots/home-768.png) | Home at tablet width. |
| [docs/qa/screenshots/home-1024.png](docs/qa/screenshots/home-1024.png) | Home at a small desktop width. |
| [docs/qa/screenshots/home-1440.png](docs/qa/screenshots/home-1440.png) | Home at a wide desktop width. |
| [docs/qa/screenshots/viewport-320-top.png](docs/qa/screenshots/viewport-320-top.png) | The top of the page at narrow mobile width. |
| [docs/qa/screenshots/menu-open-375.png](docs/qa/screenshots/menu-open-375.png) | Mobile navigation open. |
| [docs/qa/screenshots/menu-open-768.png](docs/qa/screenshots/menu-open-768.png) | Tablet navigation open. |
| [docs/qa/screenshots/nojs-375.png](docs/qa/screenshots/nojs-375.png) | Mobile layout with JavaScript disabled. |
| [docs/qa/screenshots/nojs-1440.png](docs/qa/screenshots/nojs-1440.png) | Desktop layout with JavaScript disabled. |
| [docs/qa/screenshots/focus-visible-1440.png](docs/qa/screenshots/focus-visible-1440.png) | Visible keyboard focus on desktop. |
| [docs/qa/screenshots/reduced-motion-1440.png](docs/qa/screenshots/reduced-motion-1440.png) | Desktop layout with reduced animation requested. |

## Tests, Packaging And Repository Settings

These support development and publishing; they are not public website pages.

| File | What it does |
| --- | --- |
| [tests/test_site.py](tests/test_site.py) | Checks page structure, navigation, assets, design rules, Contact markup and a basic local server. Also provides the HTML reader reused by SEO tests. |
| [tests/test_seo.py](tests/test_seo.py) | Checks the five pages' search/sharing information, headings, image dimensions and internal links. |
| [tests/test_contact_backend.py](tests/test_contact_backend.py) | Tests real PHP request handling, validation, mail acceptance/failure, security checks and the upload ZIPs using synthetic data. |
| [tests/smtp_sandbox.py](tests/smtp_sandbox.py) | A temporary local mail server for tests. It keeps test messages in memory and never forwards them externally. |
| [tests/test_accessibility_audit.py](tests/test_accessibility_audit.py) | Checks that the historical accessibility report contains its required evidence and limitations. It is not a fresh browser accessibility audit. |
| [scripts/build_packages.py](scripts/build_packages.py) | Creates three upload ZIPs: public website, private backend with its email library, and a separate example configuration. It does not upload anything. |
| [.github/workflows/ci.yml](.github/workflows/ci.yml) | GitHub's automated checks: installs PHP dependencies, checks PHP syntax, runs tests and creates downloadable ZIPs. It does not deploy the website. |
| [.gitignore](.gitignore) | Keeps downloaded libraries, local passwords, generated ZIPs and temporary files out of version control. This is not a substitute for keeping secrets outside the public folder. |

Generated folders such as `backend/vendor/`, `dist/`, `__pycache__/` and `.pytest_cache/` can be recreated. The hidden `.git/` folder holds repository history; do not delete it as part of a website cleanup.

## Preview Locally

Run these commands from the folder containing this README. You need PHP 8.1 or newer with the OpenSSL and mbstring extensions, plus Composer for the email library.

```sh
composer install --working-dir=backend --no-interaction --prefer-dist
ACTP_BACKEND_DIR="$PWD/backend" ACTP_PRIVATE_DIR="$(dirname "$PWD")/actpsb-private" php -S 127.0.0.1:8001 -t .
```

Open [the local site](http://127.0.0.1:8001/) or [Contact](http://127.0.0.1:8001/contact.html). Use another port if 8001 is already occupied. Press Ctrl+C in the server terminal to stop it.

You can review the page layout and textboxes without private mail settings. To test actual sending locally, a maintainer must set up a separate private test configuration; see [docs/contact-backend.md](docs/contact-backend.md). Never place production passwords in the public folder or paste them into chat.

## Run Checks

Python 3 runs the tests without extra Python packages. Full mail tests also need PHP, the installed backend library and the `openssl` command. Package tests need Composer. Read any reported skips: a skipped mail test does not prove delivery works.

```sh
python3 -m unittest discover -s tests -v
```

Tests cover code and page rules, not every visual detail. After changing shared styles or navigation, also check desktop and mobile layouts, keyboard navigation and the visible Contact fields in a browser. A real hosted inbox test is separate from the local test mail server.

## Publish To The Hosted Site

For the existing working host, back up the site and keep its private mail configuration unchanged. Do not replace that configuration with the disabled example.

Build the upload packages locally:

```sh
python3 scripts/build_packages.py
```

The generated `dist/` folder contains:

| Package | Where it belongs in the documented hosting setup |
| --- | --- |
| `actpsb-public.zip` | Extract inside `/home/arriscom/public_html/actpsb.com`. Contains the five pages, assets, icon and public PHP entry point. |
| `actpsb-backend.zip` | Extract inside `/home/arriscom/actpsb-backend`, outside the public folder. Contains server code and the installed email library. |
| `actpsb-private.zip` | For a new setup only: extract inside `/home/arriscom/actpsb-private`. Contains an example configuration, not working credentials. Do not overwrite an existing working configuration. |

These paths describe the existing hosting plan; a different account needs its own paths. The detailed steps and configuration checklist are in [docs/contact-backend.md](docs/contact-backend.md).

A Git push runs the configured GitHub checks and produces packages; this repository's workflow does not publish them to the hosting account. After deploying matching public and backend packages, verify the live pages and confirm a test enquiry reaches the intended mailbox.
