#!/usr/bin/env python3
"""
Practical Comprehensive NHANES Correlation Analysis
Downloads actual data and computes real correlations for top variable candidates
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import pandas as pd
import numpy as np
from pandas_nhanes import get_cycle_variables, get_variables
import warnings
import json
from collections import defaultdict
warnings.filterwarnings('ignore')

# Constants
MIN_DATA_POINTS_FOR_TRANSFORMATION = 10
MIN_SAMPLE_SIZE = 30
MIN_OVERLAP_THRESHOLD = 0.1

# Prioritize these variable categories for interesting relationships
PRIORITY_CATEGORIES = {
    'laboratory': ['LBX', 'URX'],
    'body_measures': ['BMX'],
    'blood_pressure': ['BPX'],
    'dietary': ['DR1T', 'DR2T'],  # Total nutrients
    'mental_health': ['DPQ'],
    'sleep': ['SLD'],
    'alcohol': ['ALQ'],
    'smoking': ['SMQ'],
    'physical_activity': ['PAQ', 'PAD'],
}


def is_priority_variable(var_name):
    """Check if variable is in priority categories"""
    for category, prefixes in PRIORITY_CATEGORIES.items():
        if any(var_name.startswith(p) for p in prefixes):
            return True, category
    return False, 'other'


def is_obvious_relationship(var1, var2):
    """Check if two variables have an obvious expected relationship"""
    if var1 == var2:
        return True
    
    # Same prefix (likely related questions)
    if var1[:3] == var2[:3]:
        return True
    
    # Sequential numbers (e.g., DPQ010, DPQ020)
    if var1[:-2] == var2[:-2] and len(var1) == len(var2):
        return True
    
    return False


def select_variables_for_cycle(cycle_name, variables_df, n_per_category=10):
    """
    Smart variable selection: pick top N from each priority category
    """
    cycle_vars = variables_df[variables_df['cycle name'] == cycle_name].copy()
    
    selected = []
    for category, prefixes in PRIORITY_CATEGORIES.items():
        cat_vars = cycle_vars[
            cycle_vars['variable name'].apply(
                lambda x: any(x.startswith(p) for p in prefixes)
            )
        ]
        # Remove duplicates and administrative variables
        cat_vars = cat_vars[
            ~cat_vars['variable name'].str.contains('SEQN|CHECK', case=False, na=False)
        ]
        
        # Sample up to n_per_category
        if len(cat_vars) > n_per_category:
            sample = cat_vars.sample(n=n_per_category, random_state=42)
        else:
            sample = cat_vars
        
        selected.extend(sample['variable name'].tolist())
    
    return list(set(selected))  # Remove duplicates


def apply_transformations(series):
    """Apply non-linear transformations"""
    transformations = {'original': series}
    
    positive_mask = series > 0
    if positive_mask.sum() > MIN_DATA_POINTS_FOR_TRANSFORMATION:
        log_series = series.copy()
        log_series[positive_mask] = np.log(series[positive_mask])
        transformations['log'] = log_series
        
        sqrt_series = series.copy()
        sqrt_series[positive_mask] = np.sqrt(series[positive_mask])
        transformations['sqrt'] = sqrt_series
        
        transformations['square'] = series ** 2
        
        nonzero_mask = series != 0
        if nonzero_mask.sum() > MIN_DATA_POINTS_FOR_TRANSFORMATION:
            inv_series = series.copy()
            inv_series[nonzero_mask] = 1 / series[nonzero_mask]
            transformations['inverse'] = inv_series
    
    return transformations


def compute_correlations_for_cycle(cycle_name, var_list, variables_df):
    """
    Download data and compute correlations for a cycle
    
    NOTE: This requires internet access to download NHANES data
    """
    print(f"\n{'='*80}")
    print(f"PROCESSING CYCLE: {cycle_name}")
    print(f"{'='*80}")
    print(f"Variables to analyze: {len(var_list)}")
    
    try:
        # Download data
        print("Downloading data...")
        df = get_cycle_variables(cycle_name, *var_list)
        
        print(f"Downloaded {len(df)} rows")
        print(f"Valid data points: {df.notna().sum().sum()}")
        
        # Compute correlations
        results = []
        var_pairs_processed = 0
        
        for i, var1 in enumerate(var_list):
            for j, var2 in enumerate(var_list):
                if i >= j:
                    continue
                
                # Skip obvious relationships
                if is_obvious_relationship(var1, var2):
                    continue
                
                var_pairs_processed += 1
                
                # Get clean data
                subset = df[[var1, var2]].dropna()
                
                if len(subset) < MIN_SAMPLE_SIZE:
                    continue
                
                # Get variable info
                var1_info = variables_df[
                    (variables_df['cycle name'] == cycle_name) & 
                    (variables_df['variable name'] == var1)
                ]
                var2_info = variables_df[
                    (variables_df['cycle name'] == cycle_name) & 
                    (variables_df['variable name'] == var2)
                ]
                
                if var1_info.empty or var2_info.empty:
                    continue
                
                var1_info = var1_info.iloc[0]
                var2_info = var2_info.iloc[0]
                
                # Apply transformations
                trans1 = apply_transformations(subset[var1])
                trans2 = apply_transformations(subset[var2])
                
                # Compute correlations for all transformation combinations
                for t1_name, t1_data in trans1.items():
                    for t2_name, t2_data in trans2.items():
                        try:
                            valid_mask = ~(pd.isna(t1_data) | pd.isna(t2_data) | 
                                          np.isinf(t1_data) | np.isinf(t2_data))
                            
                            if valid_mask.sum() < MIN_SAMPLE_SIZE:
                                continue
                            
                            corr = np.corrcoef(t1_data[valid_mask], t2_data[valid_mask])[0, 1]
                            
                            if not np.isnan(corr):
                                is_priority1, cat1 = is_priority_variable(var1)
                                is_priority2, cat2 = is_priority_variable(var2)
                                
                                results.append({
                                    'cycle': cycle_name,
                                    'var1': var1,
                                    'var2': var2,
                                    'var1_desc': var1_info['variable explanation'],
                                    'var2_desc': var2_info['variable explanation'],
                                    'category1': cat1,
                                    'category2': cat2,
                                    'cross_category': cat1 != cat2,
                                    'transform1': t1_name,
                                    'transform2': t2_name,
                                    'correlation': corr,
                                    'abs_correlation': abs(corr),
                                    'n_samples': valid_mask.sum()
                                })
                        except (ValueError, RuntimeError, TypeError) as e:
                            # Skip correlation calculation if data types incompatible
                            continue
        
        print(f"Processed {var_pairs_processed} variable pairs")
        print(f"Computed {len(results)} correlations (with transformations)")
        
        return results
        
    except Exception as e:
        print(f"Error processing cycle {cycle_name}: {e}")
        return []


def rank_and_filter_results(all_results, top_n_per_transformation=100):
    """
    Rank results and extract top findings by transformation type
    """
    df = pd.DataFrame(all_results)
    
    if len(df) == 0:
        print("No results to rank")
        return {}
    
    print(f"\n{'='*80}")
    print("RANKING AND FILTERING RESULTS")
    print(f"{'='*80}")
    
    # Calculate improvement score for transformations
    original_corrs = df[
        (df['transform1'] == 'original') & 
        (df['transform2'] == 'original')
    ].set_index(['cycle', 'var1', 'var2'])['abs_correlation']
    
    df['original_correlation'] = df.apply(
        lambda row: original_corrs.get((row['cycle'], row['var1'], row['var2']), 0),
        axis=1
    )
    
    df['improvement'] = df['abs_correlation'] - df['original_correlation']
    
    # Filter for interesting relationships
    # 1. Cross-category with strong correlation
    # 2. Significant improvement with transformation
    # 3. Unexpected variable pairs
    
    interesting = df[
        (df['abs_correlation'] > 0.3) |  # Moderate+ correlation
        (df['improvement'] > 0.1) |  # Transformation reveals hidden pattern
        (df['cross_category'] == True)  # Cross-domain relationship
    ].copy()
    
    print(f"Filtered to {len(interesting)} interesting relationships")
    
    # Rank by transformation type
    ranked_by_transform = {}
    
    for transform_combo in interesting[['transform1', 'transform2']].drop_duplicates().values:
        t1, t2 = transform_combo
        key = f"{t1}_{t2}"
        
        subset = interesting[
            (interesting['transform1'] == t1) & 
            (interesting['transform2'] == t2)
        ].copy()
        
        # Sort by absolute correlation descending
        subset = subset.sort_values('abs_correlation', ascending=False)
        
        ranked_by_transform[key] = subset.head(top_n_per_transformation)
    
    return ranked_by_transform


def main():
    """
    Execute comprehensive analysis on selected cycles
    """
    print("="*80)
    print("COMPREHENSIVE NHANES CORRELATION ANALYSIS")
    print("Practical Implementation with Data Download")
    print("="*80)
    
    variables = get_variables()
    
    # Select cycles to analyze (can be configured)
    # Start with recent, well-populated cycles
    target_cycles = ['2015-2016', '2013-2014', '2011-2012']
    
    print(f"\nAnalyzing {len(target_cycles)} cycles: {', '.join(target_cycles)}")
    print("This will download real NHANES data and compute actual correlations.\n")
    
    all_results = []
    
    for cycle in target_cycles:
        # Select smart subset of variables
        var_list = select_variables_for_cycle(cycle, variables, n_per_category=10)
        
        print(f"\nCycle {cycle}: Selected {len(var_list)} variables")
        
        # Compute correlations
        cycle_results = compute_correlations_for_cycle(cycle, var_list, variables)
        all_results.extend(cycle_results)
        
        print(f"Accumulated {len(all_results)} total correlations so far")
    
    print(f"\n{'='*80}")
    print(f"ANALYSIS COMPLETE - {len(all_results)} total correlations computed")
    print(f"{'='*80}")
    
    if len(all_results) == 0:
        print("\nNo correlations computed. This may be due to:")
        print("- No internet access for data download")
        print("- Insufficient data overlap between variables")
        print("- API connection issues")
        return
    
    # Rank and filter
    ranked = rank_and_filter_results(all_results, top_n_per_transformation=50)
    
    # Save results by transformation type
    print(f"\n{'='*80}")
    print("SAVING RESULTS BY TRANSFORMATION TYPE")
    print(f"{'='*80}")
    
    summary = []
    for transform_key, df_subset in ranked.items():
        if len(df_subset) > 0:
            filename = f"top_correlations_{transform_key}.csv"
            df_subset.to_csv(filename, index=False)
            print(f"✓ {transform_key}: {len(df_subset)} relationships → {filename}")
            
            summary.append({
                'transformation': transform_key,
                'count': len(df_subset),
                'max_correlation': df_subset['abs_correlation'].max(),
                'mean_correlation': df_subset['abs_correlation'].mean()
            })
    
    # Generate summary report
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv("transformation_summary.csv", index=False)
    
    print(f"\n{'='*80}")
    print("TOP FINDINGS BY TRANSFORMATION TYPE")
    print(f"{'='*80}\n")
    print(summary_df.to_string(index=False))
    
    # Extract and display most interesting findings
    print(f"\n{'='*80}")
    print("MOST INTERESTING RELATIONSHIPS (TOP 10)")
    print(f"{'='*80}")
    
    all_interesting = pd.concat([df for df in ranked.values() if len(df) > 0])
    top_10 = all_interesting.nlargest(10, 'abs_correlation')
    
    for idx, row in top_10.iterrows():
        print(f"\n{row['var1']} ↔ {row['var2']}")
        print(f"  {row['var1_desc']}")
        print(f"  {row['var2_desc']}")
        print(f"  Correlation: {row['correlation']:.3f} "
              f"(transform: {row['transform1']}/{row['transform2']})")
        print(f"  Categories: {row['category1']} ↔ {row['category2']}")
        print(f"  Cycle: {row['cycle']}, n={row['n_samples']:,}")
    
    print(f"\n{'='*80}")
    print("✓ Analysis complete! Check CSV files for detailed results.")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
