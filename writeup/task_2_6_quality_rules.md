# Problem: Gopher Quality Filters

## (a)

I implemented the requested subset of the Gopher quality filters: word count between 50 and 100,000, mean word length between 3 and 10 characters, at most 30% of nonempty lines ending in `...`, and at least 80% of words containing an alphabetic character.

## (b)

I ran the rule-based filter on 20 random extracted WARC examples; 9 of 20 passed. The filter correctly rejected several obviously bad examples, including adult/SEO spam pages, extremely long word-list pages, and pages dominated by product/navigation fragments. However, it also passed some examples I would reject manually, such as an adult-link page, a forum profile/login page, and short contact/category pages with lots of boilerplate, because the Gopher rules only check shallow text statistics. Conversely, it rejected some pages that could contain useful domain-specific information, such as product pages or non-English institutional pages, because formatting, dense lists, or tokenization made them look low-quality under these simple criteria.
