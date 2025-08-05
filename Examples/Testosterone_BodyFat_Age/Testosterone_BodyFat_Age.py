#!/usr/bin/env python3
"""
Testosterone vs. Body Fat by Age Buckets (NHANES 1999-2000)

This script analyzes the relationship between estimated percent body fat and testosterone levels
across age buckets, using NHANES 1999-2000 data. All data is plotted on a single figure.
"""

import pandas as pd
import numpy as np
from scipy.ndimage import gaussian_filter1d
import plotly.graph_objects as go
from pandas_nhanes import get_dataset
body
# --- Constants ---

CYCLE = "1999-2000"
BODYFAT_VAR = "BIDPFAT"  # Estimated percent body fat
BODYFAT_FILE = "BIX"
TESTOSTERONE_VAR = "SSTESTO"  # Serum testosterone (ng/dL)
TESTOSTERONE_FILE = "LAB13"
AGE_VAR = "RIDAGEYR"
AGE_FILE = "DEMO"

# --- Data Loading ---
def load_and_merge_data():
    """Loads and merges body fat, testosterone, and demographic data from NHANES 1999-2000."""
    # Body fat
    bodyfat = get_dataset(f"{BODYFAT_FILE}_A")[["SEQN", BODYFAT_VAR]]
    # Testosterone
    testo = get_dataset(f"{TESTOSTERONE_FILE}_A")[["SEQN", TESTOSTERONE_VAR]]
    # Demographics (age)
    demo = get_dataset(f"{AGE_FILE}_A")[["SEQN", AGE_VAR]].rename(columns={AGE_VAR: "Age (years)"})
    df = pd.merge(bodyfat, testo, on="SEQN", how="inner")
    df = pd.merge(df, demo, on="SEQN", how="inner")
    return df

# --- Data Cleaning ---
def clean_data(df):
    """Removes rows with missing or implausible data."""
    df = df.dropna(subset=[BODYFAT_VAR, TESTOSTERONE_VAR, "Age (years)"]).copy()
    # Remove outliers: restrict to plausible human ranges
    df = df[(df[BODYFAT_VAR] > 2) & (df[BODYFAT_VAR] < 60)]
    df = df[(df[TESTOSTERONE_VAR] > 10) & (df[TESTOSTERONE_VAR] < 2000)]
    df = df[(df["Age (years)"] >= 18) & (df["Age (years)"] <= 80)]
    return df

# --- Analysis ---
def compute_binned_stats(df, n_bins=8):
    """Bins by age and computes mean/SD for each bin."""
    bins = np.linspace(df["Age (years)"].min(), df["Age (years)"].max(), n_bins+1)
    df["age_bin"] = pd.cut(df["Age (years)"], bins, include_lowest=True)
    stats = df.groupby("age_bin").agg({
        BODYFAT_VAR: ["mean", "std"],
        TESTOSTERONE_VAR: ["mean", "std"],
        "Age (years)": "mean"
    }).reset_index(drop=True)
    stats.columns = ["_".join(col).strip("_") for col in stats.columns.values]
    return stats

# --- Plotting ---
def create_plot(df, stats):
    """Creates a single figure with scatter and binned means/SDs."""
    fig = go.Figure()
    # Raw data
    fig.add_trace(go.Scatter(
        x=df[BODYFAT_VAR], y=df[TESTOSTERONE_VAR],
        mode="markers", marker=dict(size=4, color=df["Age (years)"], colorscale="Viridis", colorbar=dict(title="Age")),
        name="Individuals", opacity=0.4
    ))
    # Binned means
    fig.add_trace(go.Scatter(
        x=stats[f"{BODYFAT_VAR}_mean"], y=stats[f"{TESTOSTERONE_VAR}_mean"],
        mode="lines+markers", line=dict(color="black", width=3), marker=dict(size=10, color="red"),
        name="Mean by Age Bin"
    ))
    # Error bars (SD)
    fig.add_trace(go.Scatter(
        x=stats[f"{BODYFAT_VAR}_mean"],
        y=stats[f"{TESTOSTERONE_VAR}_mean"] + stats[f"{TESTOSTERONE_VAR}_std"],
        mode="lines", line=dict(color="rgba(0,0,0,0.2)", dash="dot"), showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=stats[f"{BODYFAT_VAR}_mean"],
        y=stats[f"{TESTOSTERONE_VAR}_mean"] - stats[f"{TESTOSTERONE_VAR}_std"],
        mode="lines", line=dict(color="rgba(0,0,0,0.2)", dash="dot"), showlegend=False
    ))
    fig.update_layout(
        title="Testosterone vs. Body Fat by Age Buckets (NHANES 1999-2000)",
        xaxis_title="Estimated Percent Body Fat (%)",
        yaxis_title="Serum Testosterone (ng/dL)",
        template="plotly_white",
        width=900, height=600
    )
    return fig

# --- Main ---
def main():
    df = load_and_merge_data()
    df = clean_data(df)
    stats = compute_binned_stats(df)
    print(f"N subjects: {len(df)}")
    print(f"Age range: {df['Age (years)'].min()} - {df['Age (years)'].max()}")
    fig = create_plot(df, stats)
    fig.write_html("Testosterone_BodyFat_Age.html")
    fig.write_image("Testosterone_BodyFat_Age.png", scale=2)

if __name__ == "__main__":
    main()