# Problem: Personally Identifiable Information

## (d)

Naively masking PII can remove useful context or distort the data distribution: for example, phone numbers in business pages, historical documents, code snippets, or public institutional contact pages may be replaced even when they are not private personal information. The masks themselves can also become artifacts that the model learns to emit too often, and false negatives can leave sensitive data in the training set anyway. I would mitigate this with stricter context-aware filters, separate handling for public business/contact pages versus private user-generated content, audits of false positives and false negatives, and avoiding overtraining on the literal mask tokens.

## (e)

I ran the email, phone, and IPv4 masks over extracted WARC text and inspected the first 20 documents where at least one replacement was made. Most replacements were true positives from contact sections, such as `admin@aa.com`, `96352805@qq.com`, `czctzb@163.com`, `info@aideadomicilecoaticook.com`, Chinese mobile-style phone numbers, and US/Canadian/Russian formatted contact numbers. False positives included public/business contact information that is not necessarily private PII, and one movie/streaming page where a URL/share artifact looked email-like enough to be masked. False negatives included international phone formats with country codes, spaces, or punctuation such as `+7 (499) 391-15-17` and `819 849-7716`; those are real phone numbers but outside the deliberately simple US-focused regex. No IPv4 replacements appeared in these first 20 replacement-hit examples.
