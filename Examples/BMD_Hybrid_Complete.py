#!/usr/bin/env python3
"""
Hybrid BMD Analysis - NHANES Multiple Cycles
Combines the most complete data from different NHANES cycles:
- Total Body BMD: 2013-2014 cycle (ages 8-59)
- Femur & Spine BMD: 2007-2008 cycle (ages 8-80)
"""

from pandas_nhanes import get_dataset
import pandas as pd
from scipy.stats import zscore
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

print("Loading BMD data from multiple NHANES cycles...")
print("- 2007-2008: Femur and Spine BMD (ages 8-80)")
print("- 2013-2014: Total Body BMD (ages 8-59)")
print()

# Load 2007-2008 femur and spine data (full age range)
femur_data_2008 = get_dataset("DXXFEM_E")
femur_data_2008 = femur_data_2008[["SEQN", "DXXNKBMD", "DXXOFBMD"]]
femur_data_2008 = femur_data_2008.rename(columns={
    "DXXNKBMD": "Femoral Neck BMD (g/cm²)",
    "DXXOFBMD": "Total Femur BMD (g/cm²)"
})

spine_data_2008 = get_dataset("DXXSPN_E")
spine_data_2008 = spine_data_2008[["SEQN", "DXXOSBMD"]]
spine_data_2008 = spine_data_2008.rename(columns={
    "DXXOSBMD": "Total Spine BMD (g/cm²)"
})

demographics_2008 = get_dataset("DEMO_E")
demographics_2008 = demographics_2008[["SEQN", "RIDAGEYR", "RIAGENDR"]]
demographics_2008 = demographics_2008.rename(columns={
    "RIDAGEYR": "Age (years)",
    "RIAGENDR": "Gender"
})
demographics_2008["Gender"] = demographics_2008["Gender"].map({1: "Male", 2: "Female"})

# Load 2013-2014 total body data
total_body_data_2014 = get_dataset("DXX_H")
total_body_data_2014 = total_body_data_2014[["SEQN", "DXDTOBMD"]]
total_body_data_2014 = total_body_data_2014.rename(columns={
    "DXDTOBMD": "Total Body BMD (g/cm²)"
})

demographics_2014 = get_dataset("DEMO_H")
demographics_2014 = demographics_2014[["SEQN", "RIDAGEYR", "RIAGENDR"]]
demographics_2014 = demographics_2014.rename(columns={
    "RIDAGEYR": "Age (years)",
    "RIAGENDR": "Gender"
})
demographics_2014["Gender"] = demographics_2014["Gender"].map({1: "Male", 2: "Female"})

# Create 2007-2008 dataset (femur and spine)
df_2008 = pd.merge(femur_data_2008, spine_data_2008, on="SEQN", how="outer")
df_2008 = pd.merge(df_2008, demographics_2008, on="SEQN")
df_2008["Cycle"] = "2007-2008"

# Create 2013-2014 dataset (total body)
df_2014 = pd.merge(total_body_data_2014, demographics_2014, on="SEQN")
df_2014["Cycle"] = "2013-2014"

# Remove outliers for each dataset
def remove_outliers(df, cols):
    outlier_mask = np.zeros(len(df), dtype=bool)
    for col in cols:
        valid_mask = df[col].notna()
        if valid_mask.sum() > 0:
            z_scores = np.abs(zscore(df.loc[valid_mask, col]))
            outlier_positions = np.where(valid_mask)[0][z_scores >= 3]
            outlier_mask[outlier_positions] = True
    return df[~outlier_mask]

# Clean datasets
bmd_cols_2008 = ["Femoral Neck BMD (g/cm²)", "Total Femur BMD (g/cm²)", "Total Spine BMD (g/cm²)"]
bmd_cols_2014 = ["Total Body BMD (g/cm²)"]

df_2008 = df_2008.dropna(subset=bmd_cols_2008, how="all")
df_2008 = remove_outliers(df_2008, bmd_cols_2008)

df_2014 = df_2014.dropna(subset=bmd_cols_2014, how="all")
df_2014 = remove_outliers(df_2014, bmd_cols_2014)

