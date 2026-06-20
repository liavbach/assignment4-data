# Problem: Language Identification

## (a)

I implemented language identification using the fastText `lid.176.bin` model. The adapter returns the top predicted language code with the fastText confidence score, normalizing labels like `__label__en` to `en`.

## (b)

If language identification is wrong, the downstream model can get a training mixture that does not match the intended product: for example, English filtering might silently include boilerplate-heavy non-English pages, exclude minority-language or code-switched pages, or overrepresent languages that the classifier finds easier. This can make the model worse for some user groups, unexpectedly multilingual in places, or brittle on dialects and mixed-language inputs. In a higher-stakes deployment, I would mitigate this with held-out human-labeled audits across languages and domains, conservative confidence thresholds, separate treatment for code-switching/unknown-language pages, and monitoring of model behavior by language after training.

## (c)

I sampled 20 extracted WARC records and manually labeled their main language: Chinese, Chinese, English, German, Chinese, Chinese, Romanian, Finnish, Chinese, Danish, Korean, Chinese, Dutch, English, Chinese, English, Greek, English, Hungarian, English. The fastText classifier agreed with my labels on all 20 examples, but some pages with lots of navigation, product specs, or redirect boilerplate had relatively low confidence, especially English pages around 0.55-0.72 and Danish/Korean pages around 0.58-0.61. By my labels, 5 of 20 documents were English, so the English fraction was 25%. For filtering English pages, I would start with a threshold around 0.7 for higher precision, then tune it on a larger manually labeled sample because a lower threshold such as 0.55 would recover more short/boilerplate English pages at the cost of more risk.
