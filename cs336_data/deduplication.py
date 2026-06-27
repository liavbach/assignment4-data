from __future__ import annotations

import hashlib
import os
import unicodedata
from collections import Counter
from collections import defaultdict
from itertools import combinations
from pathlib import Path


def _line_hash(line: bytes) -> bytes:
    return hashlib.blake2b(line, digest_size=16).digest()


def exact_line_deduplication(input_files: list[os.PathLike], output_directory: os.PathLike) -> None:
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)

    line_counts: Counter[bytes] = Counter()
    for input_file in input_files:
        with Path(input_file).open("rb") as f:
            for line in f:
                line_counts[_line_hash(line)] += 1

    for input_file in input_files:
        input_path = Path(input_file)
        deduplicated_path = output_path / input_path.name
        with input_path.open("rb") as src, deduplicated_path.open("wb") as dst:
            for line in src:
                if line_counts[_line_hash(line)] == 1:
                    dst.write(line)


def _normalize_for_minhash(text: str) -> list[str]:
    text = unicodedata.normalize("NFD", text.lower())
    chars: list[str] = []
    for char in text:
        category = unicodedata.category(char)
        if category.startswith("M"):
            continue
        if category.startswith("P"):
            chars.append(" ")
        else:
            chars.append(char)
    return "".join(chars).split()


def _word_ngrams(tokens: list[str], ngrams: int) -> set[str]:
    if ngrams <= 0:
        raise ValueError("ngrams must be positive")
    if len(tokens) < ngrams:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i : i + ngrams]) for i in range(len(tokens) - ngrams + 1)}


def _hash_ngram(ngram: str, seed: int) -> int:
    payload = f"{seed}\0{ngram}".encode("utf-8", errors="surrogatepass")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "big")


def _minhash_signature(ngram_set: set[str], num_hashes: int) -> tuple[int, ...]:
    if num_hashes <= 0:
        raise ValueError("num_hashes must be positive")
    if not ngram_set:
        max_hash = (1 << 64) - 1
        return tuple(max_hash for _ in range(num_hashes))
    return tuple(min(_hash_ngram(ngram, seed) for ngram in ngram_set) for seed in range(num_hashes))


def _candidate_pairs(signatures: list[tuple[int, ...]], num_bands: int) -> set[tuple[int, int]]:
    if num_bands <= 0:
        raise ValueError("num_bands must be positive")
    if signatures and len(signatures[0]) % num_bands != 0:
        raise ValueError("num_hashes must be divisible by num_bands")

    rows_per_band = len(signatures[0]) // num_bands if signatures else 0
    buckets: dict[tuple[int, tuple[int, ...]], list[int]] = defaultdict(list)
    for doc_idx, signature in enumerate(signatures):
        for band_idx in range(num_bands):
            start = band_idx * rows_per_band
            end = start + rows_per_band
            buckets[(band_idx, signature[start:end])].append(doc_idx)

    pairs: set[tuple[int, int]] = set()
    for bucket in buckets.values():
        if len(bucket) > 1:
            pairs.update(tuple(sorted(pair)) for pair in combinations(bucket, 2))
    return pairs


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    return len(left & right) / len(left | right)


class _UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self.parent[max(left_root, right_root)] = min(left_root, right_root)


def minhash_deduplication(
    input_files: list[os.PathLike],
    num_hashes: int,
    num_bands: int,
    ngrams: int,
    jaccard_threshold: float,
    output_directory: os.PathLike,
) -> None:
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)

    input_paths = [Path(path) for path in input_files]
    ngram_sets: list[set[str]] = []
    for input_path in input_paths:
        text = input_path.read_text(encoding="utf-8", errors="replace")
        tokens = _normalize_for_minhash(text)
        ngram_sets.append(_word_ngrams(tokens, ngrams))

    signatures = [_minhash_signature(ngram_set, num_hashes) for ngram_set in ngram_sets]
    candidates = _candidate_pairs(signatures, num_bands)

    clusters = _UnionFind(len(input_paths))
    for left_idx, right_idx in candidates:
        if _jaccard(ngram_sets[left_idx], ngram_sets[right_idx]) >= jaccard_threshold:
            clusters.union(left_idx, right_idx)

    keep_by_root: dict[int, int] = {}
    for doc_idx in range(len(input_paths)):
        root = clusters.find(doc_idx)
        keep_by_root[root] = min(doc_idx, keep_by_root.get(root, doc_idx))
    keep_indices = set(keep_by_root.values())

    for doc_idx, input_path in enumerate(input_paths):
        if doc_idx in keep_indices:
            (output_path / input_path.name).write_bytes(input_path.read_bytes())