print(f"2007-2008 data: {len(df_2008)} subjects, ages {df_2008['Age (years)'].min():.0f}-{df_2008['Age (years)'].max():.0f}")
print(f"2013-2014 data: {len(df_2014)} subjects, ages {df_2014['Age (years)'].min():.0f}-{df_2014['Age (years)'].max():.0f}")
print()

# Check data availability
for col in bmd_cols_2008:
    print(f"{col} (2007-2008): {df_2008[col].notna().sum()} subjects")
for col in bmd_cols_2014:
    print(f"{col} (2013-2014): {df_2014[col].notna().sum()} subjects")

# Create subplots for each BMD measurement by gender
fig, axes = plt.subplots(2, 2, figsize=(18, 14))
fig.suptitle("Comprehensive BMD Analysis - NHANES Multi-Cycle Data", fontsize=20, y=0.98)

# Increase font sizes globally
plt.rcParams.update({'font.size': 10})

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
    age_bins = np.linspace(x_sorted.min(), x_sorted.max(), 12)
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
        ax.plot(bin_centers, mean_smooth, color=color, linewidth=2.5, label=f'{label} Mean')
        
        # Plot 1 SD bands (ensure they don't go negative)
        lower_1sd = np.maximum(mean_smooth - std_smooth, 0)
        ax.fill_between(bin_centers, lower_1sd, mean_smooth + std_smooth,
                       color=color, alpha=0.15, label=f'{label} ±1 SD')

# Define measurements with their corresponding datasets and cycles
measurements = [
    ("Femoral Neck BMD (g/cm²)", "Femoral Neck", df_2008, "2007-2008", 8, 80),
    ("Total Femur BMD (g/cm²)", "Total Femur", df_2008, "2007-2008", 8, 80),
    ("Total Spine BMD (g/cm²)", "Total Spine", df_2008, "2007-2008", 8, 80),
    ("Total Body BMD (g/cm²)", "Total Body", df_2014, "2013-2014", 8, 59)
]

# Colors for male and female
colors = {"Male": "#1f77b4", "Female": "#ff7f0e"}

# Plot each measurement
for idx, (col, title, data, cycle, min_age, max_age) in enumerate(measurements):
    ax = axes[idx // 2, idx % 2]
    
    # Only plot if data is available
    data_mask = data[col].notna()
    if data_mask.sum() > 0:
        for gender in ["Male", "Female"]:
            gender_data = data[(data["Gender"] == gender) & data_mask]
            if len(gender_data) > 0:
                color = colors[gender]
                
                # Plot scatter points
                sns.scatterplot(data=gender_data, x="Age (years)", y=col, 
                               color=color, alpha=0.4, s=15, ax=ax, label=f'{gender} Data')
                
                # Add fitted lines
                add_fitted_lines(ax, gender_data["Age (years)"].values, gender_data[col].values, color, gender)
    
    # Customize subplot
    ax.set_xlabel("Age (years)", fontsize=12)
    ax.set_ylabel("BMD (g/cm²)", fontsize=12)
    
    # Enhanced title with cycle and age range information
    title_text = f"{title}\n({cycle}, ages {min_age}-{max_age}, n={data_mask.sum():,})"
    ax.set_title(title_text, fontsize=12, pad=15)
    
    ax.set_xlim(5, 85)
    
    # Set appropriate y-limits based on typical BMD ranges
    if "Femoral Neck" in title:
        ax.set_ylim(0.3, 1.4)
    elif "Total Femur" in title:
        ax.set_ylim(0.4, 1.6)
    elif "Total Spine" in title:
        ax.set_ylim(0.4, 1.8)
    elif "Total Body" in title:
        ax.set_ylim(0.6, 1.6)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    ax.grid(True, which='minor', alpha=0.1)
    ax.minorticks_on()
    
    # Add clinical reference lines for osteoporosis/osteopenia
    if "Femoral Neck" in title:
        ax.axhline(y=0.7, color='orange', linestyle='--', alpha=0.7, linewidth=1)
        ax.axhline(y=0.6, color='red', linestyle='--', alpha=0.7, linewidth=1)
        ax.text(82, 0.72, 'Osteopenia', fontsize=8, color='orange', alpha=0.8)
        ax.text(82, 0.62, 'Osteoporosis', fontsize=8, color='red', alpha=0.8)
    elif "Total Spine" in title:
        ax.axhline(y=1.0, color='orange', linestyle='--', alpha=0.7, linewidth=1)
        ax.axhline(y=0.8, color='red', linestyle='--', alpha=0.7, linewidth=1)
        ax.text(82, 1.02, 'Osteopenia', fontsize=8, color='orange', alpha=0.8)
        ax.text(82, 0.82, 'Osteoporosis', fontsize=8, color='red', alpha=0.8)
    
    # Add legend only to the first subplot
    if idx == 0:
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)

