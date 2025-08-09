#!/usr/bin/env python3
"""
Comprehensive Whole-Body Bone Mineral Density (BMD) Analysis using NHANES 2011-2012 data.

This script analyzes the distribution of BMD across various body parts measured by DEXA scans,
including the head, arms, legs, ribs, spine, pelvis, trunk, and total body. It visualizes
the relationship between age, gender, and BMD for each body part.
"""

import pandas as pd
import numpy as np
try:
    from scipy.stats import zscore as _scipy_zscore  # type: ignore
except Exception:  # SciPy optional
    _scipy_zscore = None
try:
    from scipy.ndimage import gaussian_filter1d as _scipy_gaussian_filter1d  # type: ignore
except Exception:  # SciPy optional
    _scipy_gaussian_filter1d = None
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pandas_nhanes import get_cycle_variables
from pathlib import Path

# --- Constants ---

BMD_COLS_DICT = {
    "DXXHEBMD": "Head BMD (g/cm²)",
    "DXXLABMD": "Left Arm BMD (g/cm²)",
    "DXXRABMD": "Right Arm BMD (g/cm²)",
    "DXXLLBMD": "Left Leg BMD (g/cm²)",
    "DXXRLBMD": "Right Leg BMD (g/cm²)",
    "DXXLRBMD": "Left Ribs BMD (g/cm²)",
    "DXXRRBMD": "Right Ribs BMD (g/cm²)",
    "DXXLSBMD": "Lumbar Spine BMD (g/cm²)",
    "DXXTSBMD": "Thoracic Spine BMD (g/cm²)",
    "DXXPEBMD": "Pelvis BMD (g/cm²)",
    "DXDTRBMD": "Trunk BMD (g/cm²)",
    "DXDSTBMD": "Subtotal BMD (g/cm²)",
    "DXDTOBMD": "Total Body BMD (g/cm²)"
}

MEASUREMENTS_ORDERED = [
    ("Head BMD (g/cm²)", "Head"),
    ("Left Arm BMD (g/cm²)", "Left Arm"),
    ("Right Arm BMD (g/cm²)", "Right Arm"),
    ("Left Leg BMD (g/cm²)", "Left Leg"),
    ("Right Leg BMD (g/cm²)", "Right Leg"),
    ("Left Ribs BMD (g/cm²)", "Left Ribs"),
    ("Right Ribs BMD (g/cm²)", "Right Ribs"),
    ("Lumbar Spine BMD (g/cm²)", "Lumbar Spine"),
    ("Thoracic Spine BMD (g/cm²)", "Thoracic Spine"),
    ("Pelvis BMD (g/cm²)", "Pelvis"),
    ("Trunk BMD (g/cm²)", "Trunk"),
    ("Subtotal BMD (g/cm²)", "Subtotal"),
    ("Total Body BMD (g/cm²)", "Total Body")
]

COLORS = {"Male": "#ff7f0e", "Female": "#1f77b4"}
SUBPLOT_ROWS = 7
SUBPLOT_COLS = 2

# --- Data Loading and Preprocessing ---

# --- Helpers (SciPy fallbacks and utilities) ---

def _safe_zscore(x: np.ndarray) -> np.ndarray:
    """Return z-score; use SciPy if available, else NumPy fallback.
    x: 1D float array.
    """
    if _scipy_zscore is not None:
        try:
            return _scipy_zscore(x, nan_policy='omit')
        except TypeError:
            # Older SciPy without nan_policy
            m = np.nanmean(x)
            s = np.nanstd(x)
            return (x - m) / (s if s > 0 else 1.0)
    m = np.nanmean(x)
    s = np.nanstd(x)
    return (x - m) / (s if s > 0 else 1.0)

def _gaussian1d(arr: np.ndarray, sigma: float) -> np.ndarray:
    """Gaussian smooth 1D array; use SciPy if available, else NumPy kernel."""
    if _scipy_gaussian_filter1d is not None:
        return _scipy_gaussian_filter1d(arr, sigma=sigma, mode='nearest')
    # Build a simple Gaussian kernel
    radius = max(1, int(3 * sigma))
    x = np.arange(-radius, radius + 1)
    kernel = np.exp(-(x ** 2) / (2 * sigma ** 2))
    kernel /= kernel.sum()
    # Pad with edge values and convolve
    pad_left = arr[0]
    pad_right = arr[-1]
    padded = np.concatenate([np.full(radius, pad_left), arr, np.full(radius, pad_right)])
    smoothed = np.convolve(padded, kernel, mode='valid')
    return smoothed

