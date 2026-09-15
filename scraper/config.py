"""
ResellRadar Scraper Configuration
Defines Scrapy settings, rate limiting, retry middleware, and user-agent settings.
"""

BOT_NAME = "resellradar_bot"

SPIDER_MODULES = ["scraper.spider"]
NEWSPIDER_MODULE = "scraper.spider"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Rate limiting & throttling
CONCURRENT_REQUESTS = 16
DOWNLOAD_DELAY = 1.0  # 1 second delay between requests
RANDOMIZE_DOWNLOAD_DELAY = True

# AutoThrottle Extension
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# Retry middleware configuration for graceful handling of rate-limiting/throttling
RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Default Request Headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "User-Agent": "ResellRadar-DataIngestBot/1.0 (+http://resellradar.edu; student big-data project)",
}

# Feed Exporter Settings
FEED_FORMAT = "json"
FEED_EXPORT_ENCODING = "utf-8"
