from __future__ import annotations

import argparse
import bz2
import gzip
import json
import re
import ssl
import sys
import urllib.request
from pathlib import Path
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cs336_data.common import get_shared_assets_path


URL_RE = re.compile(
    r"\b(?:https?|telnet|gopher|file|wais|ftp):[\w/#~:.?+=&%@!\-.:?\\-]+?(?=[.:?\-]*(?:[^\w/#~:.?+=&%@!\-.:?\-]|$))"
)


def _urlopen(url: str, *, timeout: float, insecure: bool):
    request = urllib.request.Request(url, headers={"User-Agent": "cs336-data-wiki-url-download/1.0"})
    context = ssl._create_unverified_context() if insecure else None
    return urllib.request.urlopen(request, timeout=timeout, context=context)


def _read_dump_index(*, dump_date: str, timeout: float, insecure: bool) -> tuple[str, list[str]]:
    base_url = f"https://dumps.wikimedia.org/enwiki/{dump_date}/"
    with _urlopen(base_url, timeout=timeout, insecure=insecure) as response:
        html = response.read().decode("utf-8", errors="replace")
    shards = sorted(
        set(
            re.findall(
                rf"enwiki-{dump_date}-pages-articles-multistream[0-9]+\.xml-p[0-9]+p[0-9]+\.bz2",
                html,
            )
        )
    )
    if not shards:
        raise RuntimeError(f"No wiki shards found at {base_url}")
    return base_url, shards


def _download(url: str, output_path: Path, *, timeout: float, insecure: bool) -> None:
    partial_path = Path(f"{output_path}.part")
    partial_path.unlink(missing_ok=True)
    with _urlopen(url, timeout=timeout, insecure=insecure) as response, partial_path.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    partial_path.replace(output_path)


def _extract_urls(shard_path: Path) -> list[str]:
    urls: list[str] = []
    with bz2.open(shard_path, "rt", errors="ignore") as f:
        for line in f:
            if refs := re.search("&lt;ref&gt(.*)&lt;/ref&gt;", line):
                urls.extend(URL_RE.findall(refs.group(0)))
    return urls


def _load_state(state_path: Path, temp_output_path: Path) -> set[str]:
    if not state_path.exists() or not temp_output_path.exists():
        state_path.unlink(missing_ok=True)
        temp_output_path.unlink(missing_ok=True)
        return set()
    with state_path.open("r", encoding="utf-8") as f:
        state = json.load(f)
    return set(state.get("processed_shards", []))


def _write_state(state_path: Path, processed_shards: set[str]) -> None:
    state_path.write_text(
        json.dumps({"processed_shards": sorted(processed_shards)}, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    shared = get_shared_assets_path()
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump-date", default="20260501")
    parser.add_argument("--output", type=Path, default=shared / "wiki" / "enwiki-20260501-extracted_urls.txt.gz")
    parser.add_argument("--cache-dir", type=Path, default=shared / "wiki" / ".cache")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification. Useful if the local machine clock breaks certificate validation.",
    )
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    temp_output_path = Path(f"{args.output}.tmp")
    state_path = Path(f"{args.output}.state.json")

    base_url, shards = _read_dump_index(dump_date=args.dump_date, timeout=args.timeout, insecure=args.insecure)
    processed_shards = _load_state(state_path, temp_output_path)

    print(f"[wiki] extracting {len(shards)} shards to {args.output}", flush=True)
    print(f"[wiki] already processed {len(processed_shards)} shards", flush=True)

    total_urls = 0
    output_mode = "at" if processed_shards else "wt"
    with gzip.open(temp_output_path, output_mode, encoding="utf-8") as output:
        for index, shard in enumerate(shards, 1):
            if shard in processed_shards:
                print(f"[wiki] {index}/{len(shards)} skipping {shard}", flush=True)
                continue

            shard_path = args.cache_dir / shard
            if not shard_path.exists():
                print(f"[wiki] {index}/{len(shards)} downloading {shard}", flush=True)
                try:
                    _download(base_url + shard, shard_path, timeout=args.timeout, insecure=args.insecure)
                except (OSError, URLError, TimeoutError):
                    shard_path.unlink(missing_ok=True)
                    raise
            else:
                print(f"[wiki] {index}/{len(shards)} using cached {shard}", flush=True)

            print(f"[wiki] {index}/{len(shards)} scanning {shard}", flush=True)
            urls = _extract_urls(shard_path)
            for url in urls:
                output.write(url + "\n")
            total_urls += len(urls)
            processed_shards.add(shard)
            _write_state(state_path, processed_shards)
            print(f"[wiki] {index}/{len(shards)} found {len(urls)} urls; new total={total_urls}", flush=True)

    temp_output_path.replace(args.output)
    state_path.unlink(missing_ok=True)
    print(f"[wiki] wrote {args.output} ({args.output.stat().st_size} bytes)", flush=True)


if __name__ == "__main__":
    main()
