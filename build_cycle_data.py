#!/usr/bin/env python3
"""
build_cycle_data.py
───────────────────
For each cached NHANES cohort, sample 3 000 rows from the merged numeric
columns and write a compact JSON file that the browser can use to compute
Pearson correlations and scatter plots entirely on the fly.

Output (in data/):
  manifest.json          - list of available cycles + column counts
  2009-2010.json         - sampled column data for that cohort
  2011-2012.json         - …
  …
"""

import os, glob, json, gzip
import numpy as np
import pandas as pd

# ── Configuration ─────────────────────────────────────────────────────────────
COHORTS = {
    "2009-2010": "F",
    "2011-2012": "G",
    "2013-2014": "H",
    "2015-2016": "I",
    "2017-2018": "J",
}

CACHE_DIR     = os.path.expanduser("~/.cache/pandas_nhanes")
OUTPUT_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SAMPLE_ROWS   = 3000
MIN_VALID_COL = 100    # column must have ≥ this many non-null values to keep
ROUND_DP      = 2      # decimal places for stored numbers


# ── Helpers ───────────────────────────────────────────────────────────────────
def load_merged(suffix: str) -> pd.DataFrame | None:
    pattern = os.path.join(CACHE_DIR, f"*_{suffix}.xpt")
    files   = sorted(glob.glob(pattern))
    if not files:
        return None
    print(f"  {len(files)} XPT files found for suffix _{suffix}")

    tables = []
    for f in files:
        try:
            df = pd.read_sas(f)
            if "SEQN" in df.columns:
                tables.append(df)
        except Exception as e:
            print(f"    Skip {os.path.basename(f)}: {e}")

    if not tables:
        return None

    merged = tables[0]
    for other in tables[1:]:
        merged = merged.merge(other, on="SEQN", how="outer", suffixes=("", "_dup"))
    dup = [c for c in merged.columns if c.endswith("_dup")]
    merged.drop(columns=dup, inplace=True)
    return merged


def select_numeric(df: pd.DataFrame) -> list[str]:
    num = df.select_dtypes(include=[np.number])
    counts = num.notna().sum()
    cols = (counts[counts >= MIN_VALID_COL]
            .drop("SEQN", errors="ignore")
            .index.tolist())
    return cols


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    manifest = []

    for cycle, suffix in COHORTS.items():
        print(f"\n{'━' * 56}")
        print(f"  Cohort {cycle}  (suffix _{suffix})")
        print(f"{'━' * 56}")

        df = load_merged(suffix)
        if df is None:
            print("  No cached data – skipping.")
            continue

        cols = select_numeric(df)
        n_total = len(df)
        n_sample = min(SAMPLE_ROWS, n_total)
        print(f"  Merged → {n_total:,} rows × {len(df.columns):,} columns")
        print(f"  Eligible numeric columns: {len(cols)}")

        if len(cols) < 2:
            continue

        sample = df[cols].sample(n=n_sample, random_state=42)

        col_data = {}
        for c in cols:
            vals = sample[c].tolist()
            col_data[c] = [
                None if (v is None or (isinstance(v, float) and np.isnan(v)))
                else round(float(v), ROUND_DP)
                for v in vals
            ]

        payload = {
            "cycle":    cycle,
            "n_total":  n_total,
            "n_sample": n_sample,
            "cols":     cols,
            "data":     col_data,
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
