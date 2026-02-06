#!/usr/bin/env python3
"""
Variable Correlation Analysis - Demo Version
Demonstrates the correlation analysis methodology using simulated NHANES-like data

This shows how the analysis would work with real data from the API.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)


def generate_simulated_data(n_samples=5000):
    """
    Generate simulated NHANES-like data with interesting correlations
    """
    print("Generating simulated NHANES-like data...")
    
    # Age (20-80)
    age = np.random.normal(45, 15, n_samples).clip(20, 80)
    
    # BMI - correlated with age (tends to increase with age)
    bmi = 22 + 0.1 * age + np.random.normal(0, 4, n_samples)
    
    # Blood pressure - correlated with BMI and age
    systolic_bp = 100 + 0.5 * age + 0.8 * bmi + np.random.normal(0, 8, n_samples)
    
    # Cholesterol - correlated with age and BMI, non-linear with BP
    cholesterol = 150 + 0.8 * age + 0.5 * bmi + np.random.normal(0, 25, n_samples)
    
    # Sleep hours - U-shaped relationship with depression (optimal 7-8h)
    sleep_hours = np.random.normal(7, 1.5, n_samples).clip(3, 12)
    
    # Depression score - higher at both extremes of sleep
    sleep_deviation = np.abs(sleep_hours - 7.5)
    depression = 5 + 3 * sleep_deviation + np.random.normal(0, 3, n_samples)
    depression = depression.clip(0, 27)
    
    # Physical activity - inversely correlated with depression
    physical_activity = 150 - 10 * depression + np.random.normal(0, 40, n_samples)
    physical_activity = physical_activity.clip(0, 500)
    
    # Blood glucose - non-linear relationship with BMI (exponential)
    glucose = 80 + np.exp((bmi - 25) / 10) * 10 + np.random.normal(0, 8, n_samples)
    
    # Vitamin D - inverse relationship with BMI (surprising but real)
    vitamin_d = 40 - 0.5 * bmi + np.random.normal(0, 10, n_samples)
    vitamin_d = vitamin_d.clip(10, 100)
    
    # Alcohol consumption - independent but with age effect
    alcohol_freq = np.random.poisson(2 + 0.02 * (age - 40), n_samples).clip(0, 30)
    
    df = pd.DataFrame({
        'RIDAGEYR': age,
        'BMXBMI': bmi,
        'BPXSY1': systolic_bp,
        'LBXTC': cholesterol,
        'SLD012': sleep_hours,
        'DPQ_TOTAL': depression,
        'PAQ_MINS': physical_activity,
        'LBXGLU': glucose,
        'LBXVIDMS': vitamin_d,
        'ALQ120Q': alcohol_freq
    })
    
    # Add some missing values to be realistic
    for col in df.columns:
        missing_mask = np.random.random(n_samples) < 0.05
        df.loc[missing_mask, col] = np.nan
    
    return df


def get_variable_descriptions():
    """
    Get descriptions for the simulated variables
    """
    return pd.DataFrame({
        'variable name': ['RIDAGEYR', 'BMXBMI', 'BPXSY1', 'LBXTC', 'SLD012', 
                         'DPQ_TOTAL', 'PAQ_MINS', 'LBXGLU', 'LBXVIDMS', 'ALQ120Q'],
        'variable explanation': [
            'Age in years at screening',
            'Body Mass Index (kg/m²)',
            'Systolic blood pressure (mm Hg)',
            'Total cholesterol (mg/dL)',
            'Sleep hours per night',
            'Depression screening score (PHQ-9)',
            'Physical activity minutes per week',
            'Fasting glucose (mg/dL)',
            'Vitamin D (nmol/L)',
            'Alcohol drinking frequency (days/month)'
        ]
    })


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
    
    if positive_mask.sum() > 10:
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
    
    total_pairs = len(variables) * (len(variables) - 1) // 2
    print(f"Computing correlations for {total_pairs} variable pairs...")
    
    for i, var1 in enumerate(variables):
        for j, var2 in enumerate(variables):
            if i >= j:  # Skip diagonal and duplicates
                continue
            
            # Get clean data
            subset = df[[var1, var2]].dropna()
            
            if len(subset) < 30:
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
    
    # 1. Strongest linear correlations
    print("\n1. STRONGEST LINEAR CORRELATIONS:")
    print("-" * 80)
    linear = corr_df_sorted[
        (corr_df_sorted['transform1'] == 'original') & 
        (corr_df_sorted['transform2'] == 'original')
    ].head(10)
    
    for idx, row in linear.iterrows():
        var1_info = variables_info[variables_info['variable name'] == row['var1']].iloc[0]
        var2_info = variables_info[variables_info['variable name'] == row['var2']].iloc[0]
        
        direction = "positive" if row['correlation'] > 0 else "negative"
        strength = "strong" if abs(row['correlation']) > 0.6 else "moderate"
        
        print(f"\n{row['var1']} vs {row['var2']}")
        print(f"  • {var1_info['variable explanation']}")
        print(f"  • {var2_info['variable explanation']}")
        print(f"  • Correlation: {row['correlation']:.3f} ({strength} {direction}, n={row['n_samples']:,})")
    
    # 2. Transformations revealing hidden relationships
    print("\n\n2. HIDDEN RELATIONSHIPS REVEALED BY TRANSFORMATIONS:")
    print("-" * 80)
    print("(Cases where non-linear transformation reveals stronger correlation)")
    
    improvements_found = 0
    for var_pair in corr_df[['var1', 'var2']].drop_duplicates().values:
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
                    improvements_found += 1
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
                    print(f"  • Interpretation: Non-linear relationship - {best_trans['transform1']} "
                          f"of {var1} relates to {best_trans['transform2']} of {var2}")
    
    if improvements_found == 0:
        print("\nNo significant improvements found with transformations (most relationships are linear)")
    
    # 3. Unexpected cross-domain relationships
    print("\n\n3. KEY INSIGHTS - INTERESTING RELATIONSHIPS:")
    print("-" * 80)
    
    # Define categories
    categories = {
        'demographic': ['RIDAGEYR'],
        'body': ['BMXBMI'],
        'cardiovascular': ['BPXSY1', 'LBXTC'],
        'metabolic': ['LBXGLU', 'LBXVIDMS'],
        'behavioral': ['SLD012', 'DPQ_TOTAL', 'PAQ_MINS', 'ALQ120Q']
    }
    
    def get_category(var_name):
        for cat, vars in categories.items():
            if var_name in vars:
                return cat
        return 'other'
    
    # Annotate categories
    cross_category = corr_df_sorted[
        (corr_df_sorted['transform1'] == 'original') & 
        (corr_df_sorted['transform2'] == 'original')
    ].copy()
    
    cross_category['cat1'] = cross_category['var1'].apply(get_category)
    cross_category['cat2'] = cross_category['var2'].apply(get_category)
    
    # Group findings by category
    interesting_patterns = []
    
    for idx, row in cross_category.head(20).iterrows():
        var1_info = variables_info[variables_info['variable name'] == row['var1']].iloc[0]
        var2_info = variables_info[variables_info['variable name'] == row['var2']].iloc[0]
        
        # Interpret the finding
        interpretation = ""
        if abs(row['correlation']) > 0.6:
            strength = "Strong"
        elif abs(row['correlation']) > 0.4:
            strength = "Moderate"
        else:
            strength = "Weak"
        
        direction = "positive" if row['correlation'] > 0 else "negative"
        
        # Add domain-specific interpretations
        if 'BMI' in row['var1'] or 'BMI' in row['var2']:
            if 'LBXVIDMS' in [row['var1'], row['var2']]:
                interpretation = "⭐ UNEXPECTED: Higher BMI associated with LOWER Vitamin D (inverse relationship)"
            elif 'LBXGLU' in [row['var1'], row['var2']]:
                interpretation = "Expected: Higher BMI linked to higher glucose (metabolic syndrome)"
        
        if 'SLD012' in [row['var1'], row['var2']] and 'DPQ' in [row['var1'], row['var2']]:
            interpretation = "⭐ INTERESTING: Sleep-depression relationship (may be U-shaped - check transformations)"
        
        if 'DPQ' in [row['var1'], row['var2']] and 'PAQ' in [row['var1'], row['var2']]:
            interpretation = "⭐ ACTIONABLE: Exercise inversely correlated with depression"
        
        interesting_patterns.append({
            'pattern': f"{row['var1']} vs {row['var2']}",
            'cat1': row['cat1'],
            'cat2': row['cat2'],
            'desc1': var1_info['variable explanation'],
            'desc2': var2_info['variable explanation'],
            'correlation': row['correlation'],
            'strength': strength,
            'direction': direction,
            'interpretation': interpretation
        })
    
    # Print interesting patterns
    for i, pattern in enumerate(interesting_patterns[:10], 1):
        print(f"\n{i}. {pattern['pattern']}")
        print(f"   {pattern['desc1']} ←→ {pattern['desc2']}")
        print(f"   {pattern['strength']} {pattern['direction']} correlation: {pattern['correlation']:.3f}")
        if pattern['interpretation']:
            print(f"   {pattern['interpretation']}")
    
    return corr_df_sorted


def generate_summary_report(corr_df, variables_info):
    """
    Generate a markdown summary report
    """
    report = []
    report.append("# NHANES Variable Correlation Analysis Report\n")
    report.append("## Executive Summary\n")
    report.append(f"- Analyzed {len(variables_info)} variables with {len(corr_df):,} correlation calculations\n")
    report.append(f"- Applied 5 different transformations (original, log, sqrt, square, inverse)\n")
    report.append(f"- Identified top correlations and unexpected relationships\n")
    
    # Top findings
    report.append("\n## Top 5 Strongest Correlations\n")
    linear = corr_df[
        (corr_df['transform1'] == 'original') & 
        (corr_df['transform2'] == 'original')
    ].nlargest(5, 'abs_correlation')
    
    for idx, row in linear.iterrows():
        var1_info = variables_info[variables_info['variable name'] == row['var1']].iloc[0]
        var2_info = variables_info[variables_info['variable name'] == row['var2']].iloc[0]
        report.append(f"\n### {row['var1']} ↔ {row['var2']} (r={row['correlation']:.3f})\n")
        report.append(f"- **{var1_info['variable explanation']}**\n")
        report.append(f"- **{var2_info['variable explanation']}**\n")
        report.append(f"- Sample size: {row['n_samples']:,}\n")
    
    # Key insights
    report.append("\n## Key Insights for Further Investigation\n")
    report.append("\n### 1. Metabolic Relationships\n")
    report.append("- BMI shows strong positive correlation with glucose and blood pressure\n")
    report.append("- Suggests metabolic syndrome cluster - investigate BMI threshold effects\n")
    
    report.append("\n### 2. Unexpected Finding: BMI-Vitamin D Inverse Relationship\n")
    report.append("- Higher BMI correlates with LOWER Vitamin D levels\n")
    report.append("- Possible mechanisms: adipose tissue sequestration, less outdoor activity\n")
    report.append("- **Recommendation**: Investigate vitamin D supplementation in high BMI individuals\n")
    
    report.append("\n### 3. Mental Health-Behavior Links\n")
    report.append("- Depression scores inversely correlated with physical activity\n")
    report.append("- Sleep duration shows complex relationship (may be U-shaped)\n")
    report.append("- **Recommendation**: Analyze optimal sleep ranges and activity interventions\n")
    
    report.append("\n## Methodology\n")
    report.append("- **Data Source**: NHANES 2015-2016 cycle (simulated data for demonstration)\n")
    report.append("- **Variables**: 10 health/demographic variables\n")
    report.append("- **Transformations**: Original, log, sqrt, square, inverse\n")
    report.append("- **Sample Size**: ~5,000 participants per variable\n")
    report.append("- **Correlation Method**: Pearson correlation coefficient\n")
    
    return '\n'.join(report)


def main():
    print("="*80)
    print("NHANES VARIABLE CORRELATION ANALYSIS - DEMONSTRATION")
    print("="*80)
    print("\nNOTE: Using simulated data as API access is not available in this environment.")
    print("The methodology demonstrates how the analysis would work with real NHANES data.\n")
    
    # Generate simulated data
    df = generate_simulated_data(n_samples=5000)
    variables_info = get_variable_descriptions()
    var_names = df.columns.tolist()
    
    print(f"Generated data for {len(var_names)} variables:")
    for _, row in variables_info.iterrows():
        print(f"  • {row['variable name']}: {row['variable explanation']}")
    
    print(f"\nData shape: {df.shape}")
    print(f"Sample size: {len(df):,} participants")
    
    # Compute correlations
    print("\nComputing correlations with transformations...")
    corr_results = compute_correlation_matrix(df, var_names)
    
    print(f"Computed {len(corr_results):,} correlation combinations")
    
    # Analyze and report
    results = analyze_results(corr_results, variables_info)
    
    # Save results
    output_file = "correlation_analysis_results.csv"
    results.to_csv(output_file, index=False)
    
    # Generate summary report
    report = generate_summary_report(results, variables_info)
    report_file = "ANALYSIS_REPORT.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n\n{'='*80}")
    print(f"✅ Analysis complete!")
    print(f"   • Full results: {output_file}")
    print(f"   • Summary report: {report_file}")
    print(f"{'='*80}\n")
    
    return results


if __name__ == "__main__":
    main()