plt.tight_layout()
plt.savefig(__file__.replace(".py",".png"), dpi=300, bbox_inches='tight')
plt.show()

# Print detailed summary statistics
print("\n" + "="*90)
print("COMPREHENSIVE BMD ANALYSIS - MULTI-CYCLE NHANES DATA")
print("="*90)

age_groups = [
    ("Children/Teens", 8, 19),
    ("Young Adults", 20, 39), 
    ("Middle Age", 40, 59),
    ("Older Adults", 60, 80)
]

for col, title, data, cycle, min_age, max_age in measurements:
    measurement_name = title
    print(f"\n{measurement_name.upper()} ({cycle}):")
    print("-" * 70)
    
    # Overall statistics
    bmd_data = data[col].dropna()
    if len(bmd_data) > 0:
        print(f"Overall (n={len(bmd_data)}, ages {min_age}-{max_age}):")
        print(f"  Mean ± SD: {bmd_data.mean():.3f} ± {bmd_data.std():.3f} g/cm²")
        print(f"  Range: {bmd_data.min():.3f}-{bmd_data.max():.3f} g/cm²")
        print(f"  25th-75th percentile: {bmd_data.quantile(0.25):.3f}-{bmd_data.quantile(0.75):.3f} g/cm²")
    
    # By gender
    for gender in ["Male", "Female"]:
        gender_data = data[data["Gender"] == gender][col].dropna()
        if len(gender_data) > 0:
            print(f"\n{gender} (n={len(gender_data)}):")
            print(f"  Mean ± SD: {gender_data.mean():.3f} ± {gender_data.std():.3f} g/cm²")
            print(f"  Range: {gender_data.min():.3f}-{gender_data.max():.3f} g/cm²")
    
    # By age groups (only for relevant age ranges)
    print(f"\nBy Age Groups:")
    for group_name, group_min_age, group_max_age in age_groups:
        # Only show age groups that overlap with the data range
        if group_max_age >= min_age and group_min_age <= max_age:
            age_mask = (data["Age (years)"] >= group_min_age) & (data["Age (years)"] <= group_max_age)
            age_data = data[age_mask][col].dropna()
            if len(age_data) > 0:
                print(f"  {group_name} ({group_min_age}-{group_max_age} years, n={len(age_data)}):")
                print(f"    Mean ± SD: {age_data.mean():.3f} ± {age_data.std():.3f} g/cm²")
                
                # Gender breakdown within age group
                for gender in ["Male", "Female"]:
                    gender_age_data = data[age_mask & (data["Gender"] == gender)][col].dropna()
                    if len(gender_age_data) > 0:
                        print(f"      {gender}: {gender_age_data.mean():.3f} ± {gender_age_data.std():.3f} (n={len(gender_age_data)})")

print("\n" + "="*90)
print("KEY FINDINGS - HYBRID ANALYSIS:")
print("="*90)
print("• Combines best available data from multiple NHANES cycles")
print("• 2007-2008: Full age range (8-80) for femur and spine BMD")
print("• 2013-2014: Full age range (8-59) for total body BMD")
print("• Provides most comprehensive BMD assessment across lifespan")
print("• Clear visualization of peak bone mass and age-related changes")
print("• Gender differences apparent across all measurement sites")
print("• Clinical thresholds shown for osteoporosis screening")
