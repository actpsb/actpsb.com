<?php
declare(strict_types=1);

/*
 * Public same-origin endpoint for the contact form. It holds no secrets and no logic beyond wiring.
 * The backend (vendor/, src/) and the private configuration live OUTSIDE the public web root.
 * Locations default to siblings of the web root and can be set with ACTP_BACKEND_DIR / ACTP_PRIVATE_DIR.
 * See docs/contact-backend.md.
 */

// cPanel add-on domains use /home/USER/public_html/DOMAIN, where the parent is itself web-served:
// in that case the backend belongs in the account home, two levels up.
$home = basename(dirname(__DIR__)) === 'public_html' ? dirname(__DIR__, 2) : dirname(__DIR__);
$backend = getenv('ACTP_BACKEND_DIR') ?: $home . '/actpsb-backend';
$private = getenv('ACTP_PRIVATE_DIR') ?: $home . '/actpsb-private';

header_remove('X-Powered-By');
$autoload = $backend . '/vendor/autoload.php';
if (!is_file($autoload)) {
    http_response_code(503);
    header('Content-Type: text/plain; charset=utf-8');
    header('Cache-Control: no-store');
    echo "The enquiry form is not available yet, so no message was sent.\n";
    exit;
}
require $autoload;

$env = [];
foreach (array_keys(getenv()) as $k) {
    if (is_string($k) && str_starts_with($k, 'ACTP_')) {
        $v = getenv($k);
        if (is_string($v)) {
            $env[$k] = $v;
        }
    }
}
$handler = new Actp\Contact\Handler(__DIR__, $private, $env);
$response = $handler->handle($_SERVER, $_POST);
http_response_code($response->status);
foreach ($response->headers as $name => $value) {
    header($name . ': ' . $value);
}
echo $response->body;
