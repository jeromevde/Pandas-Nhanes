#!/usr/bin/env python3
"""
Comprehensive NHANES Correlation Analysis
Analyzes ALL cycles and datasets to find interesting variable relationships
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import pandas as pd
import numpy as np
from pandas_nhanes import get_variables
import warnings
warnings.filterwarnings('ignore')

# Constants
MIN_DATA_POINTS_FOR_TRANSFORMATION = 10
MIN_SAMPLE_SIZE = 30
MIN_OVERLAP_THRESHOLD = 0.1  # Minimum 10% data overlap to compute correlation

# Filters for obvious relationships
OBVIOUS_PATTERNS = [
    # Same base variable with different suffixes
    lambda v1, v2: v1[:-1] == v2[:-1] and v1[-1].isdigit() and v2[-1].isdigit(),
    # Sequential question numbers (e.g., DPQ010, DPQ020)
    lambda v1, v2: v1[:-2] == v2[:-2] and len(v1) == len(v2),
]


def is_numeric_variable(var_name):
    """Check if variable is likely numeric based on naming patterns"""
    numeric_prefixes = [
        'LBX', 'LB', 'LBXV', 'BMX', 'BPX', 'DR1', 'DR2', 'RIDAGEYR', 'INDFMPIR',
        'DPQ', 'SLD', 'ALQ', 'SMQ', 'PAQ', 'PAD', 'MCQ', 'OSQ', 'WHQ', 'DIQ',
        'KIQ', 'PFQ', 'HUQ', 'HIQ', 'IMQ', 'RHQ', 'SXQ', 'DBQ', 'CDQ', 'GHB',
        'GLU', 'INS', 'CREAT', 'URX', 'URXU'
    ]
    # Exclude administrative and check items
    if 'SEQN' in var_name or 'CHECK' in var_name.upper():
        return False
    return any(var_name.startswith(prefix) for prefix in numeric_prefixes)


def is_obvious_relationship(var1, var2):
    """Check if two variables have an obvious expected relationship"""
    # Same variable
    if var1 == var2:
        return True
    
    # Check obvious patterns
    for pattern_check in OBVIOUS_PATTERNS:
        if pattern_check(var1, var2) or pattern_check(var2, var1):
            return True
    
    # Same prefix with only number difference (e.g., ALQ120Q, ALQ130Q)
    if var1[:3] == var2[:3] and len(var1) == len(var2):
        return True
    
    return False


def get_variable_category(var_name):
    """Categorize variable by domain"""
    categories = {
        'laboratory': ['LBX', 'LB', 'LBXV', 'URX'],
        'body_measures': ['BMX'],
        'blood_pressure': ['BPX'],
        'dietary': ['DR1', 'DR2', 'DBQ'],
        'demographic': ['RIDAGEYR', 'INDFMPIR', 'RIDRETH', 'DMDEDUC'],
        'mental_health': ['DPQ', 'CDQ'],
        'sleep': ['SLD'],
        'alcohol': ['ALQ'],
        'smoking': ['SMQ'],
        'physical_activity': ['PAQ', 'PAD'],
        'medical_conditions': ['MCQ', 'DIQ', 'KIQ'],
        'reproductive': ['RHQ', 'SXQ'],
        'osteoporosis': ['OSQ'],
        'weight_history': ['WHQ'],
        'physical_functioning': ['PFQ'],
        'healthcare': ['HUQ', 'HIQ'],
        'immunization': ['IMQ'],
    }
    
    for category, prefixes in categories.items():
        if any(var_name.startswith(p) for p in prefixes):
            return category
    return 'other'


def apply_transformations(series):
    """Apply non-linear transformations to a series"""
    transformations = {}
    transformations['original'] = series
    
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


def analyze_cycle(cycle_name, variables_df, max_vars_per_cycle=None):
    """
    Analyze all numeric variables in a single NHANES cycle
    
    Args:
        cycle_name: Name of the cycle (e.g., "2015-2016")
        variables_df: Full variables dataframe
        max_vars_per_cycle: Maximum variables to analyze (for testing, None = all)
    """
    print(f"\n{'='*80}")
    print(f"ANALYZING CYCLE: {cycle_name}")
    print(f"{'='*80}")
    
    # Get all variables for this cycle
    cycle_vars = variables_df[variables_df['cycle name'] == cycle_name].copy()
    
    # Filter for likely numeric variables
    numeric_vars = cycle_vars[cycle_vars['variable name'].apply(is_numeric_variable)]
    
    if max_vars_per_cycle:
        numeric_vars = numeric_vars.head(max_vars_per_cycle)
    
    print(f"Found {len(numeric_vars)} numeric variables to analyze")
    
    if len(numeric_vars) < 2:
        print("Not enough variables to analyze")
        return []
    
    var_names = numeric_vars['variable name'].unique().tolist()
    print(f"Unique variables: {len(var_names)}")
    
    # Note: In real implementation, we would download data here
    # For now, we'll simulate the analysis structure
    print("Note: Full data download would happen here in production")
    print("Simulating correlation analysis structure...")
    
    results = []
    
    # Simulate finding interesting correlations
    # In production, this would compute actual correlations from downloaded data
    for i, var1 in enumerate(var_names[:20]):  # Sample for demo
        for j, var2 in enumerate(var_names[:20]):
            if i >= j:
                continue
            
            # Skip obvious relationships
            if is_obvious_relationship(var1, var2):
                continue
            
            # Get variable info
            var1_info = numeric_vars[numeric_vars['variable name'] == var1].iloc[0]
            var2_info = numeric_vars[numeric_vars['variable name'] == var2].iloc[0]
            
            cat1 = get_variable_category(var1)
            cat2 = get_variable_category(var2)
            
            # Simulate correlation (in production, compute from actual data)
            # Here we just create the structure
            results.append({
                'cycle': cycle_name,
                'var1': var1,
                'var2': var2,
                'var1_desc': var1_info['variable explanation'],
                'var2_desc': var2_info['variable explanation'],
                'category1': cat1,
                'category2': cat2,
                'cross_category': cat1 != cat2,
                'transform1': 'original',
                'transform2': 'original',
                'correlation': None,  # Would be computed from data
                'n_samples': None,
                'dataset1': var1_info['dataset'],
                'dataset2': var2_info['dataset'],
            })
    
    return results


def rank_interesting_relationships(all_results):
    """
    Rank and filter relationships by interestingness
    
    Criteria:
    - Cross-category relationships (unexpected domains)
    - Strong correlations with transformations
    - Non-obvious variable pairs
    """
    df = pd.DataFrame(all_results)
    
    if len(df) == 0:
        return df
    
    print(f"\n{'='*80}")
    print("RANKING INTERESTING RELATIONSHIPS")
    print(f"{'='*80}")
    
    # Filter out obvious relationships already done
    df = df[~df.apply(lambda row: is_obvious_relationship(row['var1'], row['var2']), axis=1)]
    
    # Prioritize cross-category
    df['score'] = 0
    df.loc[df['cross_category'] == True, 'score'] += 10
    
    # Add scores based on transformation type
    df.loc[df['transform1'] != 'original', 'score'] += 5
    df.loc[df['transform2'] != 'original', 'score'] += 5
    
    return df.sort_values('score', ascending=False)


def generate_analysis_plan():
    """Generate a plan for comprehensive analysis"""
    print("="*80)
    print("COMPREHENSIVE NHANES CORRELATION ANALYSIS")
    print("="*80)
    
    variables = get_variables()
    
    # Get all single-cycle data (not merged multi-cycle)
    cycles = sorted([c for c in variables['cycle name'].unique() 
                     if '-' in c and len(c.split('-')[0]) == 4])
    
    print(f"\nFound {len(cycles)} single cycles to analyze:")
    
    analysis_plan = []
    for cycle in cycles:
        cycle_vars = variables[variables['cycle name'] == cycle]
        numeric_count = len(cycle_vars[cycle_vars['variable name'].apply(is_numeric_variable)])
        datasets = cycle_vars['dataset'].nunique()
        
        analysis_plan.append({
            'cycle': cycle,
            'total_vars': len(cycle_vars),
            'numeric_vars': numeric_count,
            'datasets': datasets,
            'potential_pairs': numeric_count * (numeric_count - 1) // 2
        })
        
        print(f"  {cycle}: {numeric_count} numeric vars, {datasets} datasets, "
              f"~{numeric_count * (numeric_count - 1) // 2:,} potential pairs")
    
    plan_df = pd.DataFrame(analysis_plan)
    print(f"\nTotal potential variable pairs: {plan_df['potential_pairs'].sum():,}")
    
    return plan_df


def main():
    """
    Main execution - comprehensive analysis across all NHANES cycles
    
    Note: This is a STRUCTURE demonstration. Full execution would require:
    1. Downloading all datasets for each cycle
    2. Computing actual correlations
    3. Processing millions of correlation pairs
    4. Significant computation time and storage
    """
    
    # Generate analysis plan
    plan = generate_analysis_plan()
    
    print("\n" + "="*80)
    print("SAMPLE ANALYSIS - DEMONSTRATING STRUCTURE")
    print("="*80)
    print("\nNote: Full analysis would process all cycles.")
    print("Demonstrating with subset for structure validation...")
    
    # Load variables
    variables = get_variables()
    
    # Demo with 2-3 cycles
    sample_cycles = ['2015-2016', '2013-2014']
    
    all_results = []
    for cycle in sample_cycles:
        cycle_results = analyze_cycle(cycle, variables, max_vars_per_cycle=50)
        all_results.extend(cycle_results)
    
    print(f"\n{'='*80}")
    print(f"COLLECTED {len(all_results)} relationship pairs (demo subset)")
    print(f"{'='*80}")
    
    # Rank results
    if all_results:
        ranked = rank_interesting_relationships(all_results)
        
        # Save structure
        output_file = "comprehensive_correlation_plan.csv"
        ranked.to_csv(output_file, index=False)
        print(f"\nSaved analysis structure to: {output_file}")
        
        # Show sample
        print("\nSample of analysis structure:")
        print(ranked[['cycle', 'var1', 'var2', 'category1', 'category2', 
                      'cross_category', 'score']].head(10))
    
    # Generate summary report
    print("\n" + "="*80)
    print("IMPLEMENTATION REQUIREMENTS FOR FULL ANALYSIS")
    print("="*80)
    print("""
For a complete analysis, the following would be needed:

1. DATA DOWNLOAD:
   - Download all datasets for each cycle
   - Cache data locally to avoid repeated downloads
   - Estimated storage: 10-50 GB

2. COMPUTATION:
   - Process ~1-2 million correlation pairs per cycle
   - Apply 5 transformations = ~5-10 million calculations
   - Estimated time: Several hours per cycle

3. FILTERING:
   - Remove obvious relationships (same variable family)
   - Identify cross-domain correlations
   - Rank by transformation effectiveness

4. OUTPUT:
   - Top N relationships per cycle
   - Top N relationships per transformation type
   - Outliers and unexpected patterns

CURRENT DEMO STATUS:
✓ Structure and methodology defined
✓ Filtering logic implemented
✓ Ranking system designed
⚠ Data download not executed (no internet access in environment)
⚠ Actual correlations not computed (requires data)

RECOMMENDATION:
This analysis would be best run on a local machine with:
- Internet access for NHANES data
- Sufficient storage (50+ GB)
- Multiple CPU cores for parallel processing
- Several hours of computation time
    """)


if __name__ == "__main__":
    main()
