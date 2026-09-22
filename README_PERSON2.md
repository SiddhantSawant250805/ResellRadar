# ResellRadar — Big Data Processing Pipeline (Person 2)

**ResellRadar** is a Big Data Analytics mini-project featuring a distributed data pipeline that mines second-hand marketplace listings (Mobile Phones and Furniture) to compute product depreciation curves, resale velocity, and regional price arbitrage opportunities.

This document covers **Person 2's Role: Big Data Processing Engineer (Core BDA component)**. Person 2 owns the Spark cleaning, entity resolution, and feature engineering stages, taking raw listings from Person 1's ingestion layer (`data/raw/`) and producing canonicalized, deduplicated datasets plus aggregated analytics tables for Person 3's graph/visualization layer (`data/curated/`).

---

## 👤 Role Ownership

| Area | Ownership |
| ---- | --------- |
| Spark cleaning & normalization | ✅ Person 2 |
| Entity resolution (MinHash LSH) | ✅ Person 2 |
| Feature engineering (Spark SQL) | ✅ Person 2 |
| `spark_jobs/` module | ✅ Person 2 |
| `data/processed/` zone | ✅ Person 2 |
| `data/curated/` zone | ✅ Person 2 |
| Scraper / HDFS ingestion | ❌ Person 1 |
| Graph / Streamlit dashboard | ❌ Person 3 |

---

## 🛠️ Tech Stack

- **Processing Engine**: Apache Spark via PySpark **4.2.0** (`local[*]` mode)
- **MLlib**: `HashingTF` + `MinHashLSH` for entity resolution
- **Window Functions & Spark SQL**: depreciation, velocity, and regional aggregations
- **Storage Format**: Parquet (`data/processed/` and `data/curated/`)
- **Environment**: Python 3.12.2, Java 19.0.2, Hadoop 3.5.0 Windows helper binaries (untracked)
- Full setup instructions: [`docs/SPARK_SETUP.md`](docs/SPARK_SETUP.md)

---

## 📁 Files Owned by Person 2 (Currently in the Codebase)

```text
ResellRadar/
├── spark_jobs/
│   ├── clean_normalize.py      # Stage 1 — schema normalization & text preprocessing
│   ├── entity_resolution.py    # Stage 2 — MinHash LSH clustering & entity IDs
│   └── feature_engineering.py  # Stage 3 — curated analytics tables
├── docs/
│   └── SPARK_SETUP.md          # Environment, Java/Hadoop & run documentation
├── data/
│   ├── processed/              # Person 2 output zone (Parquet, untracked)
│   └── curated/                # Person 2 curated analytics (Parquet, untracked)
└── requirements.txt            # pyspark==4.2.0 and numpy added by Person 2
```

---

## ⚙️ Pipeline Stages — What Was Built

### Stage 1 — `spark_jobs/clean_normalize.py`

Reads the JSON Lines conversion of Person 1's raw lake (`data/processed/raw_listings.jsonl`) with an explicit `StructType` schema and produces `data/processed/clean_listings.parquet`.

- **Schema enforcement** — 14-field `StructType` covering listing IDs, title/description, price, category, location, and platform metadata
- **Null handling** — `dropna` on the critical columns (`listing_id`, `title`, `description`, `price`, `category`, `posted_date`)
- **Text preprocessing** — lowercasing, trimming, and non-alphanumeric stripping into `title_clean` / `description_clean`
- **Timestamp conversion** — `posted_date`, `delisted_date`, `scraped_at` cast from strings to timestamps
- **Deduplication** — exact duplicate removal on `listing_id`
- **Parquet conversion** — columnar output for the downstream stages

### Stage 2 — `spark_jobs/entity_resolution.py` (Technical Centerpiece)

Consumes `clean_listings.parquet` and assigns every listing an `entity_id`, producing `data/processed/entity_resolved.parquet`. Implements the MinHash LSH clustering required by the task spec (delivered as `entity_resolution.py`).

