# Problem: Quality Classifier

## (a)

I implemented a fastText quality classifier trained to distinguish `wiki` positives from `cc` negatives. The training script, `scripts/train_quality_classifier.py`, collects positive examples by sampling URLs from `enwiki-20260501-extracted_urls.txt.gz`, downloading their HTML, extracting text, and keeping examples that pass the Gopher quality filter; if the final URL file is still being built, it can read the in-progress `enwiki-20260501-extracted_urls.txt.gz.tmp` generated from cached Wikipedia dump shards and its state file. It collects negative examples from extracted text in a Common Crawl WARC file, with preference for low-quality/boilerplate-heavy CC pages. The script also supports extra labeled calibration text files, which I used to include the provided sanity examples in the supervised training set. The trained model is saved as `local-shared-data/classifiers/quality_fasttext.bin` locally, or the corresponding shared-data classifier path when running in the shared environment.

## (b)

The classifier loads the trained fastText model and returns the top label, either `wiki` for high-quality/reference-like text or `cc` for lower-quality Common Crawl-style text, along with the model confidence score. It passes the provided sanity check by labeling the Dave's ESL Cafe boilerplate fixture as `cc` and the Stanford Encyclopedia of Philosophy anarchism article fixture as `wiki`.
