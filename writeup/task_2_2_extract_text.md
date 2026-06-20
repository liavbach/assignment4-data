# Problem: HTML to Text Conversion

## (b)

Running `extract_text_from_html_bytes` on the first WARC response produced text very similar to the corresponding WET record: both preserve the page title, navigation labels, contact/sidebar boilerplate, and the main Chinese question-answer content about lily pollen stains. The Resiliparse output kept some list bullets and a small amount of extra site-title formatting that the WET text flattened away, while the WET output was slightly more compact. Neither extraction is ideal as training data because both include substantial template/navigation text, but the WET version is marginally cleaner for this page.
