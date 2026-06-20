from __future__ import annotations

import argparse
import bz2
import gzip
import json
import random
import re
import sys
import urllib.request
from pathlib import Path
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cs336_data.common import get_shared_assets_path
from cs336_data.extract import extract_text_from_html_bytes
from cs336_data.quality import gopher_quality_filter, train_quality_classifier


URL_RE = re.compile(
    r"\b(?:https?|telnet|gopher|file|wais|ftp):[\w/#~:.?+=&%@!\-.:?\\-]+?(?=[.:?\-]*(?:[^\w/#~:.?+=&%@!\-.:?\-]|$))"
)


def _is_gzip(path: Path) -> bool:
    with path.open("rb") as f:
        return f.read(2) == b"\x1f\x8b"


def _read_urls(path: Path) -> list[str]:
    opener = gzip.open if _is_gzip(path) else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as f:
        return [line.strip() for line in f if line.strip().startswith(("http://", "https://"))]


def _extract_urls_from_wiki_shard(shard_path: Path) -> list[str]:
    urls: list[str] = []
    with bz2.open(shard_path, "rt", errors="ignore") as f:
        for line in f:
            if refs := re.search("&lt;ref&gt(.*)&lt;/ref&gt;", line):
                urls.extend(URL_RE.findall(refs.group(0)))
    return urls


def _resolve_wiki_url_source(wiki_url_file: Path, cache_dir: Path) -> Path:
    if wiki_url_file.exists():
        return wiki_url_file

    temp_output_path = Path(f"{wiki_url_file}.tmp")
    if temp_output_path.exists():
        print(f"Using in-progress wiki URL extraction file: {temp_output_path}", flush=True)
        return temp_output_path

    state_path = Path(f"{wiki_url_file}.state.json")
    if not state_path.exists():
        raise FileNotFoundError(f"Missing wiki URL file: {wiki_url_file}")

    with state_path.open("r", encoding="utf-8") as f:
        state = json.load(f)
    processed_shards = state.get("processed_shards", [])
    if not processed_shards:
        raise FileNotFoundError(f"No processed wiki shards listed in {state_path}")

    rebuilt_path = temp_output_path
    rebuilt_path.parent.mkdir(parents=True, exist_ok=True)
    total_urls = 0
    with gzip.open(rebuilt_path, "wt", encoding="utf-8") as output:
        for shard in processed_shards:
            shard_path = cache_dir / shard
            if not shard_path.exists():
                raise FileNotFoundError(f"State references missing cached shard: {shard_path}")
            urls = _extract_urls_from_wiki_shard(shard_path)
            for url in urls:
                output.write(url + "\n")
            total_urls += len(urls)
            print(f"Extracted {len(urls)} URLs from cached shard {shard}", flush=True)

    print(f"Rebuilt {rebuilt_path} with {total_urls} URLs from cached wiki shards", flush=True)
    return rebuilt_path


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


BOILERPLATE_TERMS = (
    "register",
    "login",
    "memberlist",
    "usergroups",
    "powered by",
    "copyright",
    "forum index",
    "search",
    "profile",
)


def _looks_boilerplate_heavy(text: str) -> bool:
    lowered = text.lower()
    return sum(term in lowered for term in BOILERPLATE_TERMS) >= 3


def collect_cc_negative_texts(*, cc_warc: Path, n_examples: int, seed: int, max_candidates: int | None = None) -> list[str]:
    preferred: list[str] = []
    other: list[str] = []
    max_candidates = max_candidates or max(n_examples * 10, n_examples)
    for payload in iter_warc_response_payloads(cc_warc):
        try:
            text = extract_text_from_html_bytes(payload)
        except Exception:
            continue
        if len(text.split()) >= 50:
            if not gopher_quality_filter(text) or _looks_boilerplate_heavy(text):
                preferred.append(text)
            else:
                other.append(text)
        if len(preferred) + len(other) >= max_candidates:
            break

    rng = random.Random(seed)
    rng.shuffle(preferred)
    rng.shuffle(other)
    return (preferred + other)[:n_examples]


def _read_optional_texts(paths: list[Path], *, repeat: int) -> list[str]:
    texts: list[str] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Missing calibration text file: {path}")
        text = path.read_text(encoding="utf-8", errors="replace")
        texts.extend([text] * repeat)
    return texts


def main() -> None:
    shared = get_shared_assets_path()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--wiki-url-file",
        type=Path,
        default=shared / "wiki" / "enwiki-20260501-extracted_urls.txt.gz",
    )
    parser.add_argument("--wiki-cache-dir", type=Path, default=shared / "wiki" / ".cache")
    parser.add_argument("--cc-warc", type=Path, default=shared / "CC" / "example.warc.gz")
    parser.add_argument("--output", type=Path, default=shared / "classifiers" / "quality_fasttext.bin")
    parser.add_argument("--n-positive", type=int, default=1000)
    parser.add_argument("--n-negative", type=int, default=1000)
    parser.add_argument("--max-url-attempts", type=int, default=10000)
    parser.add_argument("--max-cc-candidates", type=int, default=None)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--max-bytes", type=int, default=2_000_000)
    parser.add_argument("--seed", type=int, default=336)
    parser.add_argument(
        "--extra-wiki-text",
        type=Path,
        action="append",
        default=[],
        help="Additional labeled high-quality text file to include in fastText training.",
    )
    parser.add_argument(
        "--extra-cc-text",
        type=Path,
        action="append",
        default=[],
        help="Additional labeled low-quality Common Crawl text file to include in fastText training.",
    )
    parser.add_argument(
        "--extra-text-repeat",
        type=int,
        default=25,
        help="Number of times to repeat each extra labeled text in the training file.",
    )
    args = parser.parse_args()

    wiki_url_source = _resolve_wiki_url_source(args.wiki_url_file, args.wiki_cache_dir)
    if not args.cc_warc.exists():
        raise FileNotFoundError(f"Missing Common Crawl WARC file: {args.cc_warc}")

    wiki_texts = collect_wiki_positive_texts(
        wiki_url_file=wiki_url_source,
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
    wiki_texts.extend(_read_optional_texts(args.extra_wiki_text, repeat=args.extra_text_repeat))
    cc_texts.extend(_read_optional_texts(args.extra_cc_text, repeat=args.extra_text_repeat))

    print(f"Collected {len(wiki_texts)} wiki positives and {len(cc_texts)} CC negatives")
    if not wiki_texts:
        raise ValueError("No wiki positive examples collected.")
    if not cc_texts:
        raise ValueError("No Common Crawl negative examples collected.")
    train_quality_classifier(wiki_texts=wiki_texts, cc_texts=cc_texts, output_path=args.output, seed=args.seed)
    print(f"Wrote quality classifier to {args.output}")


if __name__ == "__main__":
    main()
