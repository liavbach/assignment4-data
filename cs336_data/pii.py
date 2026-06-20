from __future__ import annotations

import re


EMAIL_MASK = "|||EMAIL_ADDRESS|||"
PHONE_MASK = "|||PHONE_NUMBER|||"
IP_MASK = "|||IP_ADDRESS|||"

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

PHONE_RE = re.compile(
    r"""
    (?<!\d)
    (?:
        \(\d{3}\)[-\s]?\d{3}[-\s]?\d{4}
        |
        \d{3}[-\s]?\d{3}[-\s]?\d{4}
    )
    (?!\d)
    """,
    re.VERBOSE,
)

IP_RE = re.compile(
    r"""
    (?<![\d.])
    (?:
        25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d
    )
    \.
    (?:
        25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d
    )
    \.
    (?:
        25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d
    )
    \.
    (?:
        25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d
    )
    (?!\d)
    """,
    re.VERBOSE,
)


def _mask(text: str, pattern: re.Pattern[str], replacement: str) -> tuple[str, int]:
    return pattern.subn(replacement, text)


def mask_emails(text: str) -> tuple[str, int]:
    return _mask(text, EMAIL_RE, EMAIL_MASK)


def mask_phone_numbers(text: str) -> tuple[str, int]:
    return _mask(text, PHONE_RE, PHONE_MASK)


def mask_ips(text: str) -> tuple[str, int]:
    return _mask(text, IP_RE, IP_MASK)
