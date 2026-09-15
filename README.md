# ResellRadar — Data Ingestion & Raw Storage Layer (Person 1)

**ResellRadar** is a Big Data Analytics mini-project featuring a distributed data pipeline that mines second-hand marketplace listings (Mobile Phones and Furniture) to compute product depreciation curves, resale velocity, and regional price arbitrage opportunities.

This component implements **Person 1's Role: Data Engineering (Ingestion + Raw Storage Layer)**. The downstream Big Data Processing (PySpark cleaning, MinHash LSH entity resolution) and Graph/Visualization layers are owned by teammates and interface via clean schema contracts.

---

## 🛠️ Tech Stack & Architecture

- **Data Ingestion Engine**: Scrapy Spider ([`scraper/spider.py`](scraper/spider.py)) & High-Throughput Synthetic Listing Generator ([`scraper/generator.py`](scraper/generator.py)) targeting **50,000+ listings**.
- **Rate Limiting & Resilience**: AutoThrottle, request delays, user-agent rotation, and exponential backoff retry middleware ([`scraper/config.py`](scraper/config.py)).
- **Raw Lake Zone**: Immutable JSON batched storage ([`data/raw/`](data/raw/)).
- **HDFS Ingestion Engine**: Python HDFS sync module ([`hdfs_uploader.py`](hdfs_uploader.py)) supporting single-node Hadoop WebHDFS (`http://localhost:9870`), HDFS CLI, and local pseudo-emulated cluster mode.
- **Backend Control Server**: FastAPI server ([`server.py`](server.py)) with REST & live telemetry streaming APIs.
- **Control Panel Dashboard**: Next.js 14 App Router UI generated from Stitch MCP design tokens and polished with cyber-telemetry aesthetics ([`dashboard/`](dashboard/)).
- **Interface Contract**: Schema specification for downstream PySpark jobs ([`scraper/SCHEMA.md`](scraper/SCHEMA.md)).

---

## 📁 Repository Structure

```text
ResellRadar/
├── scraper/
│   ├── __init__.py
│   ├── config.py           # Scrapy autothrottle, delays & retry rules
│   ├── spider.py           # Scrapy spider for marketplace scraping
│   ├── generator.py        # 50,000+ synthetic listing generator
│   └── SCHEMA.md           # Raw JSON schema contract for Person 2 (Spark pipeline)
├── hdfs_uploader.py        # HDFS push engine (WebHDFS / CLI / Pseudo-Emulated)
├── server.py               # FastAPI control server (ports & REST endpoints)
├── dashboard/              # Next.js 14 Control Panel Web App (Stitch UI)
│   ├── app/                # Layouts & page views
│   ├── components/         # Telemetry cards, Job triggers, Log stream, HDFS panel, Data preview
│   ├── tailwind.config.js  # Stitch design system tokens
│   └── package.json
├── data/
│   ├── raw/                # Raw immutable JSON lake zone
│   ├── processed/          # Placeholder for Person 2 (PySpark cleaned data)
│   └── curated/            # Placeholder for Person 3 (Parquet & Graph export)
├── requirements.txt        # Python backend dependencies
├── .gitignore              # Repository gitignore rules
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Python Virtual Environment Setup

```bash
# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
```

### 2. Start FastAPI Backend Control Server

```bash
python server.py
# Server runs on http://127.0.0.1:8000
```

### 3. Start Next.js Control Panel UI

```bash
cd dashboard
npm install
npm run dev
# Dashboard opens at http://localhost:3000
```

---

## ⚡ Command Line Operations

### Generate 50,000+ Listing Sample Batch

```bash
python -c "from scraper.generator import generate_batch; generate_batch(count=50000, category='all')"
# Outputs: data/raw/raw_all_YYYY_MM_DD_HHMMSS.json (~40 MB)
```

### Push Raw Data to HDFS

```bash
python hdfs_uploader.py
# Pushes un-synced JSON files from data/raw/ to HDFS path /data/raw/
```

---

## 📄 Schema Contract Reference (`scraper/SCHEMA.md`)

Downstream PySpark cleaning jobs consume raw JSON files directly from HDFS `/data/raw/*.json`. For full field definitions, nullable constraints, and PySpark `StructType` code snippets, refer to [`scraper/SCHEMA.md`](scraper/SCHEMA.md).
