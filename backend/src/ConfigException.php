<?php
declare(strict_types=1);

namespace Actp\Contact;

/** Raised when server configuration is missing or invalid. The message is a fixed code, never a value. */
final class ConfigException extends \RuntimeException
{
}
