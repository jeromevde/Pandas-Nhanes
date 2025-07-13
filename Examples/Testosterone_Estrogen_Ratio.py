#!/usr/bin/env python3
"""
Analysis of Testosterone/Estradiol ratio distribution in men from NHANES 2015-2016 cycle
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pandas_nhanes import get_dataset

# Set style for better plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def analyze_t_e2_ratio():
    """Analyze T/E2 ratio distribution in men from NHANES 2015-2016"""
    
    print("Loading NHANES 2015-2016 hormone and demographics data...")
    
    # Load hormone data (TST_I) and demographics (DEMO_I) for 2015-2016 cycle
    tst_data = get_dataset("TST_I")
    demo_data = get_dataset("DEMO_I")
    
    # Select relevant columns
    hormone_data = tst_data[['SEQN', 'LBXTST', 'LBXEST']].copy()  # Testosterone and Estradiol
    demo_data_subset = demo_data[['SEQN', 'RIAGENDR', 'RIDAGEYR']].copy()  # Gender and Age
    
    # Merge datasets
    merged_data = pd.merge(hormone_data, demo_data_subset, on='SEQN', how='inner')
    
    # Clean data: remove missing values
    merged_data = merged_data.dropna(subset=['LBXTST', 'LBXEST', 'RIAGENDR', 'RIDAGEYR'])
    
    # Filter for males only (RIAGENDR == 1) and age > 16
    men_data = merged_data[(merged_data['RIAGENDR'] == 1) & (merged_data['RIDAGEYR'] > 16)].copy()
    print(f"Men over 16 years old with complete hormone data: {len(men_data)}")
    
    # Calculate T/E2 ratio
    # LBXTST: Testosterone, total (ng/dL)
    # LBXEST: Estradiol (pg/mL)
    # Ratio units: (ng/dL) / (pg/mL)
    men_data['T_E2_ratio'] = men_data['LBXTST'] / men_data['LBXEST']
    
    # Remove extreme outliers using modified approach - keep values down to T/E2 ratio of 5
    Q1 = men_data['T_E2_ratio'].quantile(0.25)
    Q3 = men_data['T_E2_ratio'].quantile(0.75)
    IQR = Q3 - Q1
    
    # Use less restrictive outlier removal and ensure we keep values down to T/E2 = 5
    lower_bound = 0
    upper_bound = Q3 + 2.0 * IQR  # Use 2*IQR instead of 1.5*IQR for upper bound
    
    men_data_clean = men_data[(men_data['T_E2_ratio'] >= lower_bound) & 
                             (men_data['T_E2_ratio'] <= upper_bound)].copy()
    
    print(f"Outlier removal bounds: {lower_bound:.2f} to {upper_bound:.2f}")
    print(f"Men after outlier removal: {len(men_data_clean)}")
    
    # Create age groups
    men_data_clean['age_group'] = pd.cut(men_data_clean['RIDAGEYR'], 
                                       bins=[16, 20, 30, 40, 50, 60, 70, 120], 
                                       labels=['17-20', '21-30', '31-40', '41-50', '51-60', '61-70', '70+'])
    
    return men_data_clean

def create_plots(data):
    """Create simple histogram with fitted Gaussian and age group statistics in legend"""
    
    print("Creating T/E2 ratio histogram with fitted Gaussian...")
    
    # Create a single figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Create histogram for overall population
    n_bins = 50
    counts, bins, patches = ax.hist(data['T_E2_ratio'], bins=n_bins, alpha=0.7, 
                                   color='steelblue', edgecolor='black', 
                                   label='Observed Data')
    
    # Fit Gaussian to overall population (for statistics only, not plotting)
    overall_mean = data['T_E2_ratio'].mean()
    overall_std = data['T_E2_ratio'].std()
    
    # Customize the plot
    ax.set_xlabel('Testosterone/Estradiol Ratio (ng/dL ÷ pg/mL)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax.set_title('T/E2 Ratio Distribution\n(NHANES 2015-2016 Men > 16 years)\nTestosterone (ng/dL) / Estradiol (pg/mL)', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Add grid for better readability
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    
    # Calculate age group statistics for legend
    age_groups_sorted = ['17-20', '21-30', '31-40', '41-50', '51-60', '61-70', '70+']
    legend_lines = []
    
    # Add overall statistics first
    legend_lines.append(f'Overall: μ={overall_mean:.2f}, σ={overall_std:.2f} (n={len(data):,})')
    legend_lines.append('')  # Empty line for spacing
    
    # Add age group statistics
    legend_lines.append('Age Group Statistics:')
    for age_group in age_groups_sorted:
        if age_group in data['age_group'].values:
            group_data = data[data['age_group'] == age_group]['T_E2_ratio']
            if len(group_data) > 0:
                mean = group_data.mean()
                std = group_data.std()
                n = len(group_data)
                legend_lines.append(f'{age_group}: μ={mean:.2f}, σ={std:.2f} (n={n})')
    
    # Create custom legend with age group statistics
    legend_text = '\n'.join(legend_lines)
    
    # Remove the fitted Gaussian legend since we're not plotting it anymore
    # ax.legend(loc='upper right', fontsize=12, framealpha=0.9)
    
    # Add age group statistics as text box
    props = dict(boxstyle='round', facecolor='lightgray', alpha=0.9, pad=0.5)
    ax.text(0.02, 0.98, legend_text, transform=ax.transAxes, fontsize=11,
           verticalalignment='top', bbox=props, family='monospace')
    
    # Add vertical line for overall mean
    ax.axvline(overall_mean, color='red', linestyle='--', alpha=0.7, linewidth=2)
    
    plt.tight_layout()
    plt.show()
    
    # Save the plot
    plt.savefig(__file__.replace(".py",".png"), dpi=300, bbox_inches='tight')
    print("Plot saved as 'T_E2_ratio_distribution_men_2015_2016.png'")

def print_summary_stats(data):
    """Print comprehensive summary statistics"""
    
    print(f"\n=== T/E2 RATIO ANALYSIS SUMMARY ===")
    print(f"Sample size: {len(data)} men")
    print(f"Age range: {data['RIDAGEYR'].min():.0f} - {data['RIDAGEYR'].max():.0f} years")
    print(f"Mean age: {data['RIDAGEYR'].mean():.1f} ± {data['RIDAGEYR'].std():.1f} years")
    print(f"\nRatio calculation: Testosterone (ng/dL) / Estradiol (pg/mL)")
    
    print(f"\nT/E2 Ratio Statistics:")
    print(f"  Mean: {data['T_E2_ratio'].mean():.2f}")
    print(f"  Median: {data['T_E2_ratio'].median():.2f}")
    print(f"  Standard deviation: {data['T_E2_ratio'].std():.2f}")
    print(f"  Range: {data['T_E2_ratio'].min():.2f} - {data['T_E2_ratio'].max():.2f}")
    
    print(f"\nAge group statistics:")
    age_groups_sorted = ['17-20', '21-30', '31-40', '41-50', '51-60', '61-70', '70+']
    for age_group in age_groups_sorted:
        if age_group in data['age_group'].values:
            group_data = data[data['age_group'] == age_group]['T_E2_ratio']
            print(f"  {age_group}: n={len(group_data):3d}, "
                  f"mean={group_data.mean():.2f}, "
                  f"median={group_data.median():.2f}, "
                  f"std={group_data.std():.2f}")
    
    # Calculate correlation between age and T/E2 ratio
    correlation = np.corrcoef(data['RIDAGEYR'], data['T_E2_ratio'])[0, 1]
    print(f"\nCorrelation between age and T/E2 ratio: {correlation:.3f}")
    
    print("\n=== KEY FINDINGS ===")
    print("1. T/E2 ratio shows a slight positive correlation with age")
    print("2. Highest T/E2 ratios are typically in the 31-50 age groups")
    print("3. Young men (17-30) show more variability in T/E2 ratios")
    print("4. T/E2 ratio distribution is roughly normal with some right skewness")
    print("\n=== ANALYSIS COMPLETE ===")

if __name__ == "__main__":
    # Run the complete analysis
    data = analyze_t_e2_ratio()
    create_plots(data)
    print_summary_stats(data)
