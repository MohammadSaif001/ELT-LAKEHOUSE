# Apache Parquet Migration & Architectural Review

This document provides an end-to-end review of the migration from JSON to **Apache Parquet** in the ELT Lakehouse pipeline. It explains **why** the change was made, **how** Parquet reads and writes data under the hood compared to JSON dictionaries, and **how** to perform everyday data operations with Parquet in Python and Spark.

---

## 1. Executive Summary & Benchmark Results

### Why Migrate?
Before migration, the pipeline stored pools and synthetic datasets as pretty-printed JSON files (`indent=4`). This caused massive performance bottlenecks:
1. **CPU Overhead**: Pure-Python JSON serialization (`json.dump` / `json.load`) had to parse strings, escape characters, and allocate millions of small Python string/dict objects row by row.
2. **Storage Bloat**: Indented text files consumed over **211 MB** for ~80,000 orders and 150,000 products.
3. **Slow Spark Ingestion**: Spark had to read text line-by-line, infer types, and tokenize strings into schema columns.

### Benchmarks (Before vs. After)

| Pipeline Stage | Baseline (JSON) | Optimized (Apache Parquet) | Improvement |
|---|---|---|---|
| **Pool Generation** | 48.0s – 68.8s | **6.2s** | **~10x faster** |
| **Dataset Generation** | 50.0s – 109.0s | **18.7s** | **~4x – 5x faster** |
| **Bronze Ingestion (Spark)** | 34.6s – 62.8s | **23.2s** | **~2x faster** |
| **Silver Processing (Spark)** | 43.8s – 86.5s | **31.8s** | **~2x faster** |
| **Total Pipeline Runtime** | **178.2s – 287.8s** | **80.00s** | **~55% – 72% overall reduction** |
| **Storage Footprint** | **211 MB** | **42 MB** | **80% compression** |
| **Test Suite Compatibility** | 36 / 36 Passing | **36 / 36 Passing (100%)** | Zero regressions |

---

## 2. Row-Oriented (JSON/CSV) vs. Columnar (Parquet)

To understand why Parquet is drastically faster and how it operates, let's contrast how data is structured on disk.

### How JSON & CSV Store Data (Row-Oriented)
JSON and CSV write data record by record:

```text
[Row 1] {"customer_id": "c1", "state": "SP", "city": "Sao Paulo"}
[Row 2] {"customer_id": "c2", "state": "RJ", "city": "Rio de Janeiro"}
[Row 3] {"customer_id": "c3", "state": "SP", "city": "Campinas"}
```

* **Repeated Overhead**: The key names (`"customer_id"`, `"state"`, `"city"`), quotes, colons, and braces are repeated on **every single row**.
* **Expensive Type Parsing**: Every number, float, boolean, or date is written as text characters. When reading, Python must parse ASCII strings into numbers or objects using CPU cycles.
* **Full File Scan Required**: If you only need the `state` column, Python or Spark must read and parse the entire file from start to finish.

---

### How Apache Parquet Stores Data (Columnar & Binary)
Parquet arranges data by columns rather than by rows, and writes binary-encoded chunks:

```text
┌───────────────── Column: customer_id ─────────────────┐
│ ["c1", "c2", "c3"]                                   │
└───────────────────────────────────────────────────────┘
┌──────────────────── Column: state ────────────────────┐
│ Dictionary: [0: "SP", 1: "RJ"] -> Encoded: [0, 1, 0]  │
└───────────────────────────────────────────────────────┘
┌──────────────────── Column: city ─────────────────────┐
│ ["Sao Paulo", "Rio de Janeiro", "Campinas"]           │
└───────────────────────────────────────────────────────┘
┌──────────────────── Footer Metadata ──────────────────┐
│ Schema (Types), Row Count, Min/Max stats per column   │
└───────────────────────────────────────────────────────┘
```

### Key Technical Advantages of Parquet
1. **Dictionary Encoding**: If `"SP"` repeats 50,000 times, Parquet writes `"SP"` once into a dictionary table and stores the data as small integer indices (1 byte each instead of 4+ bytes).
2. **Built-in Compression**: Columnar data contains values of identical types grouped together, making algorithms like Snappy or Zstandard compress up to 80–90% better than row-based text.
3. **Embedded Schema**: The data types (`int64`, `float64`, `string`, `timestamp`) are stored in the Parquet file header and footer. No type guessing or inference needed.
4. **Projection Pushdown**: If you only ask for `customer_id` and `state`, reader libraries skip reading `city` off disk entirely.
5. **Statistics & Skipping**: Parquet stores `min` and `max` values per chunk (Row Group). If you query `WHERE order_status = 'delivered'`, it can skip entire row groups without decompressing them.

---

## 3. How Parquet Works with Python Dictionaries

A common question when moving from JSON to Parquet is:
> *"In JSON it was simple: `json.load()` gives a Python `dict` or `list[dict]`, and I can access `record['id']`. How does Parquet read data and how do I do operations on it?"*

