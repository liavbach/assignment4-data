# Problem: Exact Line Deduplication

I implemented exact line deduplication by making one pass over all input files to count occurrences of each line across the full corpus, using a fixed-size Blake2b hash of the line bytes as the counter key. In a second pass, each input file is rewritten to the output directory with the same basename, preserving only lines whose global count is exactly one.

This removes repeated boilerplate such as shared headers, menus, and duplicated crawler-warning pages while preserving lines that are unique to a specific document. The implementation reads and writes bytes so that original line endings and file contents are preserved exactly for kept lines.

Verification:

```powershell
python -m pytest tests\test_deduplication.py -k exact_line -q
```

Result: `1 passed, 2 deselected`.
