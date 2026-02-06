#!/usr/bin/env python3
"""
Quick Start Guide - Run This First

This script provides an interactive menu to help you choose the right analysis
"""

import sys

def print_menu():
    print("="*80)
    print("NHANES CORRELATION ANALYSIS - QUICK START")
    print("="*80)
    print()
    print("What do you want to do?")
    print()
    print("1. COMPREHENSIVE ANALYSIS (RECOMMENDED)")
    print("   → Analyze multiple NHANES cycles with real data")
    print("   → Smart variable selection (80 vars per cycle)")
    print("   → Downloads data from CDC (requires internet)")
    print("   → Runtime: 30-60 minutes")
    print("   → Script: practical_comprehensive_analysis.py")
    print()
    print("2. VIEW ANALYSIS SCOPE")
    print("   → See total number of variable pairs across all cycles")
    print("   → Understand the full 12.8M pair analysis scope")
    print("   → No data download required")
    print("   → Runtime: < 1 minute")
    print("   → Script: comprehensive_analysis.py")
    print()
    print("3. DEMO WITH SIMULATED DATA")
    print("   → Test methodology with fake but realistic data")
    print("   → No internet required")
    print("   → Runtime: < 1 minute")
    print("   → Script: correlation_analysis_demo.py")
    print()
    print("4. SINGLE CYCLE ANALYSIS")
    print("   → Original demo - analyze one cycle (2015-2016)")
    print("   → 10 random variables")
    print("   → Requires internet")
    print("   → Runtime: 5-10 minutes")
    print("   → Script: correlation_analysis.py")
    print()
    print("="*80)
    print()

def print_recommendation():
    print("="*80)
    print("RECOMMENDATION")
    print("="*80)
    print()
    print("Based on the PR comments, you want:")
    print()
    print("✓ Full cross-join correlation study for each cycle")
    print("✓ Non-linear transformations (log, sqrt, square, inverse)")
    print("✓ Ranked results by transformation type")
    print("✓ Filter obvious relationships")
    print("✓ Extract outliers and unexpected patterns")
    print()
    print("→ RUN OPTION 1: practical_comprehensive_analysis.py")
    print()
    print("Command:")
    print("  cd Examples/Variable_Correlation_Analysis")
    print("  python3 practical_comprehensive_analysis.py")
    print()
    print("This will:")
    print("  • Analyze 3 cycles by default (configurable)")
    print("  • Select 80 priority variables per cycle")
    print("  • Compute correlations with 5 transformations")
    print("  • Filter obvious relationships automatically")
    print("  • Save results grouped by transformation type")
    print("  • Generate summary with top findings")
    print()
    print("Output files:")
    print("  • top_correlations_original_original.csv")
    print("  • top_correlations_log_log.csv")
    print("  • top_correlations_sqrt_original.csv")
    print("  • ... (one per transformation combination)")
    print("  • transformation_summary.csv")
    print()
    print("="*80)
    print()

def print_scaling_info():
    print("="*80)
    print("SCALING TO ALL CYCLES")
    print("="*80)
    print()
    print("Current scope:")
    print("  16 NHANES cycles")
    print("  ~12.8 million total variable pairs")
    print("  ~64 million calculations with transformations")
    print()
    print("To analyze ALL cycles:")
    print()
    print("Option A: Sequential Processing")
    print("  1. Edit practical_comprehensive_analysis.py")
    print("  2. Change: target_cycles = ['2015-2016', '2013-2014', ...]")
    print("  3. Add all 16 cycles to the list")
    print("  4. Runtime: ~8-16 hours total")
    print()
    print("Option B: Parallel Processing")
    print("  1. Run each cycle on separate machine/core")
    print("  2. Use cluster computing framework (Dask, Ray)")
    print("  3. Aggregate results afterward")
    print("  4. Runtime: ~1-2 hours with 16 cores")
    print()
    print("Option C: Smart Sampling (RECOMMENDED)")
    print("  1. Keep default 3 most recent cycles")
    print("  2. Covers latest data with manageable runtime")
    print("  3. Expand if needed based on findings")
    print()
    print("="*80)
    print()

def main():
    print_menu()
    print_recommendation()
    
    try:
        choice = input("Enter choice (1-4) or 's' for scaling info, 'q' to quit: ").strip()
        
        if choice == 'q':
            print("\nExiting. See COMPREHENSIVE_ANALYSIS_README.md for full documentation.")
            sys.exit(0)
        elif choice == 's':
            print()
            print_scaling_info()
            main()
        elif choice == '1':
            print("\n" + "="*80)
            print("RUNNING: Practical Comprehensive Analysis")
            print("="*80)
            import practical_comprehensive_analysis
            practical_comprehensive_analysis.main()
        elif choice == '2':
            print("\n" + "="*80)
            print("RUNNING: Analysis Scope View")
            print("="*80)
            import comprehensive_analysis
            comprehensive_analysis.main()
        elif choice == '3':
            print("\n" + "="*80)
            print("RUNNING: Demo with Simulated Data")
            print("="*80)
            import correlation_analysis_demo
            correlation_analysis_demo.main()
        elif choice == '4':
            print("\n" + "="*80)
            print("RUNNING: Single Cycle Analysis")
            print("="*80)
            import correlation_analysis
            correlation_analysis.main()
        else:
            print(f"\nInvalid choice: {choice}")
            print("Please enter 1, 2, 3, 4, 's', or 'q'\n")
            main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Exiting.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        print("\nSee COMPREHENSIVE_ANALYSIS_README.md for troubleshooting.")
        sys.exit(1)

if __name__ == "__main__":
    main()