- **Model-key construction** — strips listing-level attributes that should not define the underlying product: storage sizes (`16 GB` … `512 GB`, `1 TB`/`2 TB`), common colors (18 terms), and condition phrases (`like new`, `with box`, `unlocked`, `battery health`, …)
- **Model-difference protection** — explicitly preserves `pro max` as a token (`promax`) so *iPhone 15 Pro* and *iPhone 15 Pro Max* are never merged, with a symmetric pair filter blocking Pro ↔ Pro Max joins
- **Tokenization & hashing** — distinct token sets hashed via `HashingTF` (4096 features)
- **MinHash LSH** — `MinHashLSH` with 5 hash tables; `approxSimilarityJoin` with Jaccard distance threshold **0.3** to generate candidate similar-title pairs
- **Entity assignment** — each distinct `model_key` becomes one product entity; `row_number()` over a window assigns `entity_id`, mapped back onto every listing
- **Validated result** — 50,000 listings collapsed to **79 unique entities**

### Stage 3 — `spark_jobs/feature_engineering.py`

Consumes `entity_resolved.parquet` and writes three curated analytics tables to `data/curated/`:

| Output Table | Key Columns | Method |
| ------------ | ----------- | ------ |
| `depreciation_curve_curated.parquet` | `entity_id`, `listing_age_months`, `listing_count`, `average_price`, `median_price`, `baseline_price`, `price_change_percent` | First-seen entity date → `months_between` age buckets → avg/percentile price vs. age-0 baseline |
| `resale_velocity_curated.parquet` | `entity_id`, `delisted_listings`, `avg_resale_days`, `median_resale_days` | `datediff(posted, delisted)` on delisted listings, aggregated per entity |
| `regional_price_variance_curated.parquet` | `entity_id`, `location_region`, `listing_count`, `average_price`, `price_stddev`, `min/max_regional_price`, `regional_price_range` | Per-entity regional groupBy with windowed min/max price spread |

Also computes `resale_duration_days` on the entity-resolved frame as the velocity input.

---

## 🚀 How to Run (Person 2's Pipeline)

Prerequisites (venv, PySpark, `JAVA_HOME`, Windows Hadoop helpers) are documented in [`docs/SPARK_SETUP.md`](docs/SPARK_SETUP.md). Then run from the project root, in order:

```powershell
python spark_jobs/clean_normalize.py      # → data/processed/clean_listings.parquet
python spark_jobs/entity_resolution.py    # → data/processed/entity_resolved.parquet
python spark_jobs/feature_engineering.py  # → data/curated/*.parquet (3 tables)
```

Input contract: the raw JSON array from `data/raw/` must be converted to JSON Lines at `data/processed/raw_listings.jsonl` before Stage 1.

---

## 🔄 Data Flow

```text
Person 1: data/raw/*.json  (HDFS raw lake)
     ↓  (convert to JSONL: data/processed/raw_listings.jsonl)
Stage 1: clean_normalize.py
     ↓
data/processed/clean_listings.parquet
     ↓
Stage 2: entity_resolution.py  (MinHash LSH)
     ↓
data/processed/entity_resolved.parquet
     ↓
Stage 3: feature_engineering.py
     ↓
Person 3: data/curated/*.parquet  (dashboard & graph inputs)
```

---

## 📌 Git History — Person 2's Commits

All work was developed on the `feature/big-data-processing` branch and merged to `main` via **Pull Request #1**.

| Commit | Date | Message | Changes |
| ------ | ---- | ------- | ------- |
| `e07be81` | 2026-09-22 | Add Spark big data processing pipeline | Added `spark_jobs/clean_normalize.py`, `spark_jobs/entity_resolution.py`, `spark_jobs/feature_engineering.py`; updated `.gitignore` |
| `5bae87a` | 2026-09-22 | Add Spark setup documentation | Added `docs/SPARK_SETUP.md` |
| `bf24ce4` | 2026-09-22 | Add Spark dependencies | Added `pyspark==4.2.0`, `numpy` to `requirements.txt` |

---

## ✅ Deliverable Status

> **Spec deliverable**: canonicalized, deduplicated dataset + aggregated analytics tables — **Complete**

- Canonicalized, deduplicated dataset → `data/processed/entity_resolved.parquet` (50,000 listings → 79 entities)
- Aggregated analytics tables → 3 curated Parquet tables in `data/curated/`
- Datasets are intentionally git-ignored (see `docs/SPARK_SETUP.md` §9) and are shared through the team's agreed HDFS/storage setup — the repository carries the processing code only.