def _hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def load_and_merge_data():
    """Loads and merges BMD and demographic data from NHANES."""
    # 1) Load all BMD variables via the API (no API changes)
    bmd_vars = list(BMD_COLS_DICT.keys())
    bmd_df = get_cycle_variables("2011-2012", *bmd_vars)
    # Rename BMD columns
    bmd_rename = {k: v for k, v in BMD_COLS_DICT.items() if k in bmd_df.columns}
    bmd_df = bmd_df.rename(columns=bmd_rename)
    # 2) Load demographics (RIDAGEYR, RIAGENDR) directly from DEMO_G using variables table
    demo_df = _load_demographics_from_demo("2011-2012")
    # 3) Inner-merge to keep consistent cohort with SEQN
    df = bmd_df.merge(demo_df, on="SEQN", how="inner")
    # Validate presence
    if "Age (years)" not in df.columns:
        raise ValueError("Required column 'Age (years)' is missing after merge.")
    if "Gender" not in df.columns:
        df["Gender"] = np.nan
    return df

def _load_demographics_from_demo(cycle: str) -> pd.DataFrame:
    """Fetch DEMO_G XPT using the variables table and return SEQN, Age (years), Gender.
    Does not modify the pandas_nhanes API.
    """
    import importlib.resources
    import io
    import requests
    # Read variables table shipped with the package
    with importlib.resources.path("pandas_nhanes", "nhanes_variables.csv") as csv_path:
        vars_df = pd.read_csv(csv_path)
    # Prefer DEMO_G for the given cycle
    demo_rows = vars_df[(vars_df["cycle name"] == cycle) & (vars_df["dataset"] == "DEMO_G")]
    if demo_rows.empty:
        # Fallback to the variable RIDAGEYR in the cycle
        demo_rows = vars_df[(vars_df["cycle name"] == cycle) & (vars_df["variable name"] == "RIDAGEYR")]
        if demo_rows.empty:
            raise RuntimeError("Could not locate DEMO_G or RIDAGEYR in variables table for demographics.")
    dataset_link = demo_rows.iloc[0]["dataset link"]
    # Download and read XPT
    resp = requests.get(dataset_link)
    resp.raise_for_status()
    demo = pd.read_sas(io.BytesIO(resp.content), format="xport", encoding="utf-8")
    keep = [c for c in ["SEQN", "RIDAGEYR", "RIAGENDR"] if c in demo.columns]
    if "SEQN" not in keep:
        raise RuntimeError("Demographics dataset missing SEQN.")
    demo = demo[keep].drop_duplicates(subset=["SEQN"]).copy()
    if "RIDAGEYR" in demo.columns:
        demo = demo.rename(columns={"RIDAGEYR": "Age (years)"})
    if "RIAGENDR" in demo.columns:
        demo = demo.rename(columns={"RIAGENDR": "Gender"})
        demo["Gender"] = demo["Gender"].map({1: "Male", 2: "Female"})
    return demo

def clean_data(df):
    """Removes rows with missing data and outliers."""
    # Only use BMD columns that actually exist
    bmd_cols = [c for c in BMD_COLS_DICT.values() if c in df.columns]
    # Drop rows without Age
    if "Age (years)" in df.columns:
        df = df[df["Age (years)"].notna()].reset_index(drop=True)
    if bmd_cols:
        df = df.dropna(subset=bmd_cols, how="all").reset_index(drop=True)
    else:
        # Nothing to clean with; return as-is
        return df.reset_index(drop=True)

    # Remove outliers using Z-score method for each BMD column
    outlier_mask = np.zeros(len(df), dtype=bool)
    for col in bmd_cols:
        valid_mask = df[col].notna()
        if valid_mask.sum() > 0:
            z_scores = np.abs(_safe_zscore(df.loc[valid_mask, col].to_numpy(dtype=float)))
            full_positions = np.where(valid_mask)[0]
            col_outlier_positions = full_positions[z_scores >= 3]
            outlier_mask[col_outlier_positions] = True
    return df[~outlier_mask]

# --- Data Analysis ---

