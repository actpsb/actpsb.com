<?php
declare(strict_types=1);

namespace Actp\Contact;

/**
 * Request pipeline. Order is fixed: method, configuration (fail closed), content type and size,
 * same-origin, rate limit, honeypot, validation, SMTP send. Success is reported only after the
 * SMTP library returns success, and even then it means "accepted by the mail server", not delivered.
 */
final class Handler
{
    public const MAX_BODY = 16384;

    public function __construct(
        private string $publicDir,
        private string $privateDir,
        /** @var array<string,string> */
        private array $env,
        /** @var null|callable(Config,array<string,string>):void */
        private $sender = null,
    ) {
    }

    /**
     * @param array<string,mixed> $server
     * @param array<string,mixed> $post
     */
    public function handle(array $server, array $post): Response
    {
        $rid = bin2hex(random_bytes(5));
        $json = isset($server['HTTP_ACCEPT']) && is_string($server['HTTP_ACCEPT'])
            && str_contains($server['HTTP_ACCEPT'], 'application/json');
        $method = is_string($server['REQUEST_METHOD'] ?? null) ? $server['REQUEST_METHOD'] : '';

        if ($method !== 'POST') {
            return $this->out($json, 405, 'rejected', 'This address accepts form submissions only. Use the contact page.', [], [], $rid, false, ['Allow' => 'POST']);
        }

        try {
            $config = Config::load($this->privateDir, $this->env);
        } catch (ConfigException $e) {
            $this->log($rid, $e->getMessage(), null);
            return $this->out($json, 503, 'unavailable', 'The enquiry form is not available yet, so your message was not sent. Please use the NSX-listed details on this page instead.', [], [], $rid, false);
        }
        $log = new EventLog($config->v['state_dir']);

        $ctype = strtolower(trim(explode(';', is_string($server['CONTENT_TYPE'] ?? null) ? $server['CONTENT_TYPE'] : '')[0]));
        if (!in_array($ctype, ['application/x-www-form-urlencoded', 'multipart/form-data'], true)) {
            $log->write($rid, 'bad_content_type');
            return $this->out($json, 415, 'rejected', 'Your message was not sent because the request type is not supported.', [], [], $rid, false);
        }
        $len = $server['CONTENT_LENGTH'] ?? '0';
        if (!is_scalar($len) || !ctype_digit((string) $len) || (int) $len > self::MAX_BODY) {
            $log->write($rid, 'body_too_large');
            return $this->out($json, 413, 'rejected', 'Your message was not sent because it is too large.', [], [], $rid, false);
        }

        if (!$this->sameOrigin($server, $config->v['allowed_origins'])) {
            $log->write($rid, 'bad_origin');
            return $this->out($json, 403, 'rejected', 'Your message was not sent because the request did not come from this site\'s contact page.', [], [], $rid, false);
        }

        $ip = ClientIp::resolve($server, $config->v['trusted_proxies']);
        try {
            $rl = (new RateLimiter(
                $config->v['state_dir'],
                $config->v['rate_ip_max'],
                $config->v['rate_ip_window'],
                $config->v['rate_global_max'],
                $config->v['rate_global_window']
            ))->attempt($ip);
        } catch (\Throwable) {
            $log->write($rid, 'state_error');
            return $this->out($json, 503, 'unavailable', 'The enquiry form is temporarily unavailable, so your message was not sent. Please try again later.', [], [], $rid, false);
        }
        if (!$rl['ok']) {
            $log->write($rid, 'rate_limited');
            return $this->out($json, 429, 'rate_limited', 'Too many enquiries have been submitted recently, so your message was not sent. Please try again later.', [], $this->keep($post), $rid, true, ['Retry-After' => (string) $rl['retryAfter']]);
        }

        if (isset($post['website']) && $post['website'] !== '') {
            $log->write($rid, 'honeypot');
            return $this->out($json, 400, 'rejected', 'Your message could not be processed and was not sent.', [], [], $rid, true);
        }

        $res = Validator::validate($post);
        if ($res['errors'] !== []) {
            $log->write($rid, 'invalid');
            return $this->out($json, 422, 'invalid', 'Your message was not sent. Please correct the problems listed below.', $res['errors'], $res['values'], $rid, true);
        }

        try {
            $send = $this->sender ?? static function (Config $c, array $f): void {
                SmtpSender::send($c, $f);
            };
            $send($config, $res['values']);
        } catch (SendFailure $e) {
            $log->write($rid, $e->getMessage());
            return $this->out($json, 502, 'failed', 'Your message was not sent because the mail service did not accept it. Nothing has been delivered. Please try again later.', [], $res['values'], $rid, true);
        } catch (\Throwable) {
            $log->write($rid, 'send_error');
            return $this->out($json, 502, 'failed', 'Your message was not sent because the mail service did not accept it. Nothing has been delivered. Please try again later.', [], $res['values'], $rid, true);
        }
        $log->write($rid, 'smtp_accepted');
        return $this->out($json, 200, 'accepted', 'Your enquiry was accepted by our mail service for delivery. This is not a confirmation that it has been read or that anyone will reply.', [], [], $rid, false);
    }

    /** @param array<string,mixed> $server @param list<string> $allowed */
    private function sameOrigin(array $server, array $allowed): bool
    {
        $site = $server['HTTP_SEC_FETCH_SITE'] ?? null;
        if (is_string($site) && !in_array($site, ['same-origin', 'none'], true)) {
            return false;
        }
        $origin = $server['HTTP_ORIGIN'] ?? null;
        if (!is_string($origin) || $origin === '') {
            return false; // browsers send Origin on POST; absence is not accepted
        }
        return in_array(strtolower($origin), $allowed, true);
    }

    /** @param array<string,mixed> $post @return array<string,string> */
    private function keep(array $post): array
    {
        $o = [];
        foreach (['name', 'email', 'organisation', 'message'] as $k) {
            $o[$k] = is_string($post[$k] ?? null) ? mb_substr($post[$k], 0, Validator::MAX_MESSAGE, 'UTF-8') : '';
        }
        return $o;
    }

    private function log(string $rid, string $code, ?Config $c): void
    {
        // Without valid configuration there is no trusted state dir; use the private dir default.
        (new EventLog($this->privateDir . '/var'))->write($rid, $code);
    }

    /**
     * @param array<string,string> $errors
     * @param array<string,string> $values
     * @param array<string,string> $extra
     */
    private function out(bool $json, int $status, string $state, string $message, array $errors, array $values, string $rid, bool $showForm, array $extra = []): Response
    {
        $h = $extra + [
            'Cache-Control' => 'no-store',
            'X-Content-Type-Options' => 'nosniff',
            'Referrer-Policy' => 'same-origin',
            'X-Frame-Options' => 'DENY',
        ];
        if ($json) {
            $h['Content-Type'] = 'application/json; charset=utf-8';
            return new Response($status, $h, (string) json_encode([
                'status' => $state, 'message' => $message, 'errors' => (object) $errors, 'reference' => $rid,
            ], JSON_UNESCAPED_SLASHES));
        }
        $h['Content-Type'] = 'text/html; charset=utf-8';
        $h['Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'self'";
        return new Response($status, $h, Page::render($this->publicDir, $state, $message, $values, $errors, $rid, $showForm));
    }
}
