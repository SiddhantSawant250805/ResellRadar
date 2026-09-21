Person 1 — Data Engineer (Ingestion + Storage)

Owns: Scraper, HDFS setup, raw data pipeline

Build the Scrapy spider (or synthetic data generator) for phones + furniture listings
Set up local pseudo-distributed Hadoop cluster, push raw data to HDFS
Handle data quality at the source: rate limiting, retry logic, schema consistency in raw JSON
Own /data/raw/ and the scraper/ module
Deliverable: 50k+ clean raw listings landing reliably in HDFS
Person 2 — Big Data Processing Engineer (Core BDA component)

Owns: Spark cleaning, entity resolution, feature engineering

Build clean_normalize.py — schema normalization, text preprocessing
Build entity_resolution_minhash.py — MinHash LSH clustering (the technical centerpiece — this person should be comfortable tuning Jaccard thresholds/hash tables)
Build feature_engineering.py — depreciation curves, resale velocity, regional price variance via Spark SQL
Own /data/processed/, /data/curated/, and most of spark_jobs/
Deliverable: canonicalized, deduplicated dataset + aggregated analytics tables
Person 3 — Graph & Visualization Engineer (Presentation layer)

Owns: Graph construction, dashboard, demo

Build build_graph.py — NetworkX graph, PageRank/connected-components for arbitrage clustering
Build the Streamlit dashboard (app.py) — depreciation charts, regional heatmap, velocity distributions
Own the final demo flow and visual polish (this person should also lead the report's diagrams/screenshots)
Deliverable: interactive dashboard + graph visualizations ready for evaluation
Shared responsibilities (all 3)
Report writing — each person writes the section for their own component (methodology-per-module)
Integration testing — once Person 2's curated tables are ready, Person 3 wires them into the dashboard; Person 1's raw data feeding Person 2's pipeline needs a joint checkpoint
