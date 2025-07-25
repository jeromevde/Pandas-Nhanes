#!/usr/bin/env python3
"""
Comprehensive Whole-Body BMD Analysis - NHANES 2011-2012
Analyzes BMD distribution across ALL body parts measured by DEXA:
Head, Arms, Legs, Ribs, Spine regions, Pelvis, Trunk, and Total Body
"""

from pandas_nhanes import get_dataset
import pandas as pd
from scipy.stats import zscore
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

print("Loading comprehensive whole-body BMD data from NHANES 2011-2012...")
print("Including: Head, Arms, Legs, Ribs, Spine, Pelvis, Trunk, and Total Body")
print()

# Load comprehensive BMD data from 2011-2012
bmd_data = get_dataset("DXX_G")

# Select all available BMD measurements
bmd_cols_dict = {
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

# Prepare BMD data
bmd_columns = ["SEQN"] + list(bmd_cols_dict.keys())
bmd_data = bmd_data[bmd_columns]
bmd_data = bmd_data.rename(columns=bmd_cols_dict)

# Load demographics data
demographics = get_dataset("DEMO_G")
demographics = demographics[["SEQN", "RIDAGEYR", "RIAGENDR"]]
demographics = demographics.rename(columns={
    "RIDAGEYR": "Age (years)",
    "RIAGENDR": "Gender"
})
demographics["Gender"] = demographics["Gender"].map({1: "Male", 2: "Female"})

# Merge datasets
df = pd.merge(bmd_data, demographics, on="SEQN")

# Remove rows with all missing BMD data
bmd_cols = list(bmd_cols_dict.values())
df = df.dropna(subset=bmd_cols, how="all")

# Reset index and remove outliers
df = df.reset_index(drop=True)
outlier_mask = np.zeros(len(df), dtype=bool)
for col in bmd_cols:
    valid_mask = df[col].notna()
    if valid_mask.sum() > 0:
        z_scores = np.abs(zscore(df.loc[valid_mask, col]))
        outlier_positions = np.where(valid_mask)[0][z_scores >= 3]
        outlier_mask[outlier_positions] = True

df = df[~outlier_mask]

print(f"Total subjects with BMD data: {len(df)}")
print(f"Age range: {df['Age (years)'].min():.0f}-{df['Age (years)'].max():.0f} years")
print(f"Gender distribution: {df['Gender'].value_counts().to_dict()}")
print()

# Check data availability for each BMD measurement
for col in bmd_cols:
    print(f"{col}: {df[col].notna().sum()} subjects")

# Create comprehensive subplots - need a larger grid for all measurements
fig, axes = plt.subplots(4, 4, figsize=(24, 20))
fig.suptitle("Comprehensive Whole-Body BMD Analysis - NHANES 2011-2012\nAll DEXA Measurement Sites", fontsize=24, y=0.98)

# Hide the empty subplots (we have 13 measurements, need 16 subplots)
axes[3, 1].set_visible(False)
axes[3, 2].set_visible(False)
axes[3, 3].set_visible(False)

# Increase font sizes globally
plt.rcParams.update({'font.size': 9})

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
    age_bins = np.linspace(x_sorted.min(), x_sorted.max(), 10)
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
        
        # Apply gentle Gaussian smoothing
        mean_smooth = gaussian_filter1d(bin_means, sigma=0.8)
        std_smooth = gaussian_filter1d(bin_stds, sigma=0.8)
        
        # Ensure values never go negative
        mean_smooth = np.maximum(mean_smooth, 0.1)
        std_smooth = np.maximum(std_smooth, 0.1)
        
        # Plot mean line
        ax.plot(bin_centers, mean_smooth, color=color, linewidth=2, label=f'{label} Mean')
        
        # Plot 1 SD bands
        lower_1sd = np.maximum(mean_smooth - std_smooth, 0)
        ax.fill_between(bin_centers, lower_1sd, mean_smooth + std_smooth,
                       color=color, alpha=0.15, label=f'{label} ±1 SD')

# Colors for male and female
colors = {"Male": "#1f77b4", "Female": "#ff7f0e"}

# Create a list of measurements in logical order
measurements_ordered = [
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

# Plot each measurement
for idx, (col, title) in enumerate(measurements_ordered):
    row = idx // 4
    col_idx = idx % 4
    ax = axes[row, col_idx]
    
    # Only plot if data is available
    data_mask = df[col].notna()
    if data_mask.sum() > 0:
        for gender in ["Male", "Female"]:
            gender_data = df[(df["Gender"] == gender) & data_mask]
            if len(gender_data) > 0:
                color = colors[gender]
                
                # Plot scatter points
                sns.scatterplot(data=gender_data, x="Age (years)", y=col, 
                               color=color, alpha=0.3, s=8, ax=ax, label=f'{gender} Data')
                
                # Add fitted lines
                add_fitted_lines(ax, gender_data["Age (years)"].values, gender_data[col].values, color, gender)
    
    # Customize subplot
    ax.set_xlabel("Age (years)", fontsize=10)
    ax.set_ylabel("BMD (g/cm²)", fontsize=10)
    ax.set_title(f"{title}\n(n={data_mask.sum():,})", fontsize=11, pad=10)
    ax.set_xlim(5, 65)
    
    # Set appropriate y-limits based on body part
    if "Head" in title:
        ax.set_ylim(1.0, 3.5)
    elif "Arm" in title:
        ax.set_ylim(0.4, 1.2)
    elif "Leg" in title:
        ax.set_ylim(0.6, 1.8)
    elif "Rib" in title:
        ax.set_ylim(0.3, 1.0)
    elif "Spine" in title:
        ax.set_ylim(0.4, 1.8)
    elif "Pelvis" in title:
        ax.set_ylim(0.6, 1.8)
    elif "Trunk" in title:
        ax.set_ylim(0.4, 1.4)
    elif "Total" in title or "Subtotal" in title:
        ax.set_ylim(0.6, 1.6)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    ax.minorticks_on()
    
    # Add legend only to the first subplot
    if idx == 0:
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)

plt.tight_layout()
plt.savefig(__file__.replace(".py",".png"), dpi=300, bbox_inches='tight')
plt.show()

# Print detailed summary statistics
print("\n" + "="*100)
print("COMPREHENSIVE WHOLE-BODY BMD ANALYSIS - NHANES 2011-2012")
print("="*100)

age_groups = [
    ("Children/Teens", 8, 19),
    ("Young Adults", 20, 39), 
    ("Middle Age", 40, 59)
]

# Group measurements by body region for better organization
body_regions = {
    "HEAD & SKULL": ["Head BMD (g/cm²)"],
    "ARMS": ["Left Arm BMD (g/cm²)", "Right Arm BMD (g/cm²)"],
    "LEGS": ["Left Leg BMD (g/cm²)", "Right Leg BMD (g/cm²)"],
    "RIBS": ["Left Ribs BMD (g/cm²)", "Right Ribs BMD (g/cm²)"],
    "SPINE": ["Lumbar Spine BMD (g/cm²)", "Thoracic Spine BMD (g/cm²)"],
    "PELVIS": ["Pelvis BMD (g/cm²)"],
    "COMPOSITE": ["Trunk BMD (g/cm²)", "Subtotal BMD (g/cm²)", "Total Body BMD (g/cm²)"]
}

for region_name, measurements in body_regions.items():
    print(f"\n{region_name}:")
    print("-" * 80)
    
    for col in measurements:
        measurement_name = col.replace(" (g/cm²)", "")
        bmd_data = df[col].dropna()
        
        if len(bmd_data) > 0:
            print(f"\n{measurement_name} (n={len(bmd_data)}):")
            print(f"  Overall: {bmd_data.mean():.3f} ± {bmd_data.std():.3f} g/cm²")
            print(f"  Range: {bmd_data.min():.3f}-{bmd_data.max():.3f} g/cm²")
            
            # By gender
            for gender in ["Male", "Female"]:
                gender_data = df[df["Gender"] == gender][col].dropna()
                if len(gender_data) > 0:
                    print(f"  {gender}: {gender_data.mean():.3f} ± {gender_data.std():.3f} (n={len(gender_data)})")

print("\n" + "="*100)
print("KEY FINDINGS - COMPREHENSIVE WHOLE-BODY ANALYSIS:")
print("="*100)
print("• Most complete BMD dataset available from NHANES 2011-2012")
print("• 13 different body regions/measurements analyzed")
print("• Head BMD shows highest values (dense skull bone)")
print("• Ribs show lowest BMD values (trabecular-rich bone)")
print("• Clear anatomical differences in bone density patterns")
print("• Gender differences apparent across all body regions")
print("• Age-related changes visible from childhood through middle age")
print("• Comprehensive assessment of whole-body skeletal health")
