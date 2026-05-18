#!/usr/bin/env python3
"""
build_cycle_data.py
───────────────────
For each NHANES cycle:

1. Download missing XPT files into ~/.cache/pandas_nhanes/
2. Merge all datasets on SEQN
3. Classify columns as numeric ('num') or categorical ('cat', ≤12 unique values)
4. Write one output file per cycle into data/:

   <cycle>.scatter.json
       Sampled column arrays (SCATTER_ROWS rows) used by the browser for:
         - On-the-fly correlation computation when a user picks a variable
         - Scatter plots / box plots / heatmaps on pair click
       {cycle, n_total, n_sample, cols, col_types, data: {col: [val, ...]}}
       Typical size: ~3 MB raw, ~700 KB gzip per cycle

5. Write data/manifest.json
       [{cycle, n_cols, n_total, n_sample, vars, col_types}]
       Tells the browser which cycles exist and which variables are available.

JS-side computation (in index.html):
  - Pearson r   for num×num pairs
  - eta (η)     for num×cat or cat×num pairs  (correlation ratio)
  - Cramér's V  for cat×cat pairs
  All N*(N-1)/2 pairs computed in < 200 ms on 3000 rows × 300 cols.
  Results sorted by |assoc| descending — no significance threshold applied.
"""

import os, json, gzip, math
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, List
import numpy as np
import pandas as pd
import requests

# ── Configuration ─────────────────────────────────────────────────────────────
CYCLES = [
    "2001-2002", "2003-2004", "2005-2006", "2007-2008",
    "2009-2010", "2011-2012", "2013-2014", "2015-2016",
    "2017-2018", "2021-2023",
]

CSV_PATH      = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "pandas_nhanes", "nhanes_variables.csv")
CACHE_DIR     = os.path.expanduser("~/.cache/pandas_nhanes")
OUTPUT_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

MIN_VALID_COL = 100    # column needs ≥ this many non-null values to be included
CAT_MAX_UNIQ  = 12     # ≤ this many unique values → treat column as categorical
SCATTER_ROWS  = 5000   # rows sampled per cycle (higher = more reliable JS stats)
DL_WORKERS    = 8



# ── Download ──────────────────────────────────────────────────────────────────
def _download_one(dataset: str, url: str) -> str:
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
    sub = csv_df[csv_df["cycle name"] == cycle]
    links = sub[["dataset", "dataset link"]].drop_duplicates().dropna()
    if links.empty:
        print("  No dataset links found in CSV.")
        return
    missing = [(row["dataset"], row["dataset link"]) for _, row in links.iterrows()
               if not os.path.exists(os.path.join(CACHE_DIR, f"{row['dataset']}.xpt"))]
    if not missing:
        print(f"  All {len(links)} XPT files already cached.")
        return
    print(f"  Downloading {len(missing)}/{len(links)} missing XPT files …")
    with ThreadPoolExecutor(max_workers=DL_WORKERS) as pool:
        futs = {pool.submit(_download_one, ds, url): ds for ds, url in missing}
        done = 0
        for fut in as_completed(futs):
            done += 1
            msg = fut.result()
            if done % 20 == 0 or "✗" in msg:
                print(msg)
    print(f"  {done} files processed.")


