<?php
/*
 * NON-SECRET PLACEHOLDER TEMPLATE. Copy to <private dir>/config.php OUTSIDE public_html
 * (for example /home/CPANELUSER/actp-private/config.php), chmod 600, then replace every
 * value. Never commit the real file. The password placeholder fails validation on purpose, so the
 * form stays unavailable until real values are set.
 *
 * Alternatively set the same keys as ACTP_* environment variables (see docs/contact-backend.md).
 */
return [
    // Authenticated SMTP of the domain mailbox. Port 587 = STARTTLS, 465 = implicit TLS.
    // Certificate and host name are always verified; plaintext SMTP is not supported.
    'smtp_host'   => 'mail.actpsb.com',
    'smtp_port'   => 465,
    'smtp_secure' => 'ssl',            // 'ssl' = implicit TLS/SMTPS (owner-confirmed); 'tls' = STARTTLS
    'smtp_user'   => 'contact@actpsb.com',
    'smtp_pass'   => 'CONFIRM_SET_PASSWORD_ON_SERVER_ONLY',

    // The domain mailbox is the From address; the visitor address is only ever Reply-To.
    'mail_from'      => 'contact@actpsb.com',
    'mail_from_name' => 'Website enquiries',
    // Fixed recipient. Must be confirmed by ACTP; the server never takes a recipient from a request.
    'mail_to'        => 'contact@actpsb.com',

    // Exact origins allowed to POST (scheme + host, no path). https only except localhost.
    'allowed_origins' => ['https://actpsb.com'], // CONFIRM the exact live origin (www or not) before use

    // Only list proxies/CDN ranges that sit directly in front of PHP. Empty = never trust X-Forwarded-For.
    'trusted_proxies' => [],

    // Optional. Rate limit state and event log directory (default <private dir>/var). Keep outside public_html.
    // 'state_dir' => '/home/CPANELUSER/actp-private/var',
    // 'rate_ip_max' => 5, 'rate_ip_window' => 600, 'rate_global_max' => 100, 'rate_global_window' => 3600,
];
