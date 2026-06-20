from __future__ import annotations

from functools import cache
from pathlib import Path

import fasttext

from cs336_data.common import get_shared_assets_path


NSFW_MODEL = "dolma_fasttext_nsfw_jigsaw_model.bin"
TOXIC_MODEL = "dolma_fasttext_hatespeech_jigsaw_model.bin"


def _classifier_path(filename: str) -> Path:
    return get_shared_assets_path() / "classifiers" / filename


@cache
def _load_classifier(filename: str):
    model_path = _classifier_path(filename)
    if not model_path.exists():
        raise FileNotFoundError(
            f"Missing harmful-content classifier at {model_path}. "
            "Run `python scripts/download_data.py --offline-only` to download it."
        )
    return fasttext.load_model(str(model_path))


def _predict(filename: str, text: str) -> tuple[str, float]:
    model = _load_classifier(filename)
    labels, scores = model.predict(text.replace("\n", " "), k=1)
    label = labels[0].removeprefix("__label__")
    score = max(0.0, min(1.0, float(scores[0])))
    return label, score


def classify_nsfw(text: str) -> tuple[str, float]:
    return _predict(NSFW_MODEL, text)


def classify_toxic_speech(text: str) -> tuple[str, float]:
    return _predict(TOXIC_MODEL, text)
