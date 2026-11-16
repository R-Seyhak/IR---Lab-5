import hashlib
import re

import scrapy

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    def __init__(self, max_pages=2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_pages = max(1, int(max_pages))
        self.pages_seen = 0

    def parse(self, response):
        self.pages_seen += 1
        for href in response.css("article.product_pod h3 a::attr(href)").getall():
            yield response.follow(href, callback=self.parse_book)

        next_href = response.css("li.next a::attr(href)").get()
        if next_href and self.pages_seen < self.max_pages:
            yield response.follow(next_href, callback=self.parse)

    def parse_book(self, response):
        title = (response.css("div.product_main h1::text").get() or "").strip()
        description = " ".join(
            t.strip() for t in response.css("#product_description + p ::text").getall() if t.strip()
        )
        price_text = response.css("div.product_main p.price_color::text").get() or ""
        price_match = re.search(r"\d+(?:\.\d+)?", price_text)
        rating_classes = (response.css("div.product_main p.star-rating::attr(class)").get() or "").split()
        availability = " ".join(
            t.strip() for t in response.css("div.product_main p.availability ::text").getall() if t.strip()
        )
        category = response.css("ul.breadcrumb li:nth-child(3) a::text").get()

        yield {
            "doc_id": hashlib.sha1(response.url.encode("utf-8")).hexdigest()[:12],
            "title": title,
            "text": "\n".join(part for part in (title, description) if part),
            "description": description,
            "url": response.url,
            "category": category.strip() if category else None,
            "price_gbp": float(price_match.group()) if price_match else None,
            "rating": next((RATINGS[c] for c in rating_classes if c in RATINGS), None),
            "availability": availability or None,
            "source": "books.toscrape.com",
        }
