#!/usr/bin/env python3
"""
Cholesterol Analysis - NHANES Cycle 2017-2018
Analyzes LDL, HDL, and Total cholesterol distribution by age (combined genders)
"""

from pandas_nhanes import get_dataset
import pandas as pd
from scipy.stats import zscore
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

# Load cholesterol datasets
hdl_data = get_dataset("HDL_J")
hdl_data = hdl_data[["SEQN", "LBDHDD"]]
hdl_data = hdl_data.rename(columns={"LBDHDD": "HDL Cholesterol (mg/dL)"})

total_chol_data = get_dataset("TCHOL_J")
total_chol_data = total_chol_data[["SEQN", "LBXTC"]]
total_chol_data = total_chol_data.rename(columns={"LBXTC": "Total Cholesterol (mg/dL)"})

trigly_data = get_dataset("TRIGLY_J")
trigly_data = trigly_data[["SEQN", "LBDLDL"]]
trigly_data = trigly_data.rename(columns={"LBDLDL": "LDL Cholesterol (mg/dL)"})

# Load demographics data
demographics = get_dataset("DEMO_J")
demographics = demographics[["SEQN", "RIDAGEYR"]]
demographics = demographics.rename(columns={
    "RIDAGEYR": "Age (years)"
})

# Merge all datasets
df = pd.merge(hdl_data, total_chol_data, on="SEQN", how="outer")
df = pd.merge(df, trigly_data, on="SEQN", how="outer")
df = pd.merge(df, demographics, on="SEQN")

# Remove rows with all missing cholesterol data
df = df.dropna(subset=["HDL Cholesterol (mg/dL)", "Total Cholesterol (mg/dL)", "LDL Cholesterol (mg/dL)"], how="all")

# Define cholesterol columns
cholesterol_cols = ["HDL Cholesterol (mg/dL)", "Total Cholesterol (mg/dL)", "LDL Cholesterol (mg/dL)"]

# Remove outliers using z-score (threshold=3) for any cholesterol measurement
outlier_mask = np.zeros(len(df), dtype=bool)
for col in cholesterol_cols:
    col_outliers = np.abs(zscore(df[[col]], nan_policy='omit')) >= 3
    outlier_mask |= col_outliers.iloc[:, 0]

df = df[~outlier_mask]

print(f"Total subjects with cholesterol data: {len(df)}")
print(f"Age range: {df['Age (years)'].min():.0f}-{df['Age (years)'].max():.0f} years")

# Check data availability for each cholesterol type
for col in cholesterol_cols:
    print(f"{col}: {df[col].notna().sum()} subjects")

# Create a single plot with all three cholesterol types
fig, ax = plt.subplots(1, 1, figsize=(14, 10))
fig.suptitle("Cholesterol Levels vs Age - NHANES 2017-2018", fontsize=18, y=0.98)

# Increase font sizes globally
plt.rcParams.update({'font.size': 12})

# Function to add fitted mean and standard deviation lines
def add_fitted_lines(ax, x, y, color, label):
    from scipy.ndimage import gaussian_filter1d
    
    # Remove NaN values
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean, y_clean = x[mask], y[mask]
    
    if len(x_clean) < 10:  # Need enough points for fitting
        return
    
    # Sort by age for smooth curves
    sort_idx = np.argsort(x_clean)
    x_sorted = x_clean[sort_idx]
    y_sorted = y_clean[sort_idx]
    
    # Create age bins for local statistics
    age_bins = np.linspace(x_sorted.min(), x_sorted.max(), 15)
    bin_centers = []
    bin_means = []
    bin_stds = []
    
    for i in range(len(age_bins)-1):
        mask = (x_sorted >= age_bins[i]) & (x_sorted < age_bins[i+1])
        if np.sum(mask) > 5:  # Need enough points in bin
            bin_centers.append((age_bins[i] + age_bins[i+1]) / 2)
            bin_values = y_sorted[mask]
            bin_means.append(np.mean(bin_values))
            bin_stds.append(np.std(bin_values))
    
    if len(bin_centers) > 3:  # Need enough bins for smoothing
        bin_centers = np.array(bin_centers)
        bin_means = np.array(bin_means)
        bin_stds = np.array(bin_stds)
        
        # Apply gentle Gaussian smoothing to avoid wild oscillations
        mean_smooth = gaussian_filter1d(bin_means, sigma=1.0)
        std_smooth = gaussian_filter1d(bin_stds, sigma=1.0)
        
        # Ensure values never go negative
        mean_smooth = np.maximum(mean_smooth, 0.1)
        std_smooth = np.maximum(std_smooth, 0.1)
        
        # Plot mean line
        ax.plot(bin_centers, mean_smooth, color=color, linewidth=3, label=f'{label} Mean', linestyle='-')
        
        # Plot 1 SD bands (ensure they don't go negative)
        lower_1sd = np.maximum(mean_smooth - std_smooth, 0)
        ax.fill_between(bin_centers, lower_1sd, mean_smooth + std_smooth,
                       color=color, alpha=0.15, label=f'{label} ±1 SD')

