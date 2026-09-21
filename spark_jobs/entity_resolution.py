from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    split,
    array_distinct,
    row_number,
    regexp_replace,
    lower,
    trim,
    when,
    concat_ws
)
from pyspark.sql.window import Window
from pyspark.ml.feature import HashingTF, MinHashLSH


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = str(
    BASE_DIR / "data" / "processed" / "clean_listings.parquet"
)

OUTPUT_PATH = str(
    BASE_DIR / "data" / "processed" / "entity_resolved.parquet"
)


# ============================================================
# 1. START SPARK
# ============================================================

spark = SparkSession.builder \
    .appName("ResellRadar-EntityResolution") \
    .master("local[*]") \
    .config("spark.hadoop.io.native.lib.available", "false") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")


# ============================================================
# 2. READ CLEAN DATA
# ============================================================

print("Reading:")
print(INPUT_PATH)

df = spark.read.parquet(INPUT_PATH)

total_records = df.count()

print("\n========== DATASET ==========")
print("Total Records:", total_records)


# ============================================================
# 3. GET UNIQUE TITLES
# ============================================================

unique_titles = df.select(
    "title_clean"
).distinct()

unique_count = unique_titles.count()

print("Unique Titles:", unique_count)


# ============================================================
# 4. CREATE MODEL-AWARE KEY
# ============================================================

# Remove common listing-level attributes.
# These should NOT define the underlying product entity.

model_key_df = unique_titles.withColumn(
    "model_key",
    col("title_clean")
)

# Remove storage sizes
model_key_df = model_key_df.withColumn(
    "model_key",
    regexp_replace(
        col("model_key"),
        r"\b(16|32|64|128|256|512)\s*gb\b",
        ""
    )
)

model_key_df = model_key_df.withColumn(
    "model_key",
    regexp_replace(
        col("model_key"),
        r"\b(1|2)\s*tb\b",
        ""
    )
)

# Remove common colors
model_key_df = model_key_df.withColumn(
    "model_key",
    regexp_replace(
        col("model_key"),
        r"\b(black|white|blue|red|green|yellow|purple|pink|gray|grey|"
        r"silver|gold|snow|sea|charcoal|natural|tan|brown|beige)\b",
        ""
    )
)

# Remove condition / listing phrases
model_key_df = model_key_df.withColumn(
    "model_key",
    regexp_replace(
        col("model_key"),
        r"\b(like new|mint condition|excellent condition|good condition|"
        r"fair condition|great condition|fully functional|minor scuffs|"
        r"with box|original box|unlocked|battery health)\b",
        ""
    )
)

# Clean extra spaces
model_key_df = model_key_df.withColumn(
    "model_key",
    trim(
        regexp_replace(
            col("model_key"),
            r"\s+",
            " "
        )
    )
)


# ============================================================
# 5. PROTECT MODEL DIFFERENCES
# ============================================================

# IMPORTANT:
# "iPhone 15 Pro" and "iPhone 15 Pro Max" are different models.
#
# We explicitly preserve "pro max" as part of the model key.

model_key_df = model_key_df.withColumn(
    "model_key",
    when(
        col("model_key").contains("pro max"),
        regexp_replace(
            col("model_key"),
            r"\bpro max\b",
            "promax"
        )
    ).otherwise(
        col("model_key")
    )
)


# ============================================================
# 6. TOKENIZE MODEL KEY
# ============================================================

model_key_df = model_key_df.withColumn(
    "tokens",
    array_distinct(
        split(col("model_key"), " ")
    )
)


# ============================================================
# 7. HASH TITLE TOKENS
# ============================================================

hashing_tf = HashingTF(
    inputCol="tokens",
    outputCol="features",
    numFeatures=4096
)

model_key_df = hashing_tf.transform(model_key_df)


# ============================================================
# 8. MINHASH LSH
# ============================================================

mh = MinHashLSH(
    inputCol="features",
    outputCol="hashes",
    numHashTables=5
)

model = mh.fit(model_key_df)

print("\n========== MINHASH LSH ==========")
print("MinHash model created successfully.")


# ============================================================
# 9. FIND SIMILAR MODEL CANDIDATES
# ============================================================

pairs = model.approxSimilarityJoin(
    model_key_df,
    model_key_df,
    0.3,
    distCol="jaccard_distance"
)

pairs = pairs.filter(
    col("datasetA.title_clean") <
    col("datasetB.title_clean")
)


# ============================================================
# 10. REMOVE FALSE MODEL MATCHES
# ============================================================

# Do not connect Pro and Pro Max.
pairs = pairs.filter(
    ~(
        col("datasetA.model_key").contains("pro ")
        &
        col("datasetB.model_key").contains("promax")
    )
)

pairs = pairs.filter(
    ~(
        col("datasetA.model_key").contains("promax")
        &
        col("datasetB.model_key").contains("pro ")
    )
)


print("\n========== SIMILAR MODEL PAIRS ==========")

pairs.select(
    col("datasetA.title_clean").alias("title_a"),
    col("datasetB.title_clean").alias("title_b"),
    col("datasetA.model_key").alias("model_a"),
    col("datasetB.model_key").alias("model_b"),
    col("jaccard_distance")
).orderBy(
    col("jaccard_distance").asc()
).show(
    30,
    truncate=False
)


# ============================================================
# 11. CREATE ENTITY ID
# ============================================================

# Each unique model_key represents one underlying product model.

window = Window.orderBy("model_key")

model_entities = model_key_df.select(
    "model_key"
).distinct().withColumn(
    "entity_id",
    row_number().over(window)
)


# ============================================================
# 12. CREATE MODEL -> ENTITY MAPPING
# ============================================================

model_mapping = model_entities.select(
    "model_key",
    "entity_id"
)


# ============================================================
# 13. MAP ENTITY IDS TO UNIQUE TITLES
# ============================================================

title_mapping = model_key_df.select(
    "title_clean",
    "model_key"
).join(
    model_mapping,
    on="model_key",
    how="left"
).select(
    "title_clean",
    "entity_id"
)


# ============================================================
# 14. MAP ENTITY IDS BACK TO ALL LISTINGS
# ============================================================

df = df.join(
    title_mapping,
    on="title_clean",
    how="left"
)


# ============================================================
# 15. CHECK ENTITY DISTRIBUTION
# ============================================================

print("\n========== ENTITY RESULTS ==========")

print(
    "Unique Entities:",
    df.select("entity_id").distinct().count()
)

print(
    "Listings with Entity ID:",
    df.filter(col("entity_id").isNotNull()).count()
)


# ============================================================
# 16. SAVE OUTPUT
# ============================================================

print("\n========== SAVING OUTPUT ==========")

df.select(
    "listing_id",
    "title",
    "description",
    "price",
    "currency",
    "category",
    "sub_category",
    "location_city",
    "location_region",
    "posted_date",
    "delisted_date",
    "seller_type",
    "source_platform",
    "scraped_at",
    "entity_id"
).write.mode("overwrite").parquet(
    OUTPUT_PATH
)


print("\nSUCCESS!")
print("Entity-resolved dataset saved to:")
print(OUTPUT_PATH)


spark.stop()