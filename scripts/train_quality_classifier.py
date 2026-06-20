from __future__ import annotations

import argparse
import gzip
import random
import sys
import urllib.request
from pathlib import Path
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cs336_data.common import get_shared_assets_path
from cs336_data.extract import extract_text_from_html_bytes
from cs336_data.quality import gopher_quality_filter, train_quality_classifier


def _read_urls(path: Path) -> list[str]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as f:
        return [line.strip() for line in f if line.strip().startswith(("http://", "https://"))]


def _download_html(url: str, *, timeout: float, max_bytes: int) -> bytes | None:
    request = urllib.request.Request(url, headers={"User-Agent": "cs336-data-quality-classifier/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            if "html" not in content_type.lower():
                return None
            return response.read(max_bytes)
    except (OSError, URLError, TimeoutError):
        return None


def collect_wiki_positive_texts(
    *,
    wiki_url_file: Path,
    n_examples: int,
    max_attempts: int,
    seed: int,
    timeout: float,
    max_bytes: int,
) -> list[str]:
    urls = _read_urls(wiki_url_file)
    random.Random(seed).shuffle(urls)

    texts: list[str] = []
    for url in urls[:max_attempts]:
        html = _download_html(url, timeout=timeout, max_bytes=max_bytes)
        if html is None:
            continue
        text = extract_text_from_html_bytes(html)
        if gopher_quality_filter(text):
            texts.append(text)
        if len(texts) >= n_examples:
            break
    return texts


def iter_warc_response_payloads(path: Path):
    with gzip.open(path, "rb") as f:
        while True:
            line = f.readline()
            if not line:
                return
            if not line.startswith(b"WARC/"):
                continue

            headers: dict[str, str] = {}
            while True:
                header = f.readline()
                if not header or header in (b"\r\n", b"\n"):
                    break
                key, _, value = header.decode("utf-8", "replace").partition(":")
                headers[key.strip()] = value.strip()

            payload = f.read(int(headers.get("Content-Length", "0")))
            if headers.get("WARC-Type") == "response":
                separator = payload.find(b"\r\n\r\n")
                yield payload[separator + 4 :] if separator != -1 else payload

            while True:
                pos = f.tell()
                next_line = f.readline()
                if next_line in (b"\r\n", b"\n"):
                    continue
                f.seek(pos)
                break


def collect_cc_negative_texts(*, cc_warc: Path, n_examples: int, seed: int, max_candidates: int | None = None) -> list[str]:
    candidates: list[str] = []
    max_candidates = max_candidates or max(n_examples * 10, n_examples)
    for payload in iter_warc_response_payloads(cc_warc):
        try:
            text = extract_text_from_html_bytes(payload)
        except Exception:
            continue
        if len(text.split()) >= 50:
            candidates.append(text)
        if len(candidates) >= max_candidates:
            break

    random.Random(seed).shuffle(candidates)
    return candidates[:n_examples]


def main() -> None:
    shared = get_shared_assets_path()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--wiki-url-file",
        type=Path,
        default=shared / "wiki" / "enwiki-20260501-extracted_urls.txt.gz",
    )
    parser.add_argument("--cc-warc", type=Path, default=Path("CC") / "example.warc.gz")
    parser.add_argument("--output", type=Path, default=shared / "classifiers" / "quality_fasttext.bin")
    parser.add_argument("--n-positive", type=int, default=1000)
    parser.add_argument("--n-negative", type=int, default=1000)
    parser.add_argument("--max-url-attempts", type=int, default=10000)
    parser.add_argument("--max-cc-candidates", type=int, default=None)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--max-bytes", type=int, default=2_000_000)
    parser.add_argument("--seed", type=int, default=336)
    args = parser.parse_args()

    if not args.wiki_url_file.exists():
        raise FileNotFoundError(f"Missing wiki URL file: {args.wiki_url_file}")
    if not args.cc_warc.exists():
        raise FileNotFoundError(f"Missing Common Crawl WARC file: {args.cc_warc}")

    wiki_texts = collect_wiki_positive_texts(
        wiki_url_file=args.wiki_url_file,
        n_examples=args.n_positive,
        max_attempts=args.max_url_attempts,
        seed=args.seed,
        timeout=args.timeout,
        max_bytes=args.max_bytes,
    )
    cc_texts = collect_cc_negative_texts(
        cc_warc=args.cc_warc,
        n_examples=args.n_negative,
        seed=args.seed,
        max_candidates=args.max_cc_candidates,
    )

    print(f"Collected {len(wiki_texts)} wiki positives and {len(cc_texts)} CC negatives")
    if not wiki_texts:
        raise ValueError("No wiki positive examples collected.")
    if not cc_texts:
        raise ValueError("No Common Crawl negative examples collected.")
    train_quality_classifier(wiki_texts=wiki_texts, cc_texts=cc_texts, output_path=args.output, seed=args.seed)
    print(f"Wrote quality classifier to {args.output}")


if __name__ == "__main__":
    main()
