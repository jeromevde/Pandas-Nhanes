#!/usr/bin/env python3
"""
Multi-Cycle Comprehensive Analysis
Analyzes ALL NHANES cycles and publishes top 20 strongest relationships for each
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import pandas as pd
import numpy as np
from pandas_nhanes import get_cycle_variables, get_variables
import warnings
warnings.filterwarnings('ignore')

# Constants
MIN_DATA_POINTS_FOR_TRANSFORMATION = 10
MIN_SAMPLE_SIZE = 30

# Enhanced obvious relationship detection
def is_obvious_relationship(var1, var2, var1_desc, var2_desc):
    """
    Detect obvious relationships that should be filtered out
    """
    # Same variable
    if var1 == var2:
        return True
    
    # Same prefix (likely related questions)
    if var1[:3] == var2[:3]:
        return True
    
    # Sequential numbers (e.g., DPQ010, DPQ020)
    if var1[:-2] == var2[:-2] and len(var1) == len(var2):
        return True
    
    # Common obvious patterns in descriptions
    obvious_patterns = [
        ('arm', 'leg'),  # Body measurements
        ('left', 'right'),  # Bilateral measurements
        ('1st', '2nd'), ('2nd', '3rd'), ('3rd', '4th'),  # Sequential readings
        ('systolic', 'diastolic'),  # BP measurements
        ('day 1', 'day 2'),  # Repeated measurements
    ]
    
    desc1_lower = var1_desc.lower()
    desc2_lower = var2_desc.lower()
    
    for pattern1, pattern2 in obvious_patterns:
        if (pattern1 in desc1_lower and pattern2 in desc2_lower) or \
           (pattern2 in desc1_lower and pattern1 in desc2_lower):
            # Only filter if they're from same category (e.g., both body measurements)
            if var1[:3] == var2[:3]:
                return True
    
    return False


def is_priority_variable(var_name):
    """Check if variable is in priority categories"""
    priority_prefixes = {
        'laboratory': ['LBX', 'URX'],
        'body_measures': ['BMX'],
        'blood_pressure': ['BPX'],
        'dietary': ['DR1T', 'DR2T'],
        'mental_health': ['DPQ'],
        'sleep': ['SLD'],
        'alcohol': ['ALQ'],
        'smoking': ['SMQ'],
        'physical_activity': ['PAQ', 'PAD'],
    }
    
    for category, prefixes in priority_prefixes.items():
        if any(var_name.startswith(p) for p in prefixes):
            return True, category
    return False, 'other'


def select_variables_for_cycle(cycle_name, variables_df, n_per_category=10):
    """Smart variable selection: pick top N from each priority category"""
    cycle_vars = variables_df[variables_df['cycle name'] == cycle_name].copy()
    
    priority_categories = {
        'laboratory': ['LBX', 'URX'],
        'body_measures': ['BMX'],
        'blood_pressure': ['BPX'],
        'dietary': ['DR1T', 'DR2T'],
        'mental_health': ['DPQ'],
        'sleep': ['SLD'],
        'alcohol': ['ALQ'],
        'smoking': ['SMQ'],
        'physical_activity': ['PAQ', 'PAD'],
    }
    
    selected = []
    for category, prefixes in priority_categories.items():
        cat_vars = cycle_vars[
            cycle_vars['variable name'].apply(
                lambda x: any(x.startswith(p) for p in prefixes)
            )
        ]
        cat_vars = cat_vars[
            ~cat_vars['variable name'].str.contains('SEQN|CHECK', case=False, na=False)
        ]
        
        if len(cat_vars) > n_per_category:
            sample = cat_vars.sample(n=n_per_category, random_state=42)
        else:
            sample = cat_vars
        
        selected.extend(sample['variable name'].tolist())
    
    return list(set(selected))


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


def analyze_single_cycle(cycle_name, var_list, variables_df):
    """Analyze a single NHANES cycle"""
    print(f"\n{'='*80}")
    print(f"ANALYZING CYCLE: {cycle_name}")
    print(f"{'='*80}")
    print(f"Variables to analyze: {len(var_list)}")
    
    try:
        # Download data - handle variable not found errors gracefully
        print("Downloading data...")
        df = None
        attempt_count = 0
        max_attempts = 3
        
        while df is None and attempt_count < max_attempts:
            try:
                df = get_cycle_variables(cycle_name, *var_list)
            except Exception as e:
                error_msg = str(e)
                # If specific variable not found, remove it and retry
                if "not in index" in error_msg or "not found" in error_msg.lower():
                    # Extract variable name from error
                    import re
                    match = re.search(r"\['([^']+)'\]", error_msg)
                    if match and len(var_list) > 2:
                        bad_var = match.group(1)
                        print(f"  Removing problematic variable: {bad_var}")
                        var_list = [v for v in var_list if v != bad_var]
                        attempt_count += 1
                    else:
                        raise
                else:
                    raise
        
        if df is None:
            print("Failed to download data after retries")
            return []
        
        print(f"Downloaded {len(df)} rows")
        
        # Compute correlations
        results = []
        var_pairs_processed = 0
        
        for i, var1 in enumerate(var_list):
            for j, var2 in enumerate(var_list):
                if i >= j:
                    continue
                
                var_pairs_processed += 1
                
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
                
                # Check for obvious relationship
                if is_obvious_relationship(var1, var2, 
                                          var1_info['variable explanation'],
                                          var2_info['variable explanation']):
                    continue
                
                # Get clean data
                subset = df[[var1, var2]].dropna()
                
                if len(subset) < MIN_SAMPLE_SIZE:
                    continue
                
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
                            continue
        
        print(f"Processed {var_pairs_processed} variable pairs")
        print(f"Computed {len(results)} correlations (with transformations)")
        
        return results
        
    except Exception as e:
        print(f"Error analyzing cycle {cycle_name}: {e}")
        return []


def main():
    """
    Execute comprehensive analysis on ALL NHANES cycles
    """
    print("="*80)
    print("MULTI-CYCLE NHANES CORRELATION ANALYSIS")
    print("Analyzing ALL cycles and extracting top 20 relationships per cycle")
    print("="*80)
    
    variables = get_variables()
    
    # Get all single-cycle data (not merged multi-cycle)
    all_cycles = sorted([c for c in variables['cycle name'].unique() 
                        if '-' in c and len(c.split('-')[0]) == 4])
    
    print(f"\nFound {len(all_cycles)} cycles to analyze")
    print("Cycles:", ', '.join(all_cycles))
    
    # Analyze each cycle
    all_cycle_results = {}
    
    for cycle in all_cycles:
        # Select variables
        var_list = select_variables_for_cycle(cycle, variables, n_per_category=10)
        
        if len(var_list) < 2:
            print(f"\nSkipping {cycle}: insufficient variables")
            continue
        
        print(f"\n{cycle}: Selected {len(var_list)} variables")
        
        # Analyze cycle
        cycle_results = analyze_single_cycle(cycle, var_list, variables)
        
        if len(cycle_results) > 0:
            all_cycle_results[cycle] = pd.DataFrame(cycle_results)
            print(f"✓ {cycle}: {len(cycle_results)} correlations computed")
        else:
            print(f"✗ {cycle}: No correlations computed")
    
    # Generate top 20 for each cycle
    print(f"\n{'='*80}")
    print("GENERATING TOP 20 STRONGEST RELATIONSHIPS PER CYCLE")
    print(f"{'='*80}")
    
    summary_report = []
    
    for cycle, df in all_cycle_results.items():
        # Get top 20 by absolute correlation (original/original only for main report)
        top_20 = df[
            (df['transform1'] == 'original') & 
            (df['transform2'] == 'original')
        ].nlargest(20, 'abs_correlation')
        
        if len(top_20) > 0:
            # Save to file
            filename = f"top_20_relationships_{cycle.replace('-', '_')}.csv"
            top_20.to_csv(filename, index=False)
            print(f"✓ {cycle}: {len(top_20)} relationships → {filename}")
            
            # Add to summary
            summary_report.append({
                'cycle': cycle,
                'relationships_found': len(df),
                'top_20_max_correlation': top_20['abs_correlation'].max(),
                'top_20_mean_correlation': top_20['abs_correlation'].mean(),
                'output_file': filename
            })
    
    # Save summary
    summary_df = pd.DataFrame(summary_report)
    summary_df.to_csv("multi_cycle_summary.csv", index=False)
    
    print(f"\n{'='*80}")
    print("SUMMARY OF ALL CYCLES")
    print(f"{'='*80}\n")
    print(summary_df.to_string(index=False))
    
    # Generate comprehensive markdown report
    generate_markdown_report(all_cycle_results, summary_df)
    
    print(f"\n{'='*80}")
    print("✓ Multi-cycle analysis complete!")
    print(f"  - Analyzed {len(all_cycle_results)} cycles")
    print(f"  - Generated {len(summary_report)} top-20 reports")
    print(f"  - See multi_cycle_summary.csv for overview")
    print(f"  - See TOP_20_RELATIONSHIPS_ALL_CYCLES.md for detailed report")
    print(f"{'='*80}\n")


def generate_markdown_report(all_cycle_results, summary_df):
    """Generate comprehensive markdown report with top 20 for each cycle"""
    
    report = []
    report.append("# Top 20 Strongest Relationships Per NHANES Cycle")
    report.append("\n**Analysis Date:** 2026-02-06")
    report.append(f"\n**Cycles Analyzed:** {len(all_cycle_results)}")
    report.append("\n**Note:** Obvious relationships (same variable family, bilateral measurements, sequential readings) have been filtered out.")
    report.append("\n---\n")
    
    # Summary table
    report.append("## Summary by Cycle\n")
    report.append("| Cycle | Relationships Found | Max Correlation | Mean Correlation | Output File |")
    report.append("|-------|---------------------|-----------------|------------------|-------------|")
    
    for _, row in summary_df.iterrows():
        report.append(f"| {row['cycle']} | {row['relationships_found']:,} | {row['top_20_max_correlation']:.3f} | {row['top_20_mean_correlation']:.3f} | {row['output_file']} |")
    
    report.append("\n---\n")
    
    # Detailed findings per cycle
    for cycle in sorted(all_cycle_results.keys()):
        df = all_cycle_results[cycle]
        
        # Get top 20 original correlations
        top_20 = df[
            (df['transform1'] == 'original') & 
            (df['transform2'] == 'original')
        ].nlargest(20, 'abs_correlation')
        
        if len(top_20) == 0:
            continue
        
        report.append(f"## {cycle}\n")
        report.append(f"**Total Correlations Computed:** {len(df):,}")
        report.append(f"\n**Top 20 Strongest Relationships (Linear):**\n")
        
        for idx, row in top_20.iterrows():
            rank = top_20.index.get_loc(idx) + 1
            direction = "positive" if row['correlation'] > 0 else "negative"
            cross = " 🌟 CROSS-DOMAIN" if row['cross_category'] else ""
            
            report.append(f"\n### {rank}. {row['var1']} ↔ {row['var2']}")
            report.append(f"- **{row['var1_desc']}**")
            report.append(f"- **{row['var2_desc']}**")
            report.append(f"- **Correlation:** r = {row['correlation']:.3f} ({direction})")
            report.append(f"- **Sample Size:** n = {row['n_samples']:,}")
            report.append(f"- **Categories:** {row['category1']} ↔ {row['category2']}{cross}")
        
        report.append("\n---\n")
    
    # Save report
    with open("TOP_20_RELATIONSHIPS_ALL_CYCLES.md", 'w') as f:
        f.write('\n'.join(report))


if __name__ == "__main__":
    main()
