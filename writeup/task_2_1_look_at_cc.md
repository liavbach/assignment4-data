# Problem: Looking at Common Crawl

Note: the exact WARC/WET URLs printed in the handout returned 404 when checked on 2026-06-20, so I used the local `CC/example.warc.gz` and matching `CC/example.warc.wet.gz` downloaded from the first valid `CC-MAIN-2026-12` WARC path.

## (a)

The first web page URL is `http://020bld.cn.vauofnj.cn/html/991f998999.html`. It does not appear to be accessible now: both `HEAD` and `GET` requests failed DNS resolution for `020bld.cn.vauofnj.cn`. The raw HTML is Chinese and appears to be a low-quality article or template page about whether lily pollen staining can be washed out, with a large amount of boilerplate navigation, scripts, CSS links, and generic company-site structure mixed into the page.

## (b)

The corresponding WET record extracts readable Chinese text from the HTML, including the title and some page text, but it also preserves a lot of non-content material: hotline text, site navigation, category names, headers, and template/sidebar fragments. This would be noisy training data because a model could learn repeated web-template artifacts, menus, and SEO-like phrasing instead of mostly natural prose. Still, the page can provide useful signals such as Chinese vocabulary, question-answer phrasing, common web-page structure, and short factual or procedural text.

## (c)

This example might be useful for training a model intended to understand messy Chinese web pages, search snippets, SEO pages, or boilerplate-heavy crawled documents. It would be much less useful for training a high-quality assistant or long-form writing model, where the navigation clutter and low editorial quality would likely hurt the distribution.

## (d)

I inspected the next 25 WET records after the first example.

1. `021sakura.com` - Chinese; industry/news page with login/register links and company template navigation; mostly boilerplate.
2. `044mm.com` - Japanese/Chinese; adult video listing page; low-quality and harmful/noisy for general LM training.
3. `0553njl.com/kjcx/sbjkjcgj/` - Chinese; construction company awards/results page; much navigation, potentially usable corporate text.
4. `0553njl.com/xwzx/gsyw/3881.html` - Chinese; construction company news article about a commendation letter; some real article content after boilerplate.
5. `07921.cn/article/0/sex/...` - Chinese; local job/search portal page; many UI fragments, login prompts, templating artifacts.
6. `07921.cn/article/cid/12/...` - Chinese; job category page for public institution postings; again heavy portal/navigation boilerplate.
7. `100.ubc.ca/ubc-centenary/alanna-tomblin-smith/` - English; UBC Centennial alumni/profile page; first clearly high-quality page, despite menu text.
8. `11235813.org/IPB/...act=Help` - Russian; forum help/search page; mostly forum UI and help navigation.
9. `123-market.ru/brend/Kist_Vue` - Russian; marketplace/brand listing page; adblock notice, search controls, product/category clutter.
10. `128437.homepagemodules.de/u418_popoji----.html` - German; forum user profile/login page; mostly account and forum controls.
11. `168ps.com/kvpt/117579.html` - Chinese; streaming/movie page; navigation, icons, and title metadata dominate.
12. `198gg.com/vodtypehtml/50/` - Chinese; adult content index; low-quality/harmful for a general dataset.
13. `1pekesat-exae.mysch.gr/...` - Greek; phpBB-style helpdesk/forum index; mostly forum navigation and search controls.
14. `2019.whitehorseartshow.com.au/.../naked-woman/...` - English; art show artwork page; reasonable domain-specific content, with navigation boilerplate.
15. `223hei.com/htm/...` - Chinese; adult video page; low-quality/harmful for a general dataset.
16. `250a.com/2125.html` - Chinese; dating/course download page with Baidu link/code; commercial and somewhat spammy.
17. `26888hd3.com/index/detail/index/id/7.html` - Chinese; gambling/new-user bonus page; promotional and low-quality.
18. `2e-vaucresson-garches.agse.fr/...` - mostly English on a French scout-site domain; blog-spam-like article with awkward prose; questionable quality.
19. `3344eh.com` - English; only says "Loading"; unusable.
20. `377410.com/renew/l701.html` - Japanese; tutor/education testimonial list; short but coherent and potentially usable.
21. `37online.com/post/1601.html` - Chinese; entertainment/gossip/expose page; clickbait-style with lots of navigation.
22. `3iio8u.xyyanglao.com` - Chinese; corporate/product-site template for power modules; likely templated or spammy, but topical.
23. `4008881886.cn` - Chinese; company profile page; long generic corporate text, likely synthetic/SEO boilerplate.
24. `431dd.com/play/index37966-0-0.html` - Japanese/Chinese; adult video page; low-quality/harmful for general LM training.
25. `432149.com` - Chinese; long fiction/prose page; coherent text, but odd site framing and unclear provenance.

It took 7 additional WET records after the first example to reach what I would call a high-quality webpage: the UBC Centennial profile on `100.ubc.ca`. Several later records contain usable domain-specific text, but most of the early sample is dominated by boilerplate, adult content, gambling/promotional pages, forum UI, or SEO-like templates.
