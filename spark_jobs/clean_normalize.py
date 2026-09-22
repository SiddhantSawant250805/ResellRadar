import os

os.environ["HADOOP_HOME"] = os.getcwd() + "\\hadoop"
os.environ["hadoop.home.dir"] = os.getcwd() + "\\hadoop"

from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType
)
from pyspark.sql.functions import (
    col, lower, trim,
    regexp_replace, to_timestamp
)

# -------------------------------------------------
# Project paths
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = str(BASE_DIR / "data" / "processed" / "raw_listings.jsonl")
OUTPUT_PATH = str(BASE_DIR / "data" / "processed" / "clean_listings.parquet")

print("Reading from:")
print(RAW_PATH)

# -------------------------------------------------
# Spark Session
# -------------------------------------------------
spark = SparkSession.builder \
    .appName("ResellRadar-CleanNormalize") \
    .master("local[*]") \
    .config("spark.hadoop.io.native.lib.available", "false") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# -------------------------------------------------
# Schema
# -------------------------------------------------
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

# -------------------------------------------------
# Read JSON
# -------------------------------------------------
df = spark.read.schema(raw_schema).json(RAW_PATH)

print("\n========== RAW DATA ==========")
print("Total Records:", df.count())

# -------------------------------------------------
# Remove missing values
# -------------------------------------------------
df = df.dropna(subset=[
    "listing_id",
    "title",
    "description",
    "price",
    "category",
    "posted_date"
])

# -------------------------------------------------
# Clean text
# -------------------------------------------------
df = df.withColumn(
    "title_clean",
    lower(
        trim(
            regexp_replace(
                col("title"),
                "[^A-Za-z0-9 ]",
                ""
            )
        )
    )
)

df = df.withColumn(
    "description_clean",
    lower(
        trim(
            regexp_replace(
                col("description"),
                "[^A-Za-z0-9 ]",
                ""
            )
        )
    )
)

# -------------------------------------------------
# Convert dates
# -------------------------------------------------
df = df.withColumn(
    "posted_date",
    to_timestamp("posted_date")
)

df = df.withColumn(
    "delisted_date",
    to_timestamp("delisted_date")
)

df = df.withColumn(
    "scraped_at",
    to_timestamp("scraped_at")
)

# -------------------------------------------------
# Remove duplicates
# -------------------------------------------------
df = df.dropDuplicates(["listing_id"])

print("Clean Records:", df.count())

# -------------------------------------------------
# Preview
# -------------------------------------------------
print("\n========== SAMPLE ==========")

df.select(
    "listing_id",
    "title",
    "title_clean",
    "price",
    "location_city"
).show(10, truncate=False)

# -------------------------------------------------
# Save Parquet
# -------------------------------------------------
df.write.mode("overwrite").parquet(OUTPUT_PATH)

print("\n========== SUCCESS ==========")
print("Saved to:")
print(OUTPUT_PATH)

spark.stop()