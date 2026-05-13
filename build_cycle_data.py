#!/usr/bin/env python3
"""
build_cycle_data.py
───────────────────
1. Read the NHANES variables CSV to discover all XPT dataset links per cycle.
2. Download any missing XPT files to the local cache.
3. For each cycle, merge all cached XPT files, sample rows, keep numeric
   columns, and write a compact JSON file for browser-side correlation
   computation and scatter plots.

Output (in data/):
  manifest.json          – list of available cycles + column counts + var list
  2009-2010.json         – sampled column data for that cohort
  2011-2012.json         – …
"""

import os, json, gzip
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
import numpy as np
import pandas as pd
import requests

# ── Configuration ─────────────────────────────────────────────────────────────
# Standard 2-year cycles with their XPT suffix (for glob-based discovery)
# Plus CSV-based dataset lookup for all cycles
CYCLES = [
    "2001-2002",
    "2003-2004",
    "2005-2006",
    "2007-2008",
    "2009-2010",
    "2011-2012",
    "2013-2014",
    "2015-2016",
    "2017-2018",
    "2021-2023",
]

CSV_PATH      = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "pandas_nhanes", "nhanes_variables.csv")
CACHE_DIR     = os.path.expanduser("~/.cache/pandas_nhanes")
OUTPUT_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SAMPLE_ROWS   = 1500
MIN_VALID_COL = 100    # column must have ≥ this many non-null values to keep
ROUND_DP      = 2      # decimal places for stored numbers
DL_WORKERS    = 8      # parallel download threads


# ── Download helpers ──────────────────────────────────────────────────────────
def _download_one(dataset: str, url: str) -> str:
    """Download a single XPT file to cache.  Returns status string."""
    cache_path = os.path.join(CACHE_DIR, f"{dataset}.xpt")
    if os.path.exists(cache_path):
        return f"  ✓ {dataset} (cached)"
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        with open(cache_path, "wb") as f:
            f.write(r.content)
        return f"  ↓ {dataset} ({len(r.content)/1e6:.1f} MB)"
    except Exception as e:
        return f"  ✗ {dataset}: {e}"


def download_cycle_xpts(cycle: str, csv_df: pd.DataFrame):
    """Download all missing XPT files for a cycle, in parallel."""
    sub = csv_df[csv_df["cycle name"] == cycle]
    links = sub[["dataset", "dataset link"]].drop_duplicates().dropna()
    if links.empty:
        print("  No dataset links found in CSV.")
        return

    missing = [(r["dataset"], r["dataset link"]) for _, r in links.iterrows()
               if not os.path.exists(os.path.join(CACHE_DIR, f"{r['dataset']}.xpt"))]

    if not missing:
        print(f"  All {len(links)} XPT files already cached.")
        return

    print(f"  Downloading {len(missing)} / {len(links)} missing XPT files …")
    with ThreadPoolExecutor(max_workers=DL_WORKERS) as pool:
        futs = {pool.submit(_download_one, ds, url): ds for ds, url in missing}
        done = 0
        for fut in as_completed(futs):
            done += 1
            msg = fut.result()
            # Print every 20th or failed ones
            if done % 20 == 0 or "✗" in msg:
                print(msg)
        print(f"  Download complete: {done} files processed.")


# ── Load & merge ──────────────────────────────────────────────────────────────
def load_merged_from_csv(cycle: str, csv_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Load all cached XPT files for a cycle (discovered via CSV) and merge."""
    sub = csv_df[csv_df["cycle name"] == cycle]
    dataset_names = sorted(sub["dataset"].dropna().unique())
    if not dataset_names:
        return None

    tables = []
    n_skipped_dup = 0
    n_skipped_err = 0
    n_missing = 0
    for name in dataset_names:
        path = os.path.join(CACHE_DIR, f"{name}.xpt")
        if not os.path.exists(path):
            n_missing += 1
            continue
        try:
            df = pd.read_sas(path)
            if "SEQN" not in df.columns:
                continue
            df = df.set_index("SEQN")
            if df.index.duplicated().any():
                n_skipped_dup += 1
                continue
            tables.append(df)
        except Exception:
            n_skipped_err += 1

    print(f"  Loaded {len(tables)} datasets ({n_skipped_dup} multi-row, {n_skipped_err} errors, {n_missing} missing)")
    if not tables:
        return None

    merged = pd.concat(tables, axis=1, join="outer")
    merged = merged.loc[:, ~merged.columns.duplicated()]
    merged.reset_index(inplace=True)
    return merged


def classify_columns(df: pd.DataFrame) -> dict:
    """Return {col: 'num'|'cat'} for all eligible numeric columns.
    Columns with ≤ 12 unique non-null values are treated as categorical codes
    (e.g. RIAGENDR, race/ethnicity, education level, yes/no variables)."""
    num = df.select_dtypes(include=[np.number])
    counts = num.notna().sum()
    eligible = (counts[counts >= MIN_VALID_COL]
                .drop("SEQN", errors="ignore"))
    result = {}
    for c in eligible.index:
        col = df[c].dropna()
        if col.std() == 0:
            continue
        result[c] = 'cat' if col.nunique() <= 12 else 'num'
    return result


def select_numeric(df: pd.DataFrame) -> list[str]:
    """Backward-compat wrapper – returns all eligible column names."""
    return list(classify_columns(df).keys())


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    manifest = []

    # Load CSV for download discovery
    csv_df = pd.read_csv(CSV_PATH)

    for cycle in CYCLES:
        print(f"\n{'━' * 56}")
        print(f"  Cohort {cycle}")
        print(f"{'━' * 56}")

        # Step 1: download any missing XPT files for this cycle
        download_cycle_xpts(cycle, csv_df)

        # Step 2: load & merge
        df = load_merged_from_csv(cycle, csv_df)
        if df is None:
            print("  No cached data – skipping.")
            continue

        col_types = classify_columns(df)
        cols = list(col_types.keys())
        n_total = len(df)
        n_sample = min(SAMPLE_ROWS, n_total)
        n_num = sum(1 for t in col_types.values() if t == 'num')
        n_cat = sum(1 for t in col_types.values() if t == 'cat')
        print(f"  Merged → {n_total:,} rows × {len(df.columns):,} columns")
        print(f"  Eligible columns: {len(cols)} ({n_num} numeric, {n_cat} categorical)")

        if len(cols) < 2:
            continue

        sample = df[cols].sample(n=n_sample, random_state=42)

        col_data = {}
        for c in cols:
            vals = sample[c].tolist()
            if col_types[c] == 'cat':
                col_data[c] = [
                    None if (v is None or (isinstance(v, float) and np.isnan(v)))
                    else int(v)
                    for v in vals
                ]
            else:
                col_data[c] = [
                    None if (v is None or (isinstance(v, float) and np.isnan(v)))
                    else round(float(v), ROUND_DP)
                    for v in vals
                ]

        payload = {
            "cycle":     cycle,
            "n_total":   n_total,
            "n_sample":  n_sample,
            "cols":      cols,
            "col_types": col_types,
            "data":      col_data,
        }

        outpath = os.path.join(OUTPUT_DIR, f"{cycle}.json")
        raw = json.dumps(payload, separators=(",", ":"))
        with open(outpath, "w") as fh:
            fh.write(raw)

        raw_mb = len(raw) / 1e6
        gz_mb  = len(gzip.compress(raw.encode())) / 1e6
        print(f"  Written → {outpath}")
        print(f"  JSON = {raw_mb:.1f} MB  |  gzip = {gz_mb:.1f} MB")

        manifest.append({
            "cycle":    cycle,
            "n_cols":   len(cols),
            "n_total":  n_total,
            "n_sample": n_sample,
            "vars":     cols,          # ← variable list for instant JS lookup
        })

    mpath = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(mpath, "w") as fh:
        json.dump(manifest, fh, separators=(",", ":"))
    print(f"\n{'━' * 56}")
    print(f"Manifest → {mpath}  ({len(manifest)} cycles)")

    total_gz = sum(
        len(gzip.compress(
            open(os.path.join(OUTPUT_DIR, f"{m['cycle']}.json"), "rb").read()
        )) for m in manifest
    ) / 1e6
    print(f"Total gzip size: {total_gz:.1f} MB")
    print("Done!")


if __name__ == "__main__":
    main()
