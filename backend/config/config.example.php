<?php
/*
 * NON-SECRET PLACEHOLDER TEMPLATE. Copy to <private dir>/config.php OUTSIDE public_html
 * (for example /home/CPANELUSER/actp-private/config.php), chmod 600, then replace every
 * value. Never commit the real file. Placeholders below fail validation on purpose, so the
 * form stays unavailable until real values are set.
 *
 * Alternatively set the same keys as ACTP_* environment variables (see docs/contact-backend.md).
 */
return [
    // Authenticated SMTP of the domain mailbox. Port 587 = STARTTLS, 465 = implicit TLS.
    // Certificate and host name are always verified; plaintext SMTP is not supported.
    'smtp_host'   => 'mail.example.invalid',
    'smtp_port'   => 587,
    'smtp_secure' => 'tls',            // 'tls' (STARTTLS) or 'ssl' (implicit TLS)
    'smtp_user'   => 'CONFIRM_MAILBOX_USERNAME',
    'smtp_pass'   => 'CONFIRM_MAILBOX_PASSWORD',

    // The domain mailbox is the From address; the visitor address is only ever Reply-To.
    'mail_from'      => 'CONFIRM_DOMAIN_MAILBOX@example.invalid',
    'mail_from_name' => 'Website enquiries',
    // Fixed recipient. Must be confirmed by ACTP; the server never takes a recipient from a request.
    'mail_to'        => 'CONFIRM_RECIPIENT@example.invalid',

    // Exact origins allowed to POST (scheme + host, no path). https only except localhost.
    'allowed_origins' => ['https://CONFIRM_HOSTING_ORIGIN.example.invalid'],

    // Only list proxies/CDN ranges that sit directly in front of PHP. Empty = never trust X-Forwarded-For.
    'trusted_proxies' => [],

    // Optional. Rate limit state and event log directory (default <private dir>/var). Keep outside public_html.
    // 'state_dir' => '/home/CPANELUSER/actp-private/var',
    // 'rate_ip_max' => 5, 'rate_ip_window' => 600, 'rate_global_max' => 100, 'rate_global_window' => 3600,
];
