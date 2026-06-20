from __future__ import annotations

import builtins
import locale
from typing import Any


_open = builtins.open


def _is_utf8_locale() -> bool:
    return locale.getencoding().replace("-", "").lower() == "utf8"


if not _is_utf8_locale():

    def open(  # type: ignore[override]
        file: Any,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
        closefd: bool = True,
        opener: Any = None,
    ):
        if encoding is None and "b" not in mode:
            encoding = "utf-8"
        return _open(file, mode, buffering, encoding, errors, newline, closefd, opener)

    builtins.open = open
