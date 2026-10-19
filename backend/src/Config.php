<?php
declare(strict_types=1);

namespace Actp\Contact;

/**
 * Private server configuration. Read from a PHP file kept outside the public web root
 * (default: <private dir>/config.php) and optionally overridden by ACTP_* environment variables.
 * Values are never echoed, logged or sent to the browser.
 */
final class Config
{
    private const ENV_MAP = [
        'ACTP_SMTP_HOST' => 'smtp_host',
        'ACTP_SMTP_PORT' => 'smtp_port',
        'ACTP_SMTP_SECURE' => 'smtp_secure',
        'ACTP_SMTP_USER' => 'smtp_user',
        'ACTP_SMTP_PASS' => 'smtp_pass',
        'ACTP_SMTP_CA_FILE' => 'smtp_ca_file',
        'ACTP_MAIL_FROM' => 'mail_from',
        'ACTP_MAIL_FROM_NAME' => 'mail_from_name',
        'ACTP_MAIL_TO' => 'mail_to',
        'ACTP_ALLOWED_ORIGINS' => 'allowed_origins',
        'ACTP_TRUSTED_PROXIES' => 'trusted_proxies',
        'ACTP_STATE_DIR' => 'state_dir',
        'ACTP_RATE_IP_MAX' => 'rate_ip_max',
        'ACTP_RATE_IP_WINDOW' => 'rate_ip_window',
        'ACTP_RATE_GLOBAL_MAX' => 'rate_global_max',
        'ACTP_RATE_GLOBAL_WINDOW' => 'rate_global_window',
    ];

    /** @param array<string,mixed> $v */
    private function __construct(public readonly array $v)
    {
    }

    /**
     * @param array<string,string> $env
     * @throws ConfigException with a fixed, value-free code
     */
    public static function load(string $privateDir, array $env): self
    {
        $values = [];
        $file = isset($env['ACTP_CONFIG_FILE']) && $env['ACTP_CONFIG_FILE'] !== ''
            ? $env['ACTP_CONFIG_FILE']
            : $privateDir . '/config.php';
        if (is_file($file)) {
            $loaded = (static function (string $f) {
                return require $f;
            })($file);
            if (is_array($loaded)) {
                $values = $loaded;
            }
        }
        foreach (self::ENV_MAP as $envKey => $key) {
            if (isset($env[$envKey]) && $env[$envKey] !== '') {
                $values[$key] = $env[$envKey];
            }
        }
        if ($values === []) {
            throw new ConfigException('config_missing');
        }
        return self::validate($values, $privateDir);
    }

    /** @param array<string,mixed> $in */
    private static function validate(array $in, string $privateDir): self
    {
        foreach (self::flatten($in) as $item) {
            if (str_contains($item, 'CONFIRM_') || str_contains(strtolower($item), '.invalid')) {
                throw new ConfigException('config_placeholder');
            }
        }
        $s = static fn(string $k): string => isset($in[$k]) && is_scalar($in[$k]) ? trim((string) $in[$k]) : '';
        $out = [];

        $host = $s('smtp_host');
        if ($host === '' || !preg_match('/^[A-Za-z0-9.-]+$/', $host)) {
            throw new ConfigException('config_smtp_host');
        }
        $out['smtp_host'] = $host;

        $port = $s('smtp_port');
        if (!ctype_digit($port) || (int) $port < 1 || (int) $port > 65535) {
            throw new ConfigException('config_smtp_port');
        }
        $out['smtp_port'] = (int) $port;

        $secure = strtolower($s('smtp_secure'));
        if ($secure === '') {
            $secure = $out['smtp_port'] === 465 ? 'ssl' : 'tls';
        }
        // Plaintext SMTP is deliberately not an option.
        if (!in_array($secure, ['tls', 'ssl'], true)) {
            throw new ConfigException('config_smtp_secure');
        }
        $out['smtp_secure'] = $secure;

        $user = $s('smtp_user');
        $pass = isset($in['smtp_pass']) && is_string($in['smtp_pass']) ? $in['smtp_pass'] : '';
        if ($user === '' || $pass === '' || preg_match('/[\x00-\x1F\x7F]/', $user . $pass)) {
            throw new ConfigException('config_smtp_credentials');
        }
        $out['smtp_user'] = $user;
        $out['smtp_pass'] = $pass;

        foreach (['mail_from' => 'config_mail_from', 'mail_to' => 'config_mail_to'] as $k => $code) {
            $a = $s($k);
            if (!Validator::isSafeEmail($a)) {
                throw new ConfigException($code);
            }
            $out[$k] = $a;
        }
        $fromName = $s('mail_from_name');
        if (preg_match('/[\x00-\x1F\x7F]/', $fromName) || strlen($fromName) > 100) {
            throw new ConfigException('config_mail_from_name');
        }
        $out['mail_from_name'] = $fromName !== '' ? $fromName : 'Website enquiries';

        $origins = self::list($in['allowed_origins'] ?? []);
        if ($origins === []) {
            throw new ConfigException('config_allowed_origins');
        }
        foreach ($origins as $o) {
            if (!preg_match('#^(https?)://([A-Za-z0-9.-]+)(:[0-9]{1,5})?$#', $o, $m)) {
                throw new ConfigException('config_allowed_origins');
            }
            $loopback = in_array($m[2], ['localhost', '127.0.0.1'], true);
            if ($m[1] === 'http' && !$loopback) {
                throw new ConfigException('config_allowed_origins_https');
            }
        }
        $out['allowed_origins'] = array_map('strtolower', $origins);

        $proxies = self::list($in['trusted_proxies'] ?? []);
        foreach ($proxies as $p) {
            if (!ClientIp::validRange($p)) {
                throw new ConfigException('config_trusted_proxies');
            }
        }
        $out['trusted_proxies'] = $proxies;

        $ca = $s('smtp_ca_file');
        if ($ca !== '' && !is_file($ca)) {
            throw new ConfigException('config_smtp_ca_file');
        }
        $out['smtp_ca_file'] = $ca;

        $state = $s('state_dir');
        $out['state_dir'] = $state !== '' ? $state : $privateDir . '/var';

        foreach ([
            'rate_ip_max' => 5, 'rate_ip_window' => 600,
            'rate_global_max' => 100, 'rate_global_window' => 3600,
        ] as $k => $default) {
            $val = $s($k);
            $out[$k] = $val === '' ? $default : (ctype_digit($val) && (int) $val > 0 ? (int) $val : $default);
        }
        return new self($out);
    }

    /** @param array<string,mixed> $in @return list<string> */
    private static function flatten(array $in): array
    {
        $o = [];
        foreach ($in as $v) {
            if (is_array($v)) {
                array_push($o, ...self::flatten($v));
            } elseif (is_scalar($v)) {
                $o[] = (string) $v;
            }
        }
        return $o;
    }

    /** @return list<string> */
    private static function list(mixed $raw): array
    {
        if (is_string($raw)) {
            $raw = explode(',', $raw);
        }
        if (!is_array($raw)) {
            return [];
        }
        $out = [];
        foreach ($raw as $item) {
            if (is_string($item) && trim($item) !== '') {
                $out[] = trim($item);
            }
        }
        return $out;
    }
}
