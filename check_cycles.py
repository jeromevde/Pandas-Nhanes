#!/usr/bin/env python3
"""
Script to check for missing NHANES cycles in the dataset.
This helps identify which cohorts or years are incomplete.
"""

import pandas as pd
import os

def check_cycles():
    """Check which NHANES cycles are present or missing."""
    
    # Expected NHANES continuous cycles (every 2 years starting 1999-2000)
    # Note: 2019-2020 was disrupted by COVID-19 and combined into 2017-2020
    expected_continuous_cycles = [
        "1999-2000", "2001-2002", "2003-2004", "2005-2006", "2007-2008",
        "2009-2010", "2011-2012", "2013-2014", "2015-2016", "2017-2018"
    ]
    
    # Special/Combined cycles
    special_cycles = [
        "2017-2020",  # Pre-pandemic combined data (includes 2017-2018 and partial 2019-2020)
        "2021-2023"   # COVID-19 pandemic data collection
    ]
    
    # Note about 2019-2020
    covid_note = """
    
    ℹ️  NOTE: The 2019-2020 cycle was disrupted by COVID-19.
       Data collected before March 2020 was combined with 2017-2018
       into the '2017-2020' pre-pandemic cycle.
    """
    
    # Read current data
    csv_path = os.path.join(os.path.dirname(__file__), 'pandas_nhanes', 'nhanes_variables.csv')
    df = pd.read_csv(csv_path)
    current_cycles = set([c for c in df['cycle name'].unique() if '-' in c])
    
    # Report findings
    print("=" * 70)
    print("NHANES Dataset Cycle Coverage Report")
    print("=" * 70)
    
    print("\n📊 Expected Continuous NHANES Cycles (biennial):")
    print("-" * 70)
    missing_continuous = []
    for cycle in expected_continuous_cycles:
        if cycle in current_cycles:
            dataset_count = len(df[df['cycle name'] == cycle]['dataset'].unique())
            print(f"  ✓ {cycle}: Present ({dataset_count} datasets)")
        else:
            print(f"  ✗ {cycle}: MISSING")
            missing_continuous.append(cycle)
    
    print("\n📊 Special/Combined Cycles:")
    print("-" * 70)
    missing_special = []
    for cycle in special_cycles:
        if cycle in current_cycles:
            dataset_count = len(df[df['cycle name'] == cycle]['dataset'].unique())
            print(f"  ✓ {cycle}: Present ({dataset_count} datasets)")
        else:
            print(f"  ✗ {cycle}: MISSING")
            missing_special.append(cycle)
    
    if "2017-2020" in current_cycles:
        print(covid_note)
    
    print("\n📊 Additional Cycles Found:")
    print("-" * 70)
    all_expected = set(expected_continuous_cycles + special_cycles)
    unexpected = sorted(current_cycles - all_expected)
    if unexpected:
        for cycle in unexpected:
            dataset_count = len(df[df['cycle name'] == cycle]['dataset'].unique())
            print(f"  ℹ️  {cycle} ({dataset_count} datasets)")
    else:
        print("  None")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total_expected = len(expected_continuous_cycles)
    total_present = sum(1 for c in expected_continuous_cycles if c in current_cycles)
    
    all_missing = missing_continuous + missing_special
    
    if all_missing:
        print(f"⚠️  WARNING: {len(all_missing)} cycle(s) missing:")
        for cycle in all_missing:
            print(f"    - {cycle}")
        print(f"\n📈 Coverage: {total_present}/{total_expected} continuous cycles ({100*total_present//total_expected}%)")
    else:
        print("✅ All expected cycles are present!")
        print(f"📈 Coverage: {total_present}/{total_expected} continuous cycles (100%)")
    
    # Check for special cycles
    special_present = sum(1 for c in special_cycles if c in current_cycles)
    if special_present == len(special_cycles):
        print(f"✅ All special/COVID-adjusted cycles present ({special_present}/{len(special_cycles)})")
    
    print(f"\n📦 Total cycles in dataset: {len(current_cycles)}")
    print(f"📄 Total variables: {len(df)}")
    print("\n💡 For more information, see CYCLES.md")
    print("=" * 70)
    
    return all_missing

if __name__ == "__main__":
    missing = check_cycles()
    if missing:
        exit(1)  # Exit with error code if cycles are missing
    else:
        exit(0)
