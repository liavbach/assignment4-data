from __future__ import annotations

from functools import cache
from pathlib import Path

import fasttext

from cs336_data.common import get_shared_assets_path


def _language_model_path() -> Path:
    return get_shared_assets_path() / "classifiers" / "lid.176.bin"


@cache
def _load_language_model():
    model_path = _language_model_path()
    if not model_path.exists():
        raise FileNotFoundError(
            f"Missing language identification model at {model_path}. "
            "Run `python scripts/download_data.py --offline-only` to download it."
        )
    return fasttext.load_model(str(model_path))


def identify_language(text: str) -> tuple[str, float]:
    text = text.replace("\n", " ")
    labels, scores = _load_language_model().predict(text, k=1)
    language = labels[0].removeprefix("__label__")
    return language, float(scores[0])
