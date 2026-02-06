# NHANES Dataset Coverage

This document explains the NHANES cycles included in this dataset and addresses any gaps or special cases.

## Standard NHANES Cycles

NHANES (National Health and Nutrition Examination Survey) typically operates on a continuous 2-year cycle basis. The following standard cycles are included:

| Cycle | Status | Datasets |
|-------|--------|----------|
| 1999-2000 | ✅ Included | 110 |
| 2001-2002 | ✅ Included | 131 |
| 2003-2004 | ✅ Included | 141 |
| 2005-2006 | ✅ Included | 131 |
| 2007-2008 | ✅ Included | 130 |
| 2009-2010 | ✅ Included | 139 |
| 2011-2012 | ✅ Included | 148 |
| 2013-2014 | ✅ Included | 182 |
| 2015-2016 | ✅ Included | 148 |
| 2017-2018 | ✅ Included | 122 |
| 2019-2020 | ⚠️ See note below | - |

## COVID-19 Impact on NHANES Cycles

### 2019-2020 Cycle

The 2019-2020 NHANES cycle was disrupted by the COVID-19 pandemic. Data collection was suspended in March 2020. As a result:

- **There is no standalone 2019-2020 cycle** in the NHANES public dataset
- The 2019-2020 data that was collected (before pandemic suspension) was **combined** with the 2017-2018 cycle
- This combined dataset is available as the **2017-2020 Pre-Pandemic cycle**

### Special/Combined Cycles

| Cycle | Description | Datasets |
|-------|-------------|----------|
| 2017-2020 | Pre-pandemic data (combines 2017-2018 and partial 2019-2020) | 107 |
| 2021-2023 | COVID-19 pandemic data collection | 65 |

## Additional Multi-Year Cycles

Some NHANES datasets span multiple cycles for longitudinal studies or combined analyses:

| Cycle | Datasets | Description |
|-------|----------|-------------|
| 1999-2004 | 8 | Early multi-year datasets |
| 1999-2020 | 3 | Long-term trend datasets |
| 1999-2023 | 3 | Complete dataset coverage |
| 2007-2012 | 1 | Special combined dataset |

## Summary

- ✅ **Complete coverage**: All available standard NHANES cycles from 1999-2018
- ✅ **COVID-19 adapted**: Includes both pre-pandemic (2017-2020) and pandemic (2021-2023) data
- ⚠️ **Note**: The 2019-2020 standalone cycle does not exist; use the 2017-2020 cycle for this period
- 📊 **Total**: 16 different cycle periods with 53,000+ variables

## How to Use This Data

When working with NHANES data:

1. **For 2019-2020 data**: Use the `2017-2020` cycle, which includes pre-pandemic data
2. **For trend analysis**: Be aware that 2017-2020 is a 3-year cycle (not the standard 2 years)
3. **For pandemic-era data**: Use the `2021-2023` cycle

## Verification

You can verify the cycle coverage by running:

```bash
python3 check_cycles.py
```

This script will display a detailed report of all available cycles and identify any gaps.

## References

- [NHANES Website](https://www.cdc.gov/nchs/nhanes/index.htm)
- [NHANES Data Files](https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx)
- [COVID-19 Impact on NHANES](https://www.cdc.gov/nchs/nhanes/covid19.htm)
