#!/usr/bin/env python3
"""
Estradiol Analysis using NHANES 2021-2023 data.

This script analyzes the distribution of Estradiol by gender and age,
visualizing the relationship between these variables.
"""

import pandas as pd
import numpy as np
from scipy.stats import zscore
from scipy.ndimage import gaussian_filter1d
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pandas_nhanes import get_dataset

# --- Constants ---

COLORS = {"Men": "#1f77b4", "Women": "#ff7f0e"}

# --- Data Loading and Preprocessing ---

def load_and_merge_data():
    """Loads and merges estradiol and demographic data from NHANES."""
    steroid_panel = get_dataset("TST_L")[["SEQN", "LBXEST"]].rename(
        columns={"LBXEST": "Estradiol (pg/mL)"}
    )
    demographics = get_dataset("DEMO_L")[["SEQN", "RIAGENDR", "RIDAGEYR"]].rename(
        columns={"RIAGENDR": "Gender", "RIDAGEYR": "Age (years)"}
    )

    df = pd.merge(steroid_panel, demographics, on="SEQN")
    df = df.dropna().reset_index(drop=True)
    df['Gender'] = df['Gender'].map({1: 'Men', 2: 'Women'})
    return df

def clean_data(df):
    """Removes outliers from the data."""
    # Remove outliers using Z-score method
    return df[(np.abs(zscore(df[["Estradiol (pg/mL)"]], nan_policy='omit')) < 3).all(axis=1)]

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
    """Creates an interactive plot of Estradiol vs. Age by Gender."""
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=["Men", "Women"],
        shared_yaxes=True
    )

    for i, gender in enumerate(["Men", "Women"]):
        col = i + 1
        gender_df = df[df["Gender"] == gender]
        x_data = gender_df["Age (years)"]
        y_data = gender_df["Estradiol (pg/mL)"]

        # Add scatter plot for raw data
        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=y_data,
                mode='markers',
                marker=dict(color=COLORS[gender], size=4, opacity=0.5),
                name=gender,
                showlegend=False
            ),
            row=1,
            col=col
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
                row=1, col=col
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
                row=1, col=col
            )

        fig.update_xaxes(title_text="Age (years)", row=1, col=col)
    
    fig.update_yaxes(title_text="Estradiol (pg/mL)", row=1, col=1)

    fig.update_layout(
        title_text="Estradiol vs. Age by Gender (NHANES 2021-2023)",
        height=600,
        width=1000,
        template="plotly_white"
    )
    return fig

# --- Main Execution ---

def main():
    """Main function to run the analysis and generate the plot."""
    df = load_and_merge_data()
    df_cleaned = clean_data(df)

    print(f"Total subjects: {len(df_cleaned)}")
    print(f"Men: {len(df_cleaned[df_cleaned['Gender'] == 'Men'])}")
    print(f"Women: {len(df_cleaned[df_cleaned['Gender'] == 'Women'])}")
    print(f"Age range: {df_cleaned['Age (years)'].min():.0f}-{df_cleaned['Age (years)'].max():.0f} years")

    fig = create_plot(df_cleaned)
    fig.write_html("Estradiol_Age_Gender.html")
    fig.write_image("Estradiol_Age_Gender.png", scale=2)

if __name__ == "__main__":
    main()
