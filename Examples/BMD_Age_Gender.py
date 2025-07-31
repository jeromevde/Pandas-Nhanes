#!/usr/bin/env python3
"""
Comprehensive Whole-Body Bone Mineral Density (BMD) Analysis using NHANES 2011-2012 data.

This script analyzes the distribution of BMD across various body parts measured by DEXA scans,
including the head, arms, legs, ribs, spine, pelvis, trunk, and total body. It visualizes
the relationship between age, gender, and BMD for each body part.
"""

import pandas as pd
import numpy as np
from scipy.stats import zscore
from scipy.ndimage import gaussian_filter1d
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pandas_nhanes import get_dataset

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

COLORS = {"Male": "#1f77b4", "Female": "#ff7f0e"}
SUBPLOT_ROWS = 7
SUBPLOT_COLS = 2

# --- Data Loading and Preprocessing ---

def load_and_merge_data():
    """Loads and merges BMD and demographic data from NHANES."""
    bmd_data = get_dataset("DXX_G")
    demographics = get_dataset("DEMO_G")

    bmd_columns = ["SEQN"] + list(BMD_COLS_DICT.keys())
    bmd_data = bmd_data[bmd_columns].rename(columns=BMD_COLS_DICT)

    demographics = demographics[["SEQN", "RIDAGEYR", "RIAGENDR"]].rename(
        columns={"RIDAGEYR": "Age (years)", "RIAGENDR": "Gender"}
    )
    demographics["Gender"] = demographics["Gender"].map({1: "Male", 2: "Female"})

    return pd.merge(bmd_data, demographics, on="SEQN")

def clean_data(df):
    """Removes rows with missing data and outliers."""
    bmd_cols = list(BMD_COLS_DICT.values())
    df = df.dropna(subset=bmd_cols, how="all").reset_index(drop=True)

    # Remove outliers using Z-score method for each BMD column
    outlier_mask = np.zeros(len(df), dtype=bool)
    for col in bmd_cols:
        valid_mask = df[col].notna()
        if valid_mask.sum() > 0:
            z_scores = np.abs(zscore(df.loc[valid_mask, col]))
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

    # Smooth the curves using a Gaussian filter
    bin_centers = np.array(bin_centers)
    mean_smooth = np.maximum(gaussian_filter1d(np.array(bin_means), sigma=0.8), 0.1)
    std_smooth = np.maximum(gaussian_filter1d(np.array(bin_stds), sigma=0.8), 0.1)
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

    for i, (bmd_col, title) in enumerate(MEASUREMENTS_ORDERED):
        row = (i // SUBPLOT_COLS) + 1
        col = (i % SUBPLOT_COLS) + 1

        for gender in ["Male", "Female"]:
            gender_df = df[df["Gender"] == gender]
            x_data = gender_df["Age (years)"]
            y_data = gender_df[bmd_col]

            # Add scatter plot for raw data
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode='markers',
                    marker=dict(color=COLORS[gender], size=3, opacity=0.4),
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
                        line=dict(color=COLORS[gender], width=2),
                        name=f"{gender} Mean",
                        showlegend=False
                    ),
                    row=row, col=col
                )
                fig.add_trace(
                    go.Scatter(
                        x=np.concatenate([x_fit, x_fit[::-1]]),
                        y=np.concatenate([y_upper, y_lower[::-1]]),
                        fill='toself',
                        fillcolor=f"rgba({int(COLORS[gender][1:3], 16)}, {int(COLORS[gender][3:5], 16)}, {int(COLORS[gender][5:7], 16)}, 0.2)",
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
    fig.write_html("BMD_Age_Gender.html")
    fig.write_image("BMD_Age_Gender.png", scale=2)

if __name__ == "__main__":
    main()
