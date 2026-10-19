<?php
declare(strict_types=1);

namespace Actp\Contact;

/**
 * Renders the native (no-JavaScript) POST response by reusing the site's own contact.html,
 * so header, footer and styling cannot drift. The region between the ACTP:FORM markers is replaced.
 */
final class Page
{
    public const FIELDS = [
        'name' => 'Name',
        'email' => 'Email address',
        'organisation' => 'Organisation (optional)',
        'message' => 'Message',
    ];

    public static function h(string $s): string
    {
        return htmlspecialchars($s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    }

    /**
     * @param array<string,string> $values
     * @param array<string,string> $errors
     */
    public static function render(
        string $publicDir,
        string $state,
        string $message,
        array $values,
        array $errors,
        string $requestId,
        bool $showForm
    ): string {
        $tpl = @file_get_contents($publicDir . '/contact.html');
        if ($tpl === false) {
            return '<!doctype html><title>Contact</title><p>' . self::h($message) . '</p>';
        }
        $status = '<div id="form-status" class="form-status form-status--' . self::h($state)
            . '" role="' . ($state === 'accepted' ? 'status' : 'alert') . '" tabindex="-1">'
            . '<p>' . self::h($message) . '</p>';
        if ($errors !== []) {
            $status .= '<ul class="form-errors">';
            foreach ($errors as $k => $msg) {
                if (isset(self::FIELDS[$k])) {
                    $status .= '<li><a href="#field-' . self::h($k) . '">' . self::h(self::FIELDS[$k])
                        . ': ' . self::h($msg) . '</a></li>';
                }
            }
            $status .= '</ul>';
        }
        if ($requestId !== '' && $state !== 'accepted') {
            $status .= '<p class="form-status__ref">Reference: ' . self::h($requestId) . '</p>';
        }
        $status .= '</div>';
        $region = $status . ($showForm ? self::form($values, $errors) : '');
        $out = preg_replace_callback(
            '/<!--ACTP:FORM-->.*?<!--\/ACTP:FORM-->/s',
            static fn() => "<!--ACTP:FORM-->\n" . $region . "\n<!--/ACTP:FORM-->",
            $tpl,
            1
        );
        $out = is_string($out) ? $out : $tpl;
        // The response page is not the indexable contact page.
        return preg_replace('/<head>/', "<head>\n  <meta name=\"robots\" content=\"noindex\">", $out, 1) ?? $out;
    }

    /**
     * @param array<string,string> $values
     * @param array<string,string> $errors
     */
    public static function form(array $values, array $errors): string
    {
        $v = static fn(string $k): string => self::h($values[$k] ?? '');
        $f = static function (string $k, string $control) use ($errors): string {
            $err = isset($errors[$k])
                ? '<p class="field__error" id="error-' . $k . '">' . self::h($errors[$k]) . '</p>' : '';
            return '<div class="field' . (isset($errors[$k]) ? ' field--invalid' : '') . '">'
                . '<label for="field-' . $k . '">' . self::FIELDS[$k] . '</label>' . $err . $control . '</div>';
        };
        $d = static fn(string $k, string $hint = ''): string =>
            ' id="field-' . $k . '" name="' . $k . '"'
            . (isset($errors[$k]) ? ' aria-invalid="true"' : '')
            . ' aria-describedby="' . (isset($errors[$k]) ? 'error-' . $k . ' ' : '') . ($hint !== '' ? $hint : '') . '"';
        $d2 = static fn(string $k, string $hint = ''): string => str_replace(' aria-describedby=""', '', $d($k, trim($hint)));
        return self::formOpen()
            . $f('name', '<input type="text"' . $d2('name') . ' autocomplete="name" maxlength="' . Validator::MAX_NAME . '" required value="' . $v('name') . '">')
            . $f('email', '<input type="email"' . $d2('email') . ' autocomplete="email" maxlength="' . Validator::MAX_EMAIL . '" required value="' . $v('email') . '">')
            . $f('organisation', '<input type="text"' . $d2('organisation') . ' autocomplete="organization" maxlength="' . Validator::MAX_ORG . '" value="' . $v('organisation') . '">')
            . $f('message', '<textarea' . $d2('message', 'message-hint') . ' rows="7" minlength="' . Validator::MIN_MESSAGE . '" maxlength="' . Validator::MAX_MESSAGE . '" required>' . $v('message') . '</textarea>'
                . '<p class="field__hint" id="message-hint">' . Validator::MIN_MESSAGE . ' to ' . Validator::MAX_MESSAGE . ' characters.</p>')
            . self::formClose();
    }

    private static function formOpen(): string
    {
        return '<form class="contact-form" method="post" action="contact-submit.php" novalidate>';
    }

    private static function formClose(): string
    {
        return '<div class="field field--trap" aria-hidden="true"><label for="field-website">Leave this field empty</label>'
            . '<input type="text" id="field-website" name="website" tabindex="-1" autocomplete="off" value=""></div>'
            . '<button class="button" type="submit">Send enquiry</button></form>';
    }
}
