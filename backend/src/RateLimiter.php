<?php
declare(strict_types=1);

namespace Actp\Contact;

/**
 * Bounded, file-locked sliding-window limiter kept in a private state directory.
 * Client addresses are stored only as keyed hashes. State is never placed under the web root.
 */
final class RateLimiter
{
    public function __construct(
        private string $stateDir,
        private int $ipMax,
        private int $ipWindow,
        private int $globalMax,
        private int $globalWindow,
    ) {
    }

    /** @return array{ok: bool, retryAfter: int} */
    public function attempt(string $ip, ?int $now = null): array
    {
        $now ??= time();
        $this->ensureDir();
        $fh = fopen($this->stateDir . '/ratelimit.json', 'c+');
        if ($fh === false) {
            throw new \RuntimeException('state_unwritable');
        }
        try {
            if (!flock($fh, LOCK_EX)) {
                throw new \RuntimeException('state_lock');
            }
            $raw = stream_get_contents($fh);
            $data = is_string($raw) && $raw !== '' ? json_decode($raw, true) : null;
            if (!is_array($data)) {
                $data = [];
            }
            $ips = is_array($data['ip'] ?? null) ? $data['ip'] : [];
            $global = is_array($data['global'] ?? null) ? $data['global'] : [];

            $key = hash_hmac('sha256', $ip, $this->secret());
            $ipHits = array_values(array_filter(
                is_array($ips[$key] ?? null) ? $ips[$key] : [],
                fn($t) => is_int($t) && $t > $now - $this->ipWindow
            ));
            $global = array_values(array_filter($global, fn($t) => is_int($t) && $t > $now - $this->globalWindow));

            // Drop other clients' expired entries so the file stays bounded.
            foreach ($ips as $k => $hits) {
                if ($k === $key) {
                    continue;
                }
                $live = array_values(array_filter(
                    is_array($hits) ? $hits : [],
                    fn($t) => is_int($t) && $t > $now - $this->ipWindow
                ));
                if ($live === []) {
                    unset($ips[$k]);
                } else {
                    $ips[$k] = $live;
                }
            }

            $result = ['ok' => true, 'retryAfter' => 0];
            if (count($ipHits) >= $this->ipMax) {
                $result = ['ok' => false, 'retryAfter' => max(1, $ipHits[0] + $this->ipWindow - $now)];
            } elseif (count($global) >= $this->globalMax) {
                $result = ['ok' => false, 'retryAfter' => max(1, $global[0] + $this->globalWindow - $now)];
            } else {
                $ipHits[] = $now;
                $global[] = $now;
            }
            // Bound the table even under many distinct addresses.
            if (count($ips) > 5000) {
                $ips = array_slice($ips, -2500, null, true);
            }
            $ips[$key] = $ipHits;
            ftruncate($fh, 0);
            rewind($fh);
            fwrite($fh, json_encode(['ip' => $ips, 'global' => $global]));
            fflush($fh);
            flock($fh, LOCK_UN);
            return $result;
        } finally {
            fclose($fh);
        }
    }

    private function ensureDir(): void
    {
        if (!is_dir($this->stateDir) && !@mkdir($this->stateDir, 0700, true) && !is_dir($this->stateDir)) {
            throw new \RuntimeException('state_unwritable');
        }
    }

    private function secret(): string
    {
        $path = $this->stateDir . '/ratelimit.key';
        $s = @file_get_contents($path);
        if (is_string($s) && strlen($s) >= 32) {
            return $s;
        }
        $s = random_bytes(32);
        $tmp = $path . '.' . bin2hex(random_bytes(4));
        file_put_contents($tmp, $s);
        chmod($tmp, 0600);
        rename($tmp, $path); // atomic; a racing writer simply wins
        $final = @file_get_contents($path);
        return is_string($final) && strlen($final) >= 32 ? $final : $s;
    }
}