def compute_fitted_data(x, y):
    """
    Computes smoothed mean and standard deviation curves for scatter plot data.
    This helps visualize the trend in the data.
    """
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean, y_clean = x[mask], y[mask]

    if len(x_clean) < 10:
        return None, None, None, None

    sort_idx = np.argsort(x_clean)
    x_sorted, y_sorted = x_clean[sort_idx], y_clean[sort_idx]

    # Bin data to calculate rolling statistics
    age_bins = np.linspace(x_sorted.min(), x_sorted.max(), 10)
    bin_centers, bin_means, bin_stds = [], [], []

    for i in range(len(age_bins) - 1):
        mask = (x_sorted >= age_bins[i]) & (x_sorted < age_bins[i + 1])
        if np.sum(mask) > 5:
            bin_centers.append((age_bins[i] + age_bins[i + 1]) / 2)
            bin_values = y_sorted[mask]
            bin_means.append(np.mean(bin_values))
            bin_stds.append(np.std(bin_values))

    if len(bin_centers) <= 3:
        return None, None, None, None

    # Smooth the curves using a Gaussian filter (fallback if SciPy missing)
    bin_centers = np.array(bin_centers)
    mean_smooth = np.maximum(_gaussian1d(np.array(bin_means), sigma=0.8), 0.1)
    std_smooth = np.maximum(_gaussian1d(np.array(bin_stds), sigma=0.8), 0.1)
    lower_1sd = np.maximum(mean_smooth - std_smooth, 0)
    upper_1sd = mean_smooth + std_smooth

    return bin_centers, mean_smooth, lower_1sd, upper_1sd

# --- Visualization ---

def create_plot(df):
    """Creates an interactive plot of BMD vs. Age for different body parts."""
    fig = make_subplots(
        rows=SUBPLOT_ROWS,
        cols=SUBPLOT_COLS,
        subplot_titles=[title for _, title in MEASUREMENTS_ORDERED] + [""],
        vertical_spacing=0.04,
        horizontal_spacing=0.04
    )

    # Determine available groups (fallback to 'All' if Gender missing)
    available_genders = sorted([g for g in df.get("Gender", pd.Series(dtype=object)).dropna().unique()])
    if len(available_genders) == 0:
        available_genders = ["All"]

    for i, (bmd_col, title) in enumerate(MEASUREMENTS_ORDERED):
        if bmd_col not in df.columns:
            continue  # skip missing columns gracefully
        row = (i // SUBPLOT_COLS) + 1
        col = (i % SUBPLOT_COLS) + 1

        for gender in available_genders:
            if gender == "All":
                gender_df = df
                color = "#6c757d"
            else:
                gender_df = df[df["Gender"] == gender]
                color = COLORS.get(gender, "#6c757d")
            x_data = gender_df["Age (years)"]
            y_data = gender_df[bmd_col]

            # Add scatter plot for raw data
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode='markers',
                    marker=dict(color=color, size=3, opacity=0.4),
                    name=gender,
                    legendgroup=gender,
                    showlegend=(i == 0)
                ),
                row=row,
                col=col
            )

            # Add smoothed trend lines
            x_fit, y_mean, y_lower, y_upper = compute_fitted_data(x_data.values, y_data.values)
            if x_fit is not None:
                fig.add_trace(
                    go.Scatter(
                        x=x_fit, y=y_mean, mode='lines',
                        line=dict(color=color, width=2),
                        name=f"{gender} Mean",
                        showlegend=False
                    ),
                    row=row, col=col
                )
                r, g, b = _hex_to_rgb(color)
                fig.add_trace(
                    go.Scatter(
                        x=np.concatenate([x_fit, x_fit[::-1]]),
                        y=np.concatenate([y_upper, y_lower[::-1]]),
                        fill='toself',
                        fillcolor=f"rgba({r}, {g}, {b}, 0.2)",
                        line=dict(color='rgba(255,255,255,0)'),
                        name=f"{gender} ±1 SD",
                        showlegend=False
                    ),
                    row=row, col=col
                )

        fig.update_xaxes(title_text="Age (years)", row=row, col=col)
        fig.update_yaxes(title_text="BMD (g/cm²)", row=row, col=col)

    fig.update_layout(
        title_text="Bone Mineral Density vs. Age and Gender (NHANES 2011-2012)",
        height=2000,
        width=1000,
        legend_title_text="Gender",
        template="plotly_white"
    )
    return fig

# --- Main Execution ---

def main():
    """Main function to run the analysis and generate the plot."""
    df = load_and_merge_data()
    df_cleaned = clean_data(df)
    fig = create_plot(df_cleaned)
    out_dir = Path(__file__).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.write_html(out_dir / "BMD_Age_Gender.html")
    # fig.write_image("BMD_Age_Gender.png", scale=2)

if __name__ == "__main__":
    main()
