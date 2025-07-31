#!/usr/bin/env python3
"""
Cholesterol Analysis using NHANES 2017-2018 data.

This script analyzes the distribution of LDL, HDL, and Total Cholesterol by age,
combining data for all genders. It visualizes the relationship between age and
various cholesterol metrics.
"""

import pandas as pd
import numpy as np
from scipy.stats import zscore
from scipy.ndimage import gaussian_filter1d
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pandas_nhanes import get_dataset

# --- Constants ---

CHOLESTEROL_COLS = [
    "HDL Cholesterol (mg/dL)",
    "Total Cholesterol (mg/dL)",
    "LDL Cholesterol (mg/dL)"
]

COLORS = {
    "HDL Cholesterol (mg/dL)": "SeaGreen",
    "Total Cholesterol (mg/dL)": "RoyalBlue",
    "LDL Cholesterol (mg/dL)": "Crimson"
}

# --- Data Loading and Preprocessing ---

def load_and_merge_data():
    """Loads and merges cholesterol and demographic data from NHANES."""
    hdl_data = get_dataset("HDL_J")[["SEQN", "LBDHDD"]].rename(
        columns={"LBDHDD": "HDL Cholesterol (mg/dL)"}
    )
    total_chol_data = get_dataset("TCHOL_J")[["SEQN", "LBXTC"]].rename(
        columns={"LBXTC": "Total Cholesterol (mg/dL)"}
    )
    trigly_data = get_dataset("TRIGLY_J")[["SEQN", "LBDLDL"]].rename(
        columns={"LBDLDL": "LDL Cholesterol (mg/dL)"}
    )
    demographics = get_dataset("DEMO_J")[["SEQN", "RIDAGEYR"]].rename(
        columns={"RIDAGEYR": "Age (years)"}
    )

    df = pd.merge(hdl_data, total_chol_data, on="SEQN", how="outer")
    df = pd.merge(df, trigly_data, on="SEQN", how="outer")
    df = pd.merge(df, demographics, on="SEQN")
    return df

def clean_data(df):
    """Removes rows with missing data and outliers."""
    df = df.dropna(subset=CHOLESTEROL_COLS, how="all").reset_index(drop=True)

    # Remove outliers using Z-score method for each cholesterol column
    outlier_mask = np.zeros(len(df), dtype=bool)
    for col in CHOLESTEROL_COLS:
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
    """
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean, y_clean = x[mask], y[mask]

    if len(x_clean) < 10:
        return None, None, None, None

    sort_idx = np.argsort(x_clean)
    x_sorted, y_sorted = x_clean[sort_idx], y_clean[sort_idx]

    age_bins = np.linspace(x_sorted.min(), x_sorted.max(), 15)
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

    bin_centers = np.array(bin_centers)
    mean_smooth = np.maximum(gaussian_filter1d(np.array(bin_means), sigma=1.0), 0.1)
    std_smooth = np.maximum(gaussian_filter1d(np.array(bin_stds), sigma=1.0), 0.1)
    lower_1sd = np.maximum(mean_smooth - std_smooth, 0)
    upper_1sd = mean_smooth + std_smooth

    return bin_centers, mean_smooth, lower_1sd, upper_1sd

# --- Visualization ---

def create_plot(df):
    """Creates an interactive plot of Cholesterol vs. Age."""
    fig = make_subplots(
        rows=len(CHOLESTEROL_COLS),
        cols=1,
        subplot_titles=CHOLESTEROL_COLS,
        vertical_spacing=0.1
    )

    for i, col_name in enumerate(CHOLESTEROL_COLS):
        row = i + 1
        x_data = df["Age (years)"]
        y_data = df[col_name]

        # Add scatter plot for raw data
        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=y_data,
                mode='markers',
                marker=dict(color=COLORS[col_name], size=3, opacity=0.4),
                name=col_name,
                showlegend=False
            ),
            row=row,
            col=1
        )

        # Add smoothed trend lines
        x_fit, y_mean, y_lower, y_upper = compute_fitted_data(x_data.values, y_data.values)
        if x_fit is not None:
            fig.add_trace(
                go.Scatter(
                    x=x_fit, y=y_mean, mode='lines',
                    line=dict(color='black', width=2),
                    name="Mean",
                    showlegend=False
                ),
                row=row, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=np.concatenate([x_fit, x_fit[::-1]]),
                    y=np.concatenate([y_upper, y_lower[::-1]]),
                    fill='toself',
                    fillcolor='rgba(0,0,0,0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name="±1 SD",
                    showlegend=False
                ),
                row=row, col=1
            )

        fig.update_xaxes(title_text="Age (years)", row=row, col=1)
        fig.update_yaxes(title_text="Cholesterol (mg/dL)", row=row, col=1)

    fig.update_layout(
        title_text="Cholesterol Levels vs. Age (NHANES 2017-2018)",
        height=1200,
        width=800,
        template="plotly_white"
    )
    return fig

# --- Main Execution ---

def main():
    """Main function to run the analysis and generate the plot."""
    df = load_and_merge_data()
    df_cleaned = clean_data(df)

    print(f"Total subjects with cholesterol data: {len(df_cleaned)}")
    print(f"Age range: {df_cleaned['Age (years)'].min():.0f}-{df_cleaned['Age (years)'].max():.0f} years")
    for col in CHOLESTEROL_COLS:
        print(f"{col}: {df_cleaned[col].notna().sum()} subjects")

    fig = create_plot(df_cleaned)
    fig.write_html("Cholesterol_Age.html")
    #fig.write_image("Cholesterol_Age.png", scale=2)

if __name__ == "__main__":
    main()