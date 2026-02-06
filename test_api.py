#!/usr/bin/env python3
"""
Basic tests for pandas_nhanes API functions.
"""

import sys
import os

# Add package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pandas_nhanes import (
    get_variables, 
    list_cycles, 
    check_dataset_coverage
)


def test_get_variables():
    """Test that get_variables returns a non-empty DataFrame."""
    print("Testing get_variables()...")
    df = get_variables()
    assert df is not None, "get_variables returned None"
    assert len(df) > 0, "get_variables returned empty DataFrame"
    assert 'cycle name' in df.columns, "Missing 'cycle name' column"
    assert 'variable name' in df.columns, "Missing 'variable name' column"
    assert 'dataset' in df.columns, "Missing 'dataset' column"
    print(f"  ✓ Returned {len(df)} variables")


def test_list_cycles():
    """Test that list_cycles returns expected cycles."""
    print("\nTesting list_cycles()...")
    cycles = list_cycles()
    assert isinstance(cycles, list), "list_cycles should return a list"
    assert len(cycles) > 0, "list_cycles returned empty list"
    
    # Check for all expected continuous cycles
    expected_continuous = [
        "1999-2000", "2001-2002", "2003-2004", "2005-2006", "2007-2008",
        "2009-2010", "2011-2012", "2013-2014", "2015-2016", "2017-2018"
    ]
    for cycle in expected_continuous:
        assert cycle in cycles, f"Expected continuous cycle {cycle} not found"
    
    # Check for special cycles
    expected_special = ["2017-2020", "2021-2023"]
    for cycle in expected_special:
        assert cycle in cycles, f"Expected special cycle {cycle} not found"
    
    # Check that cycles are sorted
    assert cycles == sorted(cycles), "Cycles should be sorted"
    
    print(f"  ✓ Found {len(cycles)} cycles")
    print(f"  ✓ All {len(expected_continuous)} continuous cycles present")
    print(f"  ✓ All {len(expected_special)} special cycles present")


def test_check_dataset_coverage():
    """Test dataset coverage checking."""
    print("\nTesting check_dataset_coverage()...")
    
    # Test verbose=False
    coverage = check_dataset_coverage(verbose=False)
    assert isinstance(coverage, dict), "check_dataset_coverage should return a dict"
    
    # Check required keys
    required_keys = ['continuous_cycles', 'special_cycles', 'missing_cycles', 
                     'coverage_percent', 'total_cycles']
    for key in required_keys:
        assert key in coverage, f"Missing key '{key}' in coverage dict"
    
    # Check values
    assert coverage['coverage_percent'] >= 0, "Coverage percent should be >= 0"
    assert coverage['coverage_percent'] <= 100, "Coverage percent should be <= 100"
    assert coverage['total_cycles'] > 0, "Should have at least one cycle"
    assert isinstance(coverage['continuous_cycles'], list), "continuous_cycles should be a list"
    assert isinstance(coverage['special_cycles'], list), "special_cycles should be a list"
    assert isinstance(coverage['missing_cycles'], list), "missing_cycles should be a list"
    
    print(f"  ✓ Coverage: {coverage['coverage_percent']}%")
    print(f"  ✓ Total cycles: {coverage['total_cycles']}")
    
    # Dataset should be complete
    assert coverage['coverage_percent'] == 100, "Dataset should have 100% coverage"
    assert len(coverage['missing_cycles']) == 0, "No cycles should be missing"
    
    print(f"  ✓ Dataset is complete (no missing cycles)")


def test_expected_cycle_count():
    """Test that we have the expected number of continuous cycles."""
    print("\nTesting expected cycle count...")
    coverage = check_dataset_coverage(verbose=False)
    
    # Should have 10 continuous cycles (1999-2000 through 2017-2018)
    expected_continuous = 10
    actual_continuous = len(coverage['continuous_cycles'])
    assert actual_continuous == expected_continuous, \
        f"Expected {expected_continuous} continuous cycles, got {actual_continuous}"
    
    # Should have 2 special cycles (2017-2020, 2021-2023)
    expected_special = 2
    actual_special = len(coverage['special_cycles'])
    assert actual_special == expected_special, \
        f"Expected {expected_special} special cycles, got {actual_special}"
    
    print(f"  ✓ {actual_continuous} continuous cycles (expected {expected_continuous})")
    print(f"  ✓ {actual_special} special cycles (expected {expected_special})")


def test_covid_cycle_present():
    """Test that COVID-19 cycles are present."""
    print("\nTesting COVID-19 cycle presence...")
    cycles = list_cycles()
    
    # 2017-2020 should exist (pre-pandemic, includes partial 2019-2020)
    assert "2017-2020" in cycles, "2017-2020 pre-pandemic cycle should be present"
    
    # 2021-2023 should exist (pandemic data)
    assert "2021-2023" in cycles, "2021-2023 pandemic cycle should be present"
    
    # 2019-2020 should NOT exist as standalone (combined into 2017-2020)
    assert "2019-2020" not in cycles, "2019-2020 should not exist as standalone cycle"
    
    print(f"  ✓ 2017-2020 pre-pandemic cycle present")
    print(f"  ✓ 2021-2023 pandemic cycle present")
    print(f"  ✓ 2019-2020 correctly not present as standalone")


def main():
    """Run all tests."""
    print("=" * 70)
    print("Running pandas_nhanes API tests")
    print("=" * 70)
    
    tests = [
        test_get_variables,
        test_list_cycles,
        test_check_dataset_coverage,
        test_expected_cycle_count,
        test_covid_cycle_present
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n  ✗ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
