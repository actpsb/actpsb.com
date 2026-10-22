<?php
declare(strict_types=1);

namespace Actp\Contact;

/** Server-side validation. Rejects control characters in every single-line field (header injection). */
final class Validator
{
    public const MAX_NAME = 100;
    public const MAX_ORG = 150;
    public const MAX_EMAIL = 254;
    public const MIN_MESSAGE = 10;
    public const MAX_MESSAGE = 5000;
    public const CATEGORIES = [
        'NSX Nominated Adviser',
        'IPO & Capital Markets',
        'Corporate Advisory',
        'Mergers & Acquisitions',
        'General Enquiry',
    ];

    public static function isSafeEmail(string $v): bool
    {
        return $v !== ''
            && strlen($v) <= self::MAX_EMAIL
            && preg_match('/^[\x21-\x7E]+$/', $v) === 1 // printable ASCII only: no spaces, CR, LF, NUL
            && preg_match('/[<>",;\\\\]/', $v) !== 1
            && filter_var($v, FILTER_VALIDATE_EMAIL) !== false;
    }

    /**
     * @param array<string,mixed> $post
     * @return array{values: array<string,string>, errors: array<string,string>}
     */
    public static function validate(array $post): array
    {
        $values = [];
        $errors = [];
        foreach (['name', 'email', 'organisation', 'category', 'message'] as $k) {
            $raw = $post[$k] ?? '';
            if (!is_string($raw)) {
                $errors[$k] = 'This field was not submitted in a valid form.';
                $raw = '';
            }
            $values[$k] = $raw;
        }

        // Control characters are rejected on the raw value, before trim() could hide them.
        foreach (['name', 'email', 'organisation', 'category'] as $k) {
            if (!isset($errors[$k]) && preg_match('/[\x00-\x1F\x7F]/', $values[$k]) === 1) {
                $errors[$k] = 'This field must be on a single line without control characters.';
            }
        }
        $values['name'] = trim($values['name']);
        $values['email'] = trim($values['email']);
        $values['organisation'] = trim($values['organisation']);
        $values['category'] = trim($values['category']);
        $values['message'] = str_replace(["\r\n", "\r"], "\n", trim($values['message']));

        if (!isset($errors['category']) && !in_array($values['category'], self::CATEGORIES, true)) {
            $errors['category'] = 'Select a nature of enquiry from the list.';
        }

        foreach (['name' => self::MAX_NAME, 'organisation' => self::MAX_ORG] as $k => $max) {
            if (isset($errors[$k])) {
                continue;
            }
            $v = $values[$k];
            if (preg_match('//u', $v) !== 1) {
                $errors[$k] = 'This field contains characters that cannot be accepted.';
            } elseif (preg_match('/[\x00-\x1F\x7F]/', $v) === 1) {
                $errors[$k] = 'This field must be on a single line without control characters.';
            } elseif (mb_strlen($v, 'UTF-8') > $max) {
                $errors[$k] = "Use no more than {$max} characters.";
            } elseif ($k === 'name' && $v === '') {
                $errors[$k] = 'Enter your name.';
            }
        }

        if (!isset($errors['email'])) {
            $e = $values['email'];
            if ($e === '') {
                $errors['email'] = 'Enter your email address.';
            } elseif (!self::isSafeEmail($e)) {
                $errors['email'] = 'Enter a valid email address, for example name@example.com.';
            }
        }

        if (!isset($errors['message'])) {
            $m = $values['message'];
            if (preg_match('//u', $m) !== 1 || preg_match('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', $m) === 1) {
                $errors['message'] = 'The message contains characters that cannot be accepted.';
            } elseif (mb_strlen($m, 'UTF-8') < self::MIN_MESSAGE) {
                $errors['message'] = 'Enter a message of at least ' . self::MIN_MESSAGE . ' characters.';
            } elseif (mb_strlen($m, 'UTF-8') > self::MAX_MESSAGE) {
                $errors['message'] = 'Use no more than ' . self::MAX_MESSAGE . ' characters.';
            }
        }
        return ['values' => $values, 'errors' => $errors];
    }
}
