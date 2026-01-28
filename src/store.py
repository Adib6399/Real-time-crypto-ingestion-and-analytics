import os
import polars as pl
import time

# Determine absolute path of project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")

os.makedirs(DATA_DIR, exist_ok=True)

def write_parquet_batch(df: pl.DataFrame, prefix="trades"):
    ts = int(time.time())
    filename = os.path.join(DATA_DIR, f"{prefix}_{ts}.parquet")
    df.write_parquet(filename)
    print(f"Wrote {len(df)} rows → {filename}")