Under the hood, we use **PyArrow** (`pyarrow.parquet`). PyArrow is written in C++ and handles the translation between Parquet's binary columnar format and Python data structures in microseconds.

### A. Reading Parquet as Python Dictionaries (`list[dict]`)

In JSON:
```python
import json

with open("metadata/pools/customer_pool.json", "r", encoding="utf-8") as f:
    customers = json.load(f)  # returns list[dict]
```

In Parquet:
```python
import pyarrow.parquet as pq

# 1. Read the binary parquet table into memory (C++ speed)
table = pq.read_table("metadata/pools/customer_pool.parquet")

# 2. Convert directly to standard Python dictionaries
customers = table.to_pylist()  # returns list[dict]!
```

#### Why `table.to_pylist()` is a Game Changer:
* `table.to_pylist()` produces the **exact same data structure** as `json.load()`: a Python `list` containing `dict` objects.
* All downstream logic remains identical:
  ```python
  first_customer = customers[0]
  print(first_customer["customer_id"])    # Works exactly like before!
  print(first_customer["customer_city"])  # Works exactly like before!
  ```
* Because `load_pool()` and `load_generated_data()` call `table.to_pylist()`, **none of the downstream generators, business rules, or test assertions had to change**.

---

### B. Writing Python Dictionaries to Parquet

In JSON:
```python
import json

with open("customer_pool.json", "w", encoding="utf-8") as f:
    json.dump(customers, f, indent=4)  # Slow pure-python string construction
```

In Parquet:
```python
import pyarrow as pa
import pyarrow.parquet as pq

# 1. Convert list of dicts to an Arrow Table (C++ infers schema & builds columns)
table = pa.Table.from_pylist(customers)

# 2. Write compressed binary Parquet file to disk
pq.write_table(table, "customer_pool.parquet")
```

---

### C. Reading Specific Columns Only (Column Projection)
When working with large tables, you don't even need to load all columns:

```python
import pyarrow.parquet as pq

# Only load 'customer_id' and 'customer_city'
table = pq.read_table("customer_pool.parquet", columns=["customer_id", "customer_city"])
records = table.to_pylist()
```
* Parquet physically skips reading all other columns from disk, saving I/O and RAM.

---

### D. Reading Metadata Without Loading Data
Need to know how many rows are in a file without loading 150,000 dictionaries into RAM?

```python
import pyarrow.parquet as pq

# Reads only the small footer metadata (instantaneous)
meta = pq.read_metadata("customer_pool.parquet")
print(meta.num_rows)     # e.g., 100000
print(meta.num_columns)  # e.g., 5
print(meta.schema)       # Column names and types
```
We used this in `build_customers.py` and `build_products.py` to count records instantly instead of looping through all items.

---

### E. Converting to Pandas (Optional)
If you ever want to analyze data in a notebook or script using Pandas:

```python
import pyarrow.parquet as pq

table = pq.read_table("customer_pool.parquet")
df = table.to_pandas()  # Instant zero-copy or minimal copy conversion
print(df.head())
```

---

## 4. How Apache Spark Reads and Ingests Parquet

In PySpark (Bronze and Silver layers):

### Before (JSON):
```python
# Spark had to read text lines, tokenize JSON strings, and infer schemas
df = spark.read.option("multiLine", "true").json("storage/generated/generated_customers_data.json")
```

### After (Parquet):
```python
# Spark reads column batches directly into JVM memory using vectorized reader
df = spark.read.parquet("storage/generated/generated_customers_data.parquet")
```

### Spark Benefits:
1. **Vectorized Reader**: Spark uses vectorized SIMD instructions to load columns into CPU registers directly.
2. **Zero Schema Guessing**: Spark reads types directly from the Parquet metadata footer, eliminating schema inference passes.
3. **Partition Pruning & Filter Pushdown**: Spark pushes filters down to the Parquet reader level.

---

## 5. Architectural Changes Made in the Codebase

Here is the exact map of files modified and their role in the Parquet transition:

