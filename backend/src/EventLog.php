<?php
declare(strict_types=1);

namespace Actp\Contact;

/**
 * Private operational log. Records only a UTC time, a request id and a fixed event code.
 * Never records message content, visitor details, addresses, credentials or library error text.
 */
final class EventLog
{
    private const MAX_BYTES = 1048576;

    public function __construct(private string $dir)
    {
    }

    public function write(string $requestId, string $code): void
    {
        if (preg_match('/^[a-z0-9_]{1,40}$/', $code) !== 1) {
            $code = 'invalid_code';
        }
        try {
            if (!is_dir($this->dir) && !@mkdir($this->dir, 0700, true) && !is_dir($this->dir)) {
                return;
            }
            $file = $this->dir . '/contact.log';
            if (is_file($file) && filesize($file) > self::MAX_BYTES) {
                @rename($file, $file . '.1');
            }
            @file_put_contents($file, gmdate('c') . ' ' . $requestId . ' ' . $code . "\n", FILE_APPEND | LOCK_EX);
        } catch (\Throwable) {
            // Logging must never affect the response.
        }
    }
}
