# ResellRadar Raw Ingestion Data Schema Contract

**Author**: Person 1 (Data Engineering Lead)  
**Target Consumers**: Person 2 (PySpark Cleaning & MinHash LSH Entity Resolution Pipeline)  
**Version**: `1.0.0`  
**Storage Layer**: `data/raw/raw_*.json` & HDFS `/data/raw/`

---

## 1. Overview & Data Invariant
This document specifies the immutable JSON schema contract for all raw second-hand marketplace listings ingested into ResellRadar's raw storage zone (`/data/raw/`).

- **Format**: JSON Array of Objects (UTF-8 Encoded)
- **Immutability Guarantee**: Raw JSON files remain unmutated after ingestion. Person 2's Spark job reads from this path into `data/processed/`.
- **Nullability Rules**: Primary key, category, title, price, and timestamp fields are strictly required (`Non-Nullable`). Delisted dates are nullable (`Optional`).

---

## 2. Field Specifications

| Field Name | Data Type | Nullable | Description & Constraints | Sample Value |
| :--- | :--- | :--- | :--- | :--- |
| `listing_id` | `String` | **No** | Unique identifier formatted as `RR-{CAT_CODE}-{ID}` or `scraped_{ID}`. | `"RR-P-0004291"` |
| `title` | `String` | **No** | Raw listing title extracted from marketplace source. | `"Apple iPhone 15 Pro Max 256GB Natural Titanium"` |
| `description` | `String` | **No** | Freeform text description provided by seller. | `"Unlocked, mint condition with box. Battery health 98%."` |
| `price` | `Float` | **No** | Item price in USD currency. Decimal float >= 0.0. | `890.00` |
| `currency` | `String` | **No** | 3-letter ISO currency code. | `"USD"` |
| `category` | `String` | **No** | Top-level marketplace category (`"Phones & Mobile"` \| `"Furniture & Decor"`). | `"Phones & Mobile"` |
| `sub_category` | `String` | **No** | Inferred subcategory for entity resolution seeding. | `"Apple iPhone"` |
| `location_city` | `String` | **No** | Metropolitan city where item is located. | `"Austin"` |
| `location_region` | `String` | **No** | State / Region code (e.g. 2-letter postal code). | `"TX"` |
| `posted_date` | `String` | **No** | ISO-8601 timestamp when listing was posted (`YYYY-MM-DDTHH:MM:SSZ`). | `"2026-09-10T14:30:00Z"` |
| `delisted_date` | `String` | **Yes** | ISO-8601 timestamp when item was sold/delisted, or `null` if active. | `"2026-09-14T09:15:00Z"` |
| `seller_type` | `String` | **No** | Type of seller (`"Individual"`, `"Verified PowerSeller"`, `"Liquidation Depot"`, `"Refurbisher"`). | `"Individual"` |
| `source_platform` | `String` | **No** | Source marketplace (`"Craigslist"`, `"Facebook Marketplace"`, `"OfferUp"`, `"eBay Refurbished"`). | `"Facebook Marketplace"` |
| `scraped_at` | `String` | **No** | Ingestion timestamp when record was scraped into raw lake zone. | `"2026-09-15T10:00:00Z"` |

---

## 3. Sample JSON Payload

```json
[
  {
    "listing_id": "RR-P-0004291",
    "title": "Apple iPhone 15 Pro Max 256GB Natural Titanium - Like New - Unlocked with Box",
    "description": "Selling my Apple iPhone 15 Pro Max (256GB, Natural Titanium). Unlocked for all carriers. Battery health is at 98%. Comes with original USB-C cable.",
    "price": 890.00,
    "currency": "USD",
    "category": "Phones & Mobile",
    "sub_category": "Apple iPhone",
    "location_city": "Austin",
    "location_region": "TX",
    "posted_date": "2026-09-10T14:30:00Z",
    "delisted_date": "2026-09-14T09:15:00Z",
    "seller_type": "Individual",
    "source_platform": "Facebook Marketplace",
    "scraped_at": "2026-09-15T10:00:00Z"
  },
  {
    "listing_id": "RR-F-0008124",
    "title": "Herman Miller Aeron Chair Remastered (Size B / Fully Loaded) - Great Condition",
    "description": "Herman Miller Aeron Chair Remastered in Size B / Fully Loaded. Clean, smoke-free home. Must bring truck/van for pickup in Seattle, WA.",
    "price": 650.00,
    "currency": "USD",
    "category": "Furniture & Decor",
    "sub_category": "Seating & Office",
    "location_city": "Seattle",
    "location_region": "WA",
    "posted_date": "2026-09-12T18:05:00Z",
    "delisted_date": null,
    "seller_type": "Individual",
    "source_platform": "OfferUp",
    "scraped_at": "2026-09-15T10:00:00Z"
  }
]
```

---

## 4. PySpark StructType Schema Reference (For Person 2)

Person 2 can load raw JSON files directly in PySpark with the explicit schema below:

```python
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

raw_schema = StructType([
    StructField("listing_id", StringType(), False),
    StructField("title", StringType(), False),
    StructField("description", StringType(), False),
    StructField("price", DoubleType(), False),
    StructField("currency", StringType(), False),
    StructField("category", StringType(), False),
    StructField("sub_category", StringType(), False),
    StructField("location_city", StringType(), False),
    StructField("location_region", StringType(), False),
    StructField("posted_date", StringType(), False),
    StructField("delisted_date", StringType(), True),
    StructField("seller_type", StringType(), False),
    StructField("source_platform", StringType(), False),
    StructField("scraped_at", StringType(), False)
])

# Loading raw files:
# df_raw = spark.read.schema(raw_schema).json("hdfs://localhost:9000/data/raw/*.json")
```