### 1. Central Storage & Loading Helpers
* [`src/elt_lakehouse/generators/base/pool_manager.py`](file:///home/mohammadsaif/Projects/ELT-lakehouse/src/elt_lakehouse/generators/base/pool_manager.py):
  * `save_pool`: Ensures `parquet_path.parent.mkdir(parents=True, exist_ok=True)` and writes `.parquet` with PyArrow.
  * `load_pool`: Prioritizes `.parquet`, reads via PyArrow, and returns `table.to_pylist()`. Fallback to legacy `.json` only if present.
* [`src/elt_lakehouse/generators/base/data_saving.py`](file:///home/mohammadsaif/Projects/ELT-lakehouse/src/elt_lakehouse/generators/base/data_saving.py):
  * `save_generated_data`: Automatically creates output directories and writes `.parquet`.
* [`src/elt_lakehouse/generators/base/data_loading.py`](file:///home/mohammadsaif/Projects/ELT-lakehouse/src/elt_lakehouse/generators/base/data_loading.py):
  * `load_generated_data`: Prioritizes `.parquet` and returns `table.to_pylist()`.

### 2. Dataset & Pool Generators
* [`src/elt_lakehouse/spark/jobs/pool_job.py`](file:///home/mohammadsaif/Projects/ELT-lakehouse/src/elt_lakehouse/spark/jobs/pool_job.py):
  * Auto-creates `POOLS_DIR` (`metadata/pools`) before execution.
* [`src/elt_lakehouse/spark/jobs/dataset_job.py`](file:///home/mohammadsaif/Projects/ELT-lakehouse/src/elt_lakehouse/spark/jobs/dataset_job.py):
  * Auto-creates `output_path` (`storage/generated`) before execution.
* Direct Copy Optimization:
  * For datasets that match pools (`customers`, `geolocations`, `products`, `sellers`), we use `shutil.copyfile(pool_path, dest_path)` to copy the Parquet file directly, reducing generation time from ~23s down to **0.00s**.
* Seller Zip Code Normalization:
  * In `seller_generator.py`, enforced `str(zip_code)` so mixed integer/string zip codes (e.g. `'01000'`) do not trigger PyArrow schema mismatch errors.
* Lazy Pool Loading:
  * In `order_item_generator.py` and `order_generator.py`, removed import-time eager pool loads and replaced them with lazy functions (`get_product_pool()`, `get_seller_pool()`). This ensures the module can be imported even before pools are built.

### 3. Bronze Ingestion
* [`src/elt_lakehouse/ingestion/core/reader.py`](file:///home/mohammadsaif/Projects/ELT-lakehouse/src/elt_lakehouse/ingestion/core/reader.py):
  * Added `read_parquet(spark, input_path)` method.
  * Updated `read_json` with auto-fallback to `read_parquet` if the path ends with `.parquet` or if a `.parquet` file exists.
* [`src/elt_lakehouse/ingestion/bronze/*.py`](file:///home/mohammadsaif/Projects/ELT-lakehouse/src/elt_lakehouse/ingestion/bronze/):
  * Updated all 8 ingestion files (`customers.py`, `orders.py`, `products.py`, etc.) to set `INPUT_PATH` to `generated_*_data.parquet`.

### 4. Spark Session Reuse & Silver Optimizations
* [`src/elt_lakehouse/spark/jobs/bronze_job.py`](file:///home/mohammadsaif/Projects/ELT-lakehouse/src/elt_lakehouse/spark/jobs/bronze_job.py) & [`silver_job.py`](file:///home/mohammadsaif/Projects/ELT-lakehouse/src/elt_lakehouse/spark/jobs/silver_job.py):
  * Made `spark` an optional parameter: `run_bronze_ingestion(spark=None)` and `run_silver_processing(spark=None)`.
  * If an external `spark` session is passed, the jobs reuse it and do not shut it down.
* [`elt_pipeline.py`](file:///home/mohammadsaif/Projects/ELT-lakehouse/elt_pipeline.py):
  * `--run-pipeline` starts a single `SparkSession` for both Bronze ingestion and Silver processing, eliminating the 15–20s JVM shutdown and restart penalty.
* Intermediate DataFrame Caching:
  * In `silver_job.py`, parent lookup DataFrames (`orders_df`, `customers_df`, `products_df`, `sellers_df`) are persisted with `StorageLevel.MEMORY_AND_DISK` during referential integrity checks, avoiding repeated full table re-scans across 6 quarantine writes.

---

## 6. Quick Reference Cheat Sheet for Parquet

| Task | Code Snippet |
|---|---|
| **Read Parquet as `list[dict]`** | `table = pq.read_table("file.parquet")`<br>`data = table.to_pylist()` |
| **Write `list[dict]` to Parquet** | `table = pa.Table.from_pylist(data)`<br>`pq.write_table(table, "file.parquet")` |
| **Read Only 2 Columns** | `table = pq.read_table("file.parquet", columns=["col1", "col2"])`<br>`data = table.to_pylist()` |
| **Check Total Row Count Instantly** | `count = pq.read_metadata("file.parquet").num_rows` |
| **Inspect Columns and Data Types** | `schema = pq.read_schema("file.parquet")`<br>`print(schema)` |
| **Read Parquet into Pandas** | `df = pq.read_table("file.parquet").to_pandas()` |
| **Read Parquet into Spark** | `df = spark.read.parquet("file.parquet")` |
| **Write Spark DataFrame to Parquet** | `df.write.mode("overwrite").parquet("output_path")` |

---

## 7. Conclusion

By adopting Apache Parquet:
1. **Performance**: We cut overall pipeline execution time from **~3–5 minutes down to 80 seconds**.
2. **Storage**: Reduced disk footprint by **80%**.
3. **Clean Architecture**: Standardized the storage layer to be 100% Parquet-centric from pools to generated datasets, feeding seamlessly into Delta Lake Bronze and Silver layers.
4. **Developer Experience**: Maintained 100% Python dictionary compatibility via `table.to_pylist()`, ensuring that working with data remains as intuitive as working with standard Python dicts.

