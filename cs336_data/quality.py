from __future__ import annotations

import random
import re
import tempfile
from functools import cache
from pathlib import Path

import fasttext

from cs336_data.common import get_shared_assets_path


WORD_RE = re.compile(r"\S+")
QUALITY_MODEL_NAME = "quality_fasttext.bin"


def gopher_quality_filter(text: str) -> bool:
    words = WORD_RE.findall(text)
    n_words = len(words)
    if n_words < 50 or n_words > 100_000:
        return False

    mean_word_length = sum(len(word) for word in words) / n_words
    if mean_word_length < 3 or mean_word_length > 10:
        return False

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        ellipsis_lines = sum(line.endswith("...") for line in lines)
        if ellipsis_lines / len(lines) > 0.3:
            return False

    alphabetic_words = sum(any(char.isalpha() for char in word) for word in words)
    if alphabetic_words / n_words < 0.8:
        return False

    return True


def _quality_model_path() -> Path:
    return get_shared_assets_path() / "classifiers" / QUALITY_MODEL_NAME


def _to_fasttext_line(label: str, text: str) -> str:
    clean_text = " ".join(text.replace("\0", " ").split())
    return f"__label__{label} {clean_text}\n"


def train_quality_classifier(
    *,
    wiki_texts: list[str],
    cc_texts: list[str],
    output_path: Path | None = None,
    seed: int = 336,
    epoch: int = 25,
    lr: float = 0.5,
    word_ngrams: int = 2,
    dim: int = 50,
    bucket: int = 200_000,
):
    if not wiki_texts:
        raise ValueError("Need at least one wiki/high-quality positive example.")
    if not cc_texts:
        raise ValueError("Need at least one Common Crawl negative example.")

    output_path = output_path or _quality_model_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [_to_fasttext_line("wiki", text) for text in wiki_texts]
    lines.extend(_to_fasttext_line("cc", text) for text in cc_texts)
    random.Random(seed).shuffle(lines)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".quality.train.txt") as train_file:
        train_path = Path(train_file.name)
        train_file.writelines(lines)

    try:
        model = fasttext.train_supervised(
            input=str(train_path),
            epoch=epoch,
            lr=lr,
            wordNgrams=word_ngrams,
            dim=dim,
            bucket=bucket,
            minCount=1,
            verbose=0,
        )
        model.save_model(str(output_path))
    finally:
        train_path.unlink(missing_ok=True)

    return model


@cache
def _load_quality_model():
    model_path = _quality_model_path()
    if not model_path.exists():
        raise FileNotFoundError(
            f"Missing quality classifier at {model_path}. "
            "Run `python scripts/train_quality_classifier.py` to train it."
        )
    return fasttext.load_model(str(model_path))


def classify_quality(text: str) -> tuple[str, float]:
    labels, scores = _load_quality_model().predict(" ".join(text.split()), k=1)
    label = labels[0].removeprefix("__label__")
    score = max(0.0, min(1.0, float(scores[0])))
    return label, score
