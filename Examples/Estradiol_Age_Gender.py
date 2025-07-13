#!/usr/bin/env python3
"""
Estradiol Analysis - NHANES Cycle 2021-2023
Analyzes estradiol distribution by gender with age statistics
"""

from pandas_nhanes import get_dataset
import pandas as pd
from scipy.stats import zscore
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

# Load steroid hormone data
steroid_panel = get_dataset("TST_L")
steroid_panel = steroid_panel[["SEQN", "LBXEST"]]
steroid_panel = steroid_panel.rename(columns={"LBXEST": "Estradiol (pg/mL)"})

# Load demographics data
demographics = get_dataset("DEMO_L")
demographics = demographics[["SEQN", "RIAGENDR", "RIDAGEYR"]]
demographics = demographics.rename(columns={
    "RIAGENDR": "Gender", 
    "RIDAGEYR": "Age (years)"
})

# Merge datasets
df = pd.merge(steroid_panel, demographics, on="SEQN")
df = df.dropna()  # Remove rows with missing data

# Assign gender labels
df['Gender'] = df['Gender'].map({1: 'Men', 2: 'Women'})

# Remove outliers using z-score (threshold=3)
df = df[(np.abs(zscore(df[["Estradiol (pg/mL)"]], nan_policy='omit')) < 3).all(axis=1)]

print(f"Total subjects: {len(df)}")
print(f"Men: {len(df[df['Gender'] == 'Men'])}")
print(f"Women: {len(df[df['Gender'] == 'Women'])}")
print(f"Age range: {df['Age (years)'].min():.0f}-{df['Age (years)'].max():.0f} years")

# Separate data by gender
men_data = df[df['Gender'] == 'Men'].copy()
women_data = df[df['Gender'] == 'Women'].copy()

# Create side-by-side scatter plots
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle("Estradiol vs Age by Gender - NHANES 2021-2023", fontsize=18, y=0.98)

# Increase font sizes globally
plt.rcParams.update({'font.size': 12})

# Function to add fitted mean and standard deviation lines
def add_fitted_lines(ax, x, y, color):
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
        ax.plot(bin_centers, mean_smooth, color=color, linewidth=2, label='Mean')
        
        # Plot 1 SD bands (ensure they don't go negative)
        lower_1sd = np.maximum(mean_smooth - std_smooth, 0)
        ax.fill_between(bin_centers, lower_1sd, mean_smooth + std_smooth,
                       color=color, alpha=0.2, label='±1 SD')
        
        # Plot 2 SD bands (ensure they don't go negative)
        lower_2sd = np.maximum(mean_smooth - 2*std_smooth, 0)
        ax.fill_between(bin_centers, lower_2sd, mean_smooth + 2*std_smooth,
                       color=color, alpha=0.1, label='±2 SD')

# Plot Men
sns.scatterplot(data=men_data, x="Age (years)", y="Estradiol (pg/mL)", 
                color="#D7263D", alpha=0.4, s=30, ax=axes[0])
add_fitted_lines(axes[0], men_data["Age (years)"].values, men_data["Estradiol (pg/mL)"].values, "#D7263D")
axes[0].set_title(f"Men (n={len(men_data):,})", fontsize=14)
axes[0].set_ylim(0, 350)
axes[0].set_xticks(range(0, 81, 10))  # X-axis every 10 years
axes[0].set_yticks(range(0, 351, 50))  # Y-axis every 50 pg/mL

# Add note about outliers not shown for men
men_outliers = len(men_data[men_data["Estradiol (pg/mL)"] > 350])
if men_outliers > 0:
    axes[0].text(0.02, 0.98, f"Note: {men_outliers} outliers >350 pg/mL not shown", 
                transform=axes[0].transAxes, fontsize=10, 
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", 
                facecolor='lightcoral', alpha=0.7))

axes[0].legend(fontsize=11)
axes[0].grid(True, alpha=0.3)
axes[0].grid(True, which='minor', alpha=0.1)
axes[0].minorticks_on()

# Plot Women  
sns.scatterplot(data=women_data, x="Age (years)", y="Estradiol (pg/mL)", 
                color="#1B7CED", alpha=0.4, s=30, ax=axes[1])
add_fitted_lines(axes[1], women_data["Age (years)"].values, women_data["Estradiol (pg/mL)"].values, "#1B7CED")
axes[1].set_title(f"Women (n={len(women_data):,})", fontsize=14)
axes[1].set_ylim(0, 350)
axes[1].set_xticks(range(0, 81, 10))  # X-axis every 10 years
axes[1].set_yticks(range(0, 351, 50))  # Y-axis every 50 pg/mL

# Add note about outliers not shown for women
women_outliers = len(women_data[women_data["Estradiol (pg/mL)"] > 350])
if women_outliers > 0:
    axes[1].text(0.02, 0.98, f"Note: {women_outliers} outliers >350 pg/mL not shown", 
                transform=axes[1].transAxes, fontsize=10, 
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", 
                facecolor='lightblue', alpha=0.7))

axes[1].legend(fontsize=11)
axes[1].grid(True, alpha=0.3)
axes[1].grid(True, which='minor', alpha=0.1)
axes[1].minorticks_on()

plt.tight_layout()
plt.savefig(__file__.replace(".py",".png"), dpi=300, bbox_inches='tight')
plt.show()
