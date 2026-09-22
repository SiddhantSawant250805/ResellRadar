# Spark Big Data Processing Setup

## 1. Environment Requirements

The Big Data Processing pipeline was developed and tested using:

| Component | Version |
| --------- | ------- |
| Python    | 3.12.2  |
| PySpark   | 4.2.0   |
| Java      | 19.0.2  |
| Hadoop    | 3.5.0   |

The pipeline uses Apache Spark through PySpark.

---

## 2. Create Python Virtual Environment

From the project root:

```powershell
python -m venv venv
```

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

---

## 3. Install Required Python Packages

Install PySpark and NumPy:

```powershell
pip install pyspark==4.2.0 numpy
```

Verify PySpark:

```powershell
python -c "import pyspark; print(pyspark.__version__)"
```

Expected:

```text
4.2.0
```

---

## 4. Java Configuration

Java 19.0.2 is required for the tested environment.

Set `JAVA_HOME` in PowerShell:

```powershell
$env:JAVA_HOME="C:\Program Files\Java\jdk-19"
```

Verify Java:

```powershell
java -version
```

Expected:

```text
java version "19.0.2"
```

---

## 5. Windows Hadoop Helper

For Windows, Spark requires Hadoop native helper files for local execution.

The tested setup uses Hadoop 3.5.0 files matching the Hadoop version bundled with PySpark.

Set the Hadoop environment variables:

```powershell
$env:HADOOP_HOME="C:\path\to\ResellRadar\hadoop"
$env:HADOOP_COMMON_HOME="C:\path\to\ResellRadar\hadoop"
$env:PATH="C:\path\to\ResellRadar\hadoop\bin;$env:PATH"
```

The `hadoop/` directory is intentionally excluded from Git because it contains machine-specific Windows binaries.

Each Windows machine running the Spark pipeline should have its own compatible Hadoop helper setup.

---

## 6. Input Dataset

The Spark pipeline expects the cleaned input data to originate from the project's raw listings dataset.

The raw dataset is not committed to Git because of its size.

The project uses:

```text
data/raw/
```

for raw JSON data.

The raw JSON array is converted to JSON Lines format before Spark processing:

```text
data/processed/raw_listings.jsonl
```

---

## 7. Run the Big Data Processing Pipeline

Run the following scripts from the project root.

### Step 1 — Cleaning and Normalization

```powershell
python spark_jobs/clean_normalize.py
```

Output:

```text
data/processed/clean_listings.parquet
```

This step performs:

* Schema normalization
* Text cleaning
* Timestamp conversion
* Null handling
* Duplicate listing removal
* Parquet conversion

---

### Step 2 — Entity Resolution

```powershell
python spark_jobs/entity_resolution.py
```

Output:

```text
data/processed/entity_resolved.parquet
```

This step performs:

* Model/title normalization
* Removal of non-identifying attributes such as color, storage size and condition phrases
* MinHash-based similarity matching
* Entity grouping
* Entity ID assignment

The tested dataset produced:

```text
50,000 listings
79 unique entities
```

---

### Step 3 — Feature Engineering

```powershell
python spark_jobs/feature_engineering.py
```

This generates the curated analytics datasets:

```text
data/curated/depreciation_curve_curated.parquet
data/curated/resale_velocity_curated.parquet
data/curated/regional_price_variance_curated.parquet
```

The generated analytics include:

* Depreciation curves
* Resale velocity
* Regional price variance

---

## 8. Processing Flow

```text
Raw Listings
     ↓
Cleaning & Normalization
     ↓
clean_listings.parquet
     ↓
Entity Resolution
     ↓
entity_resolved.parquet
     ↓
Feature Engineering
     ↓
Curated Analytics Tables
```

---

## 9. Important Git/Data Note

Generated datasets are intentionally excluded from Git:

```text
data/raw/
data/processed/
data/curated/
```

The repository stores the **processing code**, while datasets should be shared separately through the team's agreed data storage/HDFS setup.

Do not commit large raw JSON files or generated Parquet directories to GitHub.

---

## 10. Recommended Run Order for Integration

After pulling the Big Data Processing branch:

```powershell
git pull
```

Install the required environment and configure Java/Hadoop.

Then run:

```powershell
python spark_jobs/clean_normalize.py
python spark_jobs/entity_resolution.py
python spark_jobs/feature_engineering.py
```

After successful execution, the curated Parquet datasets can be consumed by the project's downstream analytics/dashboard components.
