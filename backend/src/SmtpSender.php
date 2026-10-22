<?php
declare(strict_types=1);

namespace Actp\Contact;

use PHPMailer\PHPMailer\PHPMailer;

/**
 * Sends through authenticated SMTP using PHPMailer with verified TLS. There is no mail() fallback.
 * Sender and recipient come from server configuration only; the visitor address is Reply-To only.
 */
final class SmtpSender
{
    /**
    * @param array<string,string> $f validated fields: name, email, organisation, category, message
     * @throws SendFailure carrying a fixed category, never library text
     */
    public static function send(Config $config, array $f): void
    {
        $c = $config->v;
        $mail = new PHPMailer(true);
        try {
            $mail->isSMTP();
            $mail->SMTPDebug = 0;
            $mail->Host = $c['smtp_host'];
            $mail->Port = $c['smtp_port'];
            $mail->SMTPAuth = true;
            $mail->Username = $c['smtp_user'];
            $mail->Password = $c['smtp_pass'];
            $mail->SMTPSecure = $c['smtp_secure'] === 'ssl'
                ? PHPMailer::ENCRYPTION_SMTPS
                : PHPMailer::ENCRYPTION_STARTTLS;
            $mail->SMTPAutoTLS = false;
            $mail->Timeout = 10;
            $ssl = ['verify_peer' => true, 'verify_peer_name' => true, 'allow_self_signed' => false];
            if ($c['smtp_ca_file'] !== '') {
                $ssl['cafile'] = $c['smtp_ca_file'];
            }
            $mail->SMTPOptions = ['ssl' => $ssl];
            $mail->CharSet = PHPMailer::CHARSET_UTF8;
            $mail->Encoding = PHPMailer::ENCODING_QUOTED_PRINTABLE;
            $mail->XMailer = ' ';

            $mail->setFrom($c['mail_from'], $c['mail_from_name']);
            $mail->addAddress($c['mail_to']);
            $mail->addReplyTo($f['email'], $f['name']);
            $mail->Subject = 'Website enquiry';
            $mail->isHTML(false);
            $mail->Body = self::body($f);
            $mail->send();
        } catch (\Throwable $e) {
            throw new SendFailure(self::categorise($mail->ErrorInfo . ' ' . $e->getMessage()));
        }
    }

    /** @param array<string,string> $f */
    private static function body(array $f): string
    {
        return "A visitor used the website contact form.\n"
            . "The visitor's address below is unverified and is the Reply-To address only.\n\n"
            . 'Name: ' . $f['name'] . "\n"
            . 'Email: ' . $f['email'] . "\n"
            . 'Organisation: ' . ($f['organisation'] !== '' ? $f['organisation'] : '(not given)') . "\n"
            . 'Nature of enquiry: ' . $f['category'] . "\n\n"
            . "Message:\n" . $f['message'] . "\n";
    }

    private static function categorise(string $info): string
    {
        $i = strtolower($info);
        if (str_contains($i, 'authenticate')) {
            return 'smtp_auth';
        }
        if (str_contains($i, 'recipient')) {
            return 'smtp_recipient';
        }
        if (str_contains($i, 'connect') || str_contains($i, 'starttls') || str_contains($i, 'tls')) {
            return 'smtp_connect';
        }
        return 'smtp_send';
    }
}