# ── Load & merge ──────────────────────────────────────────────────────────────
def load_merged(cycle: str, csv_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    sub = csv_df[csv_df["cycle name"] == cycle]
    names = sorted(sub["dataset"].dropna().unique())
    tables, n_dup, n_err, n_miss = [], 0, 0, 0
    for name in names:
        path = os.path.join(CACHE_DIR, f"{name}.xpt")
        if not os.path.exists(path):
            n_miss += 1; continue
        try:
            df = pd.read_sas(path)
            if "SEQN" not in df.columns:
                continue
            df = df.set_index("SEQN")
            if df.index.duplicated().any():
                n_dup += 1; continue
            tables.append(df)
        except Exception:
            n_err += 1
    print(f"  Loaded {len(tables)} datasets  "
          f"({n_dup} dup-key, {n_err} errors, {n_miss} missing)")
    if not tables:
        return None
    merged = pd.concat(tables, axis=1, join="outer")
    merged = merged.loc[:, ~merged.columns.duplicated()]
    merged.reset_index(inplace=True)
    return merged


# ── Column classification ──────────────────────────────────────────────────────
def classify_columns(df: pd.DataFrame) -> Dict[str, str]:
    """Return {col: 'num'|'cat'} for every eligible column."""
    num = df.select_dtypes(include=[np.number])
    counts = num.notna().sum()
    eligible = counts[counts >= MIN_VALID_COL].drop("SEQN", errors="ignore")
    result: Dict[str, str] = {}
    for c in eligible.index:
        col = df[c].dropna()
        if col.std() == 0:
            continue
        result[c] = "cat" if col.nunique() <= CAT_MAX_UNIQ else "num"
    return result


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    manifest = []

    csv_df = pd.read_csv(CSV_PATH)

    for cycle in CYCLES:
        print(f"\n{'━'*56}\n  {cycle}\n{'━'*56}")

        download_cycle_xpts(cycle, csv_df)

        df = load_merged(cycle, csv_df)
        if df is None:
            print("  No data – skipping.")
            continue

        col_types = classify_columns(df)
        cols = list(col_types.keys())
        n_total = len(df)
        n_sample = min(SCATTER_ROWS, n_total)
        n_num = sum(1 for t in col_types.values() if t == "num")
        n_cat = sum(1 for t in col_types.values() if t == "cat")
        print(f"  {n_total:,} respondents · {len(cols)} cols ({n_num} num, {n_cat} cat)")

        if len(cols) < 2:
            continue

        sample = df[cols].sample(n=n_sample, random_state=42)
        col_data: Dict[str, list] = {}
        for c in cols:
            vals = sample[c].tolist()
            if col_types[c] == "cat":
                col_data[c] = [
                    None if (v is None or (isinstance(v, float) and math.isnan(v)))
                    else int(v) for v in vals
                ]
            else:
                col_data[c] = [
                    None if (v is None or (isinstance(v, float) and math.isnan(v)))
                    else round(float(v), 2) for v in vals
                ]

        payload = {
            "cycle":     cycle,
            "n_total":   n_total,
            "n_sample":  n_sample,
            "cols":      cols,
            "col_types": col_types,
            "data":      col_data,
        }

        out_path = os.path.join(OUTPUT_DIR, f"{cycle}.scatter.json")
        raw = json.dumps(payload, separators=(",", ":"))
        with open(out_path, "w") as fh:
            fh.write(raw)
        gz = len(gzip.compress(raw.encode()))
        print(f"  → {out_path}")
        print(f"     {len(raw)/1e6:.1f} MB raw  |  {gz/1e6:.2f} MB gzip")

        manifest.append({
            "cycle":     cycle,
            "n_cols":    len(cols),
            "n_total":   n_total,
            "n_sample":  n_sample,
            "vars":      cols,
            "col_types": col_types,
        })

    mpath = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(mpath, "w") as fh:
        json.dump(manifest, fh, separators=(",", ":"))

    total_raw = sum(
        os.path.getsize(os.path.join(OUTPUT_DIR, f"{m['cycle']}.scatter.json"))
        for m in manifest
        if os.path.exists(os.path.join(OUTPUT_DIR, f"{m['cycle']}.scatter.json"))
    )
    total_gz = sum(
        len(gzip.compress(open(os.path.join(OUTPUT_DIR, f"{m['cycle']}.scatter.json"), "rb").read()))
        for m in manifest
        if os.path.exists(os.path.join(OUTPUT_DIR, f"{m['cycle']}.scatter.json"))
    )
    print(f"\n{'━'*56}")
    print(f"Manifest → {mpath}  ({len(manifest)} cycles)")
    print(f"Total: {total_raw/1e6:.0f} MB raw  |  {total_gz/1e6:.0f} MB gzip")
    print("Done!")


if __name__ == "__main__":
    main()
