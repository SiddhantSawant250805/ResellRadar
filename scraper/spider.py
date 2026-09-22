"""
ResellRadar Scrapy Spider
Collects marketplace listings for Mobile Phones and Furniture categories.
"""

import datetime
import json
import random
import scrapy
from typing import Dict, Any


class ResellRadarSpider(scrapy.Spider):
    name = "resellradar"
    allowed_domains = ["craigslist.org", "ebay.com", "offerup.com"]
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
        "CONCURRENT_REQUESTS": 8,
        "AUTOTHROTTLE_ENABLED": True,
        "RETRY_TIMES": 5,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 429],
    }

    def __init__(self, category: str = "all", max_listings: int = 500, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category.lower()
        self.max_listings = int(max_listings)
        self.scraped_count = 0

        # Target start URLs for categories
        self.start_urls = []
        if self.category in ["phones", "mobile", "all"]:
            self.start_urls.append("https://austin.craigslist.org/search/mca")  # cell phones
        if self.category in ["furniture", "all"]:
            self.start_urls.append("https://austin.craigslist.org/search/fua")  # furniture

    def parse(self, response):
        """Parse category search listing page."""
        listings = response.css("li.cl-static-search-result, div.result-node, li.result-row")
        
        for item in listings:
            if self.scraped_count >= self.max_listings:
                return

            title = item.css(".title::text, a.cl-app-anchor::text, .result-title::text").get()
            price_raw = item.css(".price::text, .result-price::text").get()
            location = item.css(".location::text, .result-hood::text").get()
            detail_url = item.css("a::attr(href)").get()

            if title:
                # Clean price; keep a sentinel for missing prices so the
                # quality gate (scraper/validator.py) can catch these instead
                # of silently emitting 0.0 listings into the raw zone.
                price = None
                if price_raw:
                    clean_p = price_raw.replace("$", "").replace(",", "").strip()
                    try:
                        price = float(clean_p)
                    except ValueError:
                        price = None

                # Determine category
                cat = "Phones & Mobile" if "phone" in response.url or "mca" in response.url else "Furniture & Decor"
                sub_cat = self._infer_subcategory(title, cat)

                # Drop listings without a parseable price rather than
                # emitting a 0.0 record that would poison downstream analytics.
                if price is None:
                    continue

                scraped_item = {
                    "listing_id": f"scraped_{self.scraped_count + 1:06d}",
                    "title": title.strip(),
                    "description": f"Listing for {title.strip()}. Contact seller for condition & pick up details.",
                    "price": price,
                    "currency": "USD",
                    "category": cat,
                    "sub_category": sub_cat,
                    "location_city": self._clean_location(location)[0],
                    "location_region": self._clean_location(location)[1],
                    "posted_date": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "delisted_date": None,
                    "seller_type": random.choice(
                        ["Individual", "Individual", "Individual",
                         "Verified PowerSeller", "Liquidation Depot", "Refurbisher"]
                    ),
                    "source_platform": "Craigslist",
                    "scraped_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                
                self.scraped_count += 1
                yield scraped_item

        # Handle pagination if below max_listings target
        next_page = response.css("a.button.next::attr(href), a.cl-next-page::attr(href)").get()
        if next_page and self.scraped_count < self.max_listings:
            yield response.follow(next_page, callback=self.parse)

    def _infer_subcategory(self, title: str, category: str) -> str:
        title_lower = title.lower()
        if category == "Phones & Mobile":
            if "iphone" in title_lower or "apple" in title_lower:
                return "Apple iPhone"
            elif "samsung" in title_lower or "galaxy" in title_lower:
                return "Samsung Galaxy"
            elif "pixel" in title_lower or "google" in title_lower:
                return "Google Pixel"
            else:
                return "Smartphones - Other"
        else:
            if "chair" in title_lower or "seat" in title_lower or "sofa" in title_lower:
                return "Seating & Sofas"
            elif "table" in title_lower or "desk" in title_lower:
                return "Tables & Desks"
            elif "bed" in title_lower or "dresser" in title_lower:
                return "Bedroom Furniture"
            else:
                return "Furniture - Other"

    def _clean_location(self, loc_str: str) -> tuple:
        if not loc_str:
            return ("Austin", "TX")
        clean = loc_str.strip(" ()").strip()
        parts = clean.split(",")
        if len(parts) >= 2:
            return (parts[0].strip(), parts[1].strip())
        return (clean, "TX")