# Colors for each cholesterol type
colors = {
    "HDL Cholesterol (mg/dL)": "#2E8B57",    # Sea Green
    "Total Cholesterol (mg/dL)": "#DC143C",   # Crimson
    "LDL Cholesterol (mg/dL)": "#4169E1"     # Royal Blue
}

# Plot scatter points and fitted lines for each cholesterol type
for col in cholesterol_cols:
    # Only plot points where data is available
    data_mask = df[col].notna()
    if data_mask.sum() > 0:
        label = col.replace(" (mg/dL)", "")
        color = colors[col]
        
        # Plot scatter points
        sns.scatterplot(data=df[data_mask], x="Age (years)", y=col, 
                       color=color, alpha=0.3, s=20, ax=ax, label=f'{label} Data')
        
        # Add fitted lines
        add_fitted_lines(ax, df[data_mask]["Age (years)"].values, df[data_mask][col].values, color, label)

# Customize the plot
ax.set_xlabel("Age (years)", fontsize=14)
ax.set_ylabel("Cholesterol Level (mg/dL)", fontsize=14)
ax.set_title(f"Combined Analysis (n={len(df):,} subjects)", fontsize=14)
ax.set_xlim(0, 85)
ax.set_ylim(0, 300)

# Set axis ticks
ax.set_xticks(range(0, 91, 10))  # X-axis every 10 years
ax.set_yticks(range(0, 301, 50))  # Y-axis every 50 mg/dL

# Add grid
ax.grid(True, alpha=0.3)
ax.grid(True, which='minor', alpha=0.1)
ax.minorticks_on()

# Add legend
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)

# Add clinical reference lines with better positioning
ref_lines = [
    (40, 'Low HDL (<40 mg/dL)', 'dimgray'),
    (60, 'High HDL (≥60 mg/dL)', 'darkgreen'),
    (100, 'Optimal LDL (<100 mg/dL)', 'dimgray'),
    (130, 'Borderline High LDL (130-159 mg/dL)', 'orange'),
    (160, 'High LDL (≥160 mg/dL)', 'red'),
    (200, 'Borderline High Total (200-239 mg/dL)', 'orange'),
    (240, 'High Total (≥240 mg/dL)', 'red')
]

for y_pos, label, color in ref_lines:
    if y_pos <= 300:  # Only show lines within our y-axis range
        ax.axhline(y=y_pos, color=color, linestyle='--', alpha=0.6, linewidth=1)

# Add reference line labels positioned to avoid overlap
ax.text(85, 42, 'Low HDL', fontsize=8, color='dimgray', alpha=0.8, rotation=0)
ax.text(85, 62, 'High HDL', fontsize=8, color='darkgreen', alpha=0.8, rotation=0)
ax.text(85, 102, 'Optimal LDL', fontsize=8, color='dimgray', alpha=0.8, rotation=0)
ax.text(70, 132, 'Borderline High LDL', fontsize=8, color='orange', alpha=0.8, rotation=0)
ax.text(75, 162, 'High LDL', fontsize=8, color='red', alpha=0.8, rotation=0)
ax.text(60, 202, 'Borderline High Total', fontsize=8, color='orange', alpha=0.8, rotation=0)
ax.text(70, 242, 'High Total', fontsize=8, color='red', alpha=0.8, rotation=0)

plt.tight_layout()
plt.savefig(__file__.replace(".py",".png"), dpi=300, bbox_inches='tight')
plt.show()

# Print summary statistics
print("\nSummary Statistics:")
for col in cholesterol_cols:
    data = df[col].dropna()
    if len(data) > 0:
        label = col.replace(" (mg/dL)", "")
        print(f"{label}:")
        print(f"  Mean: {data.mean():.1f} mg/dL")
        print(f"  Median: {data.median():.1f} mg/dL")
        print(f"  Range: {data.min():.1f}-{data.max():.1f} mg/dL")
        print(f"  25th-75th percentile: {data.quantile(0.25):.1f}-{data.quantile(0.75):.1f} mg/dL")
        print()
