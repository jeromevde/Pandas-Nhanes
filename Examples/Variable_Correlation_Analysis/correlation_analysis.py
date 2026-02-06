#!/usr/bin/env python3
"""
Variable Correlation Analysis
Analyzes relationships between 10 random NHANES variables using correlation metrics
and non-linear transformations to identify interesting patterns.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import pandas as pd
import numpy as np
from pandas_nhanes import get_cycle_variables, get_variables
import warnings
warnings.filterwarnings('ignore')

def select_numeric_variables(n=10, cycle="2015-2016"):
    """
    Select n random numeric variables from NHANES data
    Focus on health/lab measurements for interesting correlations
    """
    variables = get_variables()
    
    # Filter for specific cycle and common numeric variable patterns
    cycle_vars = variables[variables['cycle name'] == cycle].copy()
    
    # Prioritize lab measurements, demographics, and health indicators
    # Exclude administrative variables like SEQN, check items, etc.
    interesting_patterns = [
        'LBX',  # Laboratory measurements
        'BMX',  # Body measurements
        'BPX',  # Blood pressure
        'DR1',  # Dietary
        'RIDAGEYR',  # Age
        'INDFMPIR',  # Income
        'DPQ',  # Depression
        'SLD',  # Sleep
        'ALQ',  # Alcohol
        'SMQ',  # Smoking
        'PAQ',  # Physical activity
    ]
    
    # Filter variables that likely contain numeric data
    numeric_candidates = cycle_vars[
        cycle_vars['variable name'].str.contains('|'.join(interesting_patterns), case=False, na=False)
    ].copy()
    
    # Remove duplicates and check items
    numeric_candidates = numeric_candidates[
        ~numeric_candidates['variable name'].str.contains('CHECK|SEQN', case=False, na=False)
    ]
    
    # Sample random variables
    if len(numeric_candidates) > n:
        selected = numeric_candidates.sample(n=n, random_state=42)
    else:
        selected = numeric_candidates.head(n)
    
    return selected['variable name'].tolist(), cycle


def apply_transformations(series):
    """
    Apply various non-linear transformations to a series
    Returns dict of transformed series
    """
    transformations = {}
    
    # Original
    transformations['original'] = series
    
    # Only apply transformations to positive values
    positive_mask = series > 0
    
    if positive_mask.sum() > 10:  # Need enough data points
        # Log transform
        log_series = series.copy()
        log_series[positive_mask] = np.log(series[positive_mask])
        transformations['log'] = log_series
        
        # Square root
        sqrt_series = series.copy()
        sqrt_series[positive_mask] = np.sqrt(series[positive_mask])
        transformations['sqrt'] = sqrt_series
        
        # Square
        transformations['square'] = series ** 2
        
        # Inverse (for non-zero values)
        nonzero_mask = series != 0
        if nonzero_mask.sum() > 10:
            inv_series = series.copy()
            inv_series[nonzero_mask] = 1 / series[nonzero_mask]
            transformations['inverse'] = inv_series
    
    return transformations


def compute_correlation_matrix(df, variables):
    """
    Compute correlation matrix with various transformations
    """
    results = []
    
    print("\n" + "="*80)
    print("CORRELATION ANALYSIS")
    print("="*80)
    
    for i, var1 in enumerate(variables):
        for j, var2 in enumerate(variables):
            if i >= j:  # Skip diagonal and duplicates
                continue
            
            # Get clean data
            subset = df[[var1, var2]].dropna()
            
            if len(subset) < 30:  # Need minimum sample size
                continue
            
            # Apply transformations
            trans1 = apply_transformations(subset[var1])
            trans2 = apply_transformations(subset[var2])
            
            # Compute correlations for all transformation combinations
            for t1_name, t1_data in trans1.items():
                for t2_name, t2_data in trans2.items():
                    try:
                        # Get valid pairs
                        valid_mask = ~(pd.isna(t1_data) | pd.isna(t2_data) | 
                                      np.isinf(t1_data) | np.isinf(t2_data))
                        
                        if valid_mask.sum() < 30:
                            continue
                        
                        corr = np.corrcoef(t1_data[valid_mask], t2_data[valid_mask])[0, 1]
                        
                        if not np.isnan(corr):
                            results.append({
                                'var1': var1,
                                'var2': var2,
                                'transform1': t1_name,
                                'transform2': t2_name,
                                'correlation': corr,
                                'abs_correlation': abs(corr),
                                'n_samples': valid_mask.sum()
                            })
                    except:
                        continue
    
    return pd.DataFrame(results)


def analyze_results(corr_df, variables_info):
    """
    Analyze and report interesting findings
    """
    print("\n" + "="*80)
    print("TOP FINDINGS")
    print("="*80)
    
    # Sort by absolute correlation
    corr_df_sorted = corr_df.sort_values('abs_correlation', ascending=False)
    
    # Find interesting patterns
    print("\n1. STRONGEST LINEAR CORRELATIONS (Original variables):")
    print("-" * 80)
    linear = corr_df_sorted[
        (corr_df_sorted['transform1'] == 'original') & 
        (corr_df_sorted['transform2'] == 'original')
    ].head(10)
    
    for idx, row in linear.iterrows():
        var1_info = variables_info[variables_info['variable name'] == row['var1']].iloc[0]
        var2_info = variables_info[variables_info['variable name'] == row['var2']].iloc[0]
        print(f"\n{row['var1']} vs {row['var2']}")
        print(f"  • {var1_info['variable explanation']}")
        print(f"  • {var2_info['variable explanation']}")
        print(f"  • Correlation: {row['correlation']:.3f} (n={row['n_samples']:,})")
    
    # Find transformations that reveal hidden relationships
    print("\n\n2. HIDDEN RELATIONSHIPS REVEALED BY TRANSFORMATIONS:")
    print("-" * 80)
    
    # Find pairs where transformation significantly improves correlation
    for var_pair in corr_df[['var1', 'var2']].drop_duplicates().values[:20]:
        var1, var2 = var_pair
        pair_corrs = corr_df[
            (corr_df['var1'] == var1) & (corr_df['var2'] == var2)
        ].copy()
        
        if len(pair_corrs) > 1:
            original_corr = pair_corrs[
                (pair_corrs['transform1'] == 'original') & 
                (pair_corrs['transform2'] == 'original')
            ]['abs_correlation'].values
            
            if len(original_corr) > 0:
                original_corr = original_corr[0]
                max_transformed = pair_corrs[
                    ~((pair_corrs['transform1'] == 'original') & 
                      (pair_corrs['transform2'] == 'original'))
                ]['abs_correlation'].max()
                
                improvement = max_transformed - original_corr
                
                # Report if transformation reveals >0.1 stronger correlation
                if improvement > 0.1 and max_transformed > 0.3:
                    best_trans = pair_corrs.loc[pair_corrs['abs_correlation'].idxmax()]
                    var1_info = variables_info[variables_info['variable name'] == var1].iloc[0]
                    var2_info = variables_info[variables_info['variable name'] == var2].iloc[0]
                    
                    print(f"\n{var1} vs {var2}")
                    print(f"  • {var1_info['variable explanation']}")
                    print(f"  • {var2_info['variable explanation']}")
                    print(f"  • Original correlation: {original_corr:.3f}")
                    print(f"  • Best with {best_trans['transform1']}/{best_trans['transform2']}: "
                          f"{best_trans['correlation']:.3f}")
                    print(f"  • Improvement: +{improvement:.3f}")
    
    # Look for unexpected relationships
    print("\n\n3. UNEXPECTED RELATIONSHIPS (different domains):")
    print("-" * 80)
    
    # Define variable categories
    categories = {
        'lab': ['LBX'],
        'body': ['BMX'],
        'blood_pressure': ['BPX'],
        'diet': ['DR1'],
        'demographic': ['RIDAGEYR', 'INDFMPIR'],
        'mental_health': ['DPQ'],
        'sleep': ['SLD'],
        'alcohol': ['ALQ'],
        'smoking': ['SMQ'],
        'activity': ['PAQ']
    }
    
    def get_category(var_name):
        for cat, patterns in categories.items():
            if any(p in var_name for p in patterns):
                return cat
        return 'other'
    
    # Find cross-category correlations
    cross_category = corr_df_sorted[
        (corr_df_sorted['transform1'] == 'original') & 
        (corr_df_sorted['transform2'] == 'original')
    ].copy()
    
    cross_category['cat1'] = cross_category['var1'].apply(get_category)
    cross_category['cat2'] = cross_category['var2'].apply(get_category)
    cross_category = cross_category[cross_category['cat1'] != cross_category['cat2']]
    
    for idx, row in cross_category.head(10).iterrows():
        var1_info = variables_info[variables_info['variable name'] == row['var1']].iloc[0]
        var2_info = variables_info[variables_info['variable name'] == row['var2']].iloc[0]
        print(f"\n{row['var1']} ({row['cat1']}) vs {row['var2']} ({row['cat2']})")
        print(f"  • {var1_info['variable explanation']}")
        print(f"  • {var2_info['variable explanation']}")
        print(f"  • Correlation: {row['correlation']:.3f} (n={row['n_samples']:,})")
    
    return corr_df_sorted


def main():
    print("="*80)
    print("NHANES VARIABLE CORRELATION ANALYSIS")
    print("Analyzing 10x10 variables = 100 correlation pairs")
    print("="*80)
    
    # Select variables
    print("\nSelecting random numeric variables...")
    var_names, cycle = select_numeric_variables(n=10)
    
    # Get variable metadata
    variables_info = get_variables()
    selected_info = variables_info[
        (variables_info['variable name'].isin(var_names)) & 
        (variables_info['cycle name'] == cycle)
    ]
    
    print(f"\nSelected variables from cycle {cycle}:")
    for idx, row in selected_info.iterrows():
        print(f"  • {row['variable name']}: {row['variable explanation']}")
    
    # Download data
    print(f"\nDownloading data for {len(var_names)} variables...")
    df = get_cycle_variables(cycle, *var_names)
    
    print(f"\nData shape: {df.shape}")
    print(f"Variables with data: {df.notna().sum().sum():,} values")
    
    # Compute correlations
    print("\nComputing correlations with transformations...")
    corr_results = compute_correlation_matrix(df, var_names)
    
    print(f"\nComputed {len(corr_results):,} correlation combinations")
    
    # Analyze and report
    results = analyze_results(corr_results, selected_info)
    
    # Save results
    output_file = "correlation_analysis_results.csv"
    results.to_csv(output_file, index=False)
    print(f"\n\n{'='*80}")
    print(f"Full results saved to: {output_file}")
    print(f"{'='*80}\n")
    
    return results


if __name__ == "__main__":
    main()
