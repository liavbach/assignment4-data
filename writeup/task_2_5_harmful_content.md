# Problem: Harmful Content

## (a)

I implemented NSFW classification with the Dolma/Jigsaw fastText NSFW model, returning either `nsfw` or `non-nsfw` plus the classifier confidence score.

## (b)

I implemented toxic-speech classification with the Dolma/Jigsaw fastText hate-speech model, returning either `toxic` or `non-toxic` plus the classifier confidence score.

## (c)

Applying harmful-content filters can remove genuinely harmful data, but it can also bias the training set by disproportionately removing discussions about sensitive topics, reclaimed language, support resources, moderation policy, or communities whose language differs from the classifier's training data. False negatives can leave harmful content in the corpus, while false positives can make the model less capable of understanding or safely responding to difficult subjects. I would mitigate this with human audits across domains and demographic contexts, separate thresholds for high-risk versus low-risk use cases, better labeled evaluation sets, and downstream safety evaluation after training rather than relying on the data filter alone.

## (d)

I ran both classifiers on 20 random extracted WARC examples and manually checked the snippets. In this sample, I judged 0/20 documents to be NSFW or toxic in the assignment's sense, and both classifiers also predicted `non-nsfw` and `non-toxic` for all 20, so I did not observe classifier errors in this small sample. Some pages were low-quality or commercially spammy, including gambling/SEO-like pages, but those are quality-filter issues rather than NSFW or toxic-speech positives. Based on this sample and the Jigsaw sanity checks, I would use a fairly high filtering threshold, around 0.8 or 0.9, for dropping documents automatically, and send borderline examples to further review or combine this signal with other quality filters.
