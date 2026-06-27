# Problem: MinHash + LSH Document Deduplication

I implemented fuzzy document deduplication by first normalizing text with lowercase conversion, NFD Unicode normalization, accent removal, punctuation removal, and whitespace normalization. Each document is represented as a set of word n-grams, then converted to a MinHash signature using multiple seeded Blake2b hash functions.

The implementation splits each signature into LSH bands and treats documents that match in at least one band as candidate duplicates. For each candidate pair, it computes the true Jaccard similarity of the normalized n-gram sets and unions documents into duplicate clusters when the similarity is at least the requested threshold. One deterministic representative, the earliest input file in each cluster, is copied to the output directory with its original file contents preserved.

Verification:

```powershell
python -m pytest tests\test_deduplication.py -q
```

Result: `3 passed`.
