<?php
declare(strict_types=1);

namespace Actp\Contact;

/**
 * Resolves the client address. X-Forwarded-For is honoured only when the immediate peer
 * (REMOTE_ADDR) is a configured trusted proxy, and then only for the right-most address
 * that is not itself a trusted proxy. Otherwise forwarded headers are ignored.
 */
final class ClientIp
{
    /** @param array<string,mixed> $server @param list<string> $trusted */
    public static function resolve(array $server, array $trusted): string
    {
        $remote = isset($server['REMOTE_ADDR']) && is_string($server['REMOTE_ADDR']) ? $server['REMOTE_ADDR'] : '';
        if (filter_var($remote, FILTER_VALIDATE_IP) === false) {
            return 'unknown';
        }
        if ($trusted === [] || !self::inAny($remote, $trusted)) {
            return $remote;
        }
        $xff = isset($server['HTTP_X_FORWARDED_FOR']) && is_string($server['HTTP_X_FORWARDED_FOR'])
            ? $server['HTTP_X_FORWARDED_FOR'] : '';
        $hops = array_reverse(array_map('trim', explode(',', $xff)));
        foreach ($hops as $hop) {
            if (filter_var($hop, FILTER_VALIDATE_IP) === false) {
                return $remote; // malformed chain: do not trust it
            }
            if (!self::inAny($hop, $trusted)) {
                return $hop;
            }
        }
        return $remote;
    }

    public static function validRange(string $range): bool
    {
        $parts = explode('/', $range, 2);
        if (filter_var($parts[0], FILTER_VALIDATE_IP) === false) {
            return false;
        }
        if (count($parts) === 2) {
            $max = str_contains($parts[0], ':') ? 128 : 32;
            return ctype_digit($parts[1]) && (int) $parts[1] <= $max;
        }
        return true;
    }

    /** @param list<string> $ranges */
    private static function inAny(string $ip, array $ranges): bool
    {
        foreach ($ranges as $r) {
            if (self::inRange($ip, $r)) {
                return true;
            }
        }
        return false;
    }

    private static function inRange(string $ip, string $range): bool
    {
        $parts = explode('/', $range, 2);
        $a = inet_pton($ip);
        $b = inet_pton($parts[0]);
        if ($a === false || $b === false || strlen($a) !== strlen($b)) {
            return false;
        }
        $bits = isset($parts[1]) ? (int) $parts[1] : strlen($a) * 8;
        $bytes = intdiv($bits, 8);
        if ($bytes > 0 && substr($a, 0, $bytes) !== substr($b, 0, $bytes)) {
            return false;
        }
        $rem = $bits % 8;
        if ($rem === 0) {
            return true;
        }
        $mask = (0xFF << (8 - $rem)) & 0xFF;
        return (ord($a[$bytes]) & $mask) === (ord($b[$bytes]) & $mask);
    }
}
