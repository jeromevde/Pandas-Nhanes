#!/usr/bin/env python3
"""
build_corr_lookup.py
────────────────────
Pre-compute top-K significantly correlated variables for every NHANES numeric
variable in every cached cohort.  Output: corr_lookup.json (placed in the repo
root so GitHub Pages can serve it alongside index.html).

Data format (compact JSON):
  {
    "2009-2010": {
      "RIDAGEYR": [["BMXBMI", 0.34, 8234], ["LBXTST", -0.21, 5023], ...],
      ...
    },
    ...
  }
  Each inner list entry: [var_name, pearson_r (rounded 3 dp), n_shared_obs]
  Only significant pairs (p < P_THRESHOLD) are included.
  Entries are sorted by |r| descending.
"""

import os, glob, json
import numpy as np
import pandas as pd
from scipy import stats

# ── Configuration ─────────────────────────────────────────────────────────────
COHORTS = {
    "2009-2010": "F",
    "2011-2012": "G",
    "2013-2014": "H",
    "2015-2016": "I",
    "2017-2018": "J",
}

CACHE_DIR     = os.path.expanduser("~/.cache/pandas_nhanes")
OUTPUT        = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corr_lookup.json")

TOP_K         = 30     # max correlates stored per variable
MIN_VALID_COL = 100    # column excluded if fewer non-null values
MIN_SHARED    = 50     # pair excluded if fewer shared non-null rows
P_THRESHOLD   = 0.05   # significance cutoff


# ── Data loading ───────────────────────────────────────────────────────────────
def load_merged(suffix: str) -> pd.DataFrame | None:
    pattern = os.path.join(CACHE_DIR, f"*_{suffix}.xpt")
    files   = glob.glob(pattern)
    if not files:
        return None
    print(f"  {len(files)} XPT files found for suffix _{suffix}")

    tables = []
    for f in sorted(files):
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

    dup_cols = [c for c in merged.columns if c.endswith("_dup")]
    merged.drop(columns=dup_cols, inplace=True)
    return merged


# ── Correlation engine ─────────────────────────────────────────────────────────
def compute_top_k(df: pd.DataFrame) -> dict[str, list]:
    """
    For every eligible numeric column return the TOP_K most correlated other
    columns that are statistically significant.
    """
    # Select numeric columns with enough data; drop SEQN
    num = df.select_dtypes(include=[np.number])
    valid_counts = num.notna().sum()
    cols = (valid_counts[valid_counts >= MIN_VALID_COL]
            .drop("SEQN", errors="ignore")
            .index.tolist())

    print(f"  Eligible columns: {len(cols)}")
    if len(cols) < 2:
        return {}

    sub = num[cols]

    # ── Shared non-null counts (vectorised) ───────────────────────────────────
    print("  Computing shared-n matrix …")
    notna     = sub.notna().astype(np.int16)
    n_mat     = (notna.values.T @ notna.values).astype(np.float32)   # (C × C)

    # ── Pearson r (pandas vectorised, pairwise deletion) ─────────────────────
    print("  Computing correlation matrix …")
    r_mat = sub.corr(method="pearson", min_periods=MIN_SHARED).values.astype(np.float32)

    # ── P-values analytically: t = r·√(n−2) / √(1−r²) ───────────────────────
    print("  Computing p-values …")
    n = n_mat
    r = r_mat
    with np.errstate(divide="ignore", invalid="ignore"):
        t_stat = r * np.sqrt(np.maximum(n - 2, 0)) / np.sqrt(np.maximum(1.0 - r**2, 1e-15))
    # Two-sided p-value; cap df at 1 to avoid domain errors
    p_mat = 2.0 * stats.t.sf(np.abs(t_stat), df=np.maximum(n - 2, 1)).astype(np.float32)

    # ── Build per-variable top-K ───────────────────────────────────────────────
    print("  Building per-variable top-K lookup …")
    result: dict[str, list] = {}
    for i, col in enumerate(cols):
        pairs: list[tuple[str, float, int]] = []
        for j in range(len(cols)):
            if i == j:
                continue
            ri = float(r[i, j])
            pi = float(p_mat[i, j])
            ni = int(n[i, j])
            if np.isnan(ri) or np.isnan(pi):
                continue
            if pi >= P_THRESHOLD:
                continue
            if ni < MIN_SHARED:
                continue
            pairs.append((cols[j], round(ri, 3), ni))

        pairs.sort(key=lambda x: -abs(x[1]))
        if pairs:
            result[col] = [[v, r_, n_] for v, r_, n_ in pairs[:TOP_K]]

    return result


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    lookup: dict[str, dict] = {}

    for cycle, suffix in COHORTS.items():
        print(f"\n{'━' * 56}")
        print(f"  Cohort {cycle}  (suffix _{suffix})")
        print(f"{'━' * 56}")

        df = load_merged(suffix)
        if df is None:
            print("  No cached data – skipping.")
            continue
        print(f"  Merged → {len(df):,} rows × {len(df.columns):,} columns")

        corr_data = compute_top_k(df)
        print(f"  Variables with at least one significant correlate: {len(corr_data):,}")
        lookup[cycle] = corr_data

    print(f"\n{'━' * 56}")
    print(f"Writing {OUTPUT} …")
    with open(OUTPUT, "w") as fh:
        json.dump(lookup, fh, separators=(",", ":"))

    size_mb = os.path.getsize(OUTPUT) / 1e6
    total_vars = sum(len(v) for v in lookup.values())
    print(f"Done! {size_mb:.1f} MB  ·  {total_vars:,} variable entries across {len(lookup)} cohorts")


if __name__ == "__main__":
    main()
