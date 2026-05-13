# pandas-nhanes

Python package for accessing [NHANES](https://www.cdc.gov/nchs/nhanes/index.htm) (National Health and Nutrition Examination Survey) data — no API key required. 53 000+ variables across 16 cycles (1999–2023). Downloaded from the CDC on first use and cached locally.

**[Website & interactive variable explorer →](https://jeromevde.github.io/Pandas-Nhanes)**

---

## Installation

```bash
pip install pandas_nhanes
```

---

## Python API

### `get_variables()`

Returns the full NHANES variables table as a DataFrame.

```python
from pandas_nhanes import get_variables

v = get_variables()
# Columns: cycle name | dataset | variable name | variable explanation |
#          dataset link | dataset documentation link

# Filter to a specific cycle
v2017 = v[v['cycle name'] == '2017-2018']

# Search by keyword
sleep_vars = v[v['variable explanation'].str.contains('sleep', case=False)]
print(sleep_vars[['cycle name', 'variable name', 'variable explanation']].to_string())
```

Available 2-year cycles: `1999-2000` `2001-2002` `2003-2004` `2005-2006` `2007-2008` `2009-2010` `2011-2012` `2013-2014` `2015-2016` `2017-2018` `2021-2023`

---

### `get_cycle_variables(cycle, *vars)`

Downloads the relevant XPT datasets from the CDC, caches them in `~/.cache/pandas_nhanes/`, and returns a DataFrame merged on `SEQN` (unique respondent ID). Variables from different survey components are outer-joined sequentially.

```python
from pandas_nhanes import get_cycle_variables

# Testosterone + age + gender — 2011-2012 cycle
df = get_cycle_variables("2011-2012", "LBXTST", "RIDAGEYR", "RIAGENDR")
#   SEQN      LBXTST  RIDAGEYR  RIAGENDR
#   62172.0    45.2      34.0       2.0
#   62174.0   312.8      67.0       1.0  ...

# Mix variables from multiple survey components in one call
df = get_cycle_variables(
    "2017-2018",
    "LBDLDL",    # LDL cholesterol  (LAB)
    "RIDAGEYR",  # Age              (DEMO)
    "SMD650",    # Cigarettes/day   (SMQ)
    "SLD012",    # Sleep hours      (SLQ)
)
```

- Unknown variables are skipped with a `[pandas_nhanes]` warning; the merge continues with the rest.
- First call per dataset downloads the `.xpt` file (~1–5 MB each). Subsequent calls use the local cache — no re-download.
- Merge log is printed to stdout: `Merging: kept N rows (was M), lost M-N (NaNs may increase)`

---

### `explore()`

Opens a searchable, paginated HTML table of all 53 000+ variables in your default browser.

```python
from pandas_nhanes import explore
explore()
# Writes ~/.cache/pandas_nhanes/nhanes_variables.html and opens it
```

---

### Common workflow

```python
from pandas_nhanes import get_variables, get_cycle_variables
import pandas as pd

# 1. Find variable codes
v = get_variables()
hits = v[v['variable explanation'].str.contains('cholesterol', case=False)]
print(hits[['cycle name', 'variable name', 'variable explanation']].to_string())

# 2. Pull the data for a cycle
df = get_cycle_variables(
    "2017-2018",
    "LBDHDD",   # HDL cholesterol
    "LBDLDL",   # LDL cholesterol
    "LBXTC",    # Total cholesterol
    "RIDAGEYR", # Age
    "RIAGENDR", # Gender (1=Male, 2=Female)
)

# 3. Clean and analyse
df = df.dropna(subset=["LBDHDD", "LBDLDL", "LBXTC", "RIDAGEYR", "RIAGENDR"])
df["RIAGENDR"] = df["RIAGENDR"].map({1.0: "Male", 2.0: "Female"})
print(df.groupby("RIAGENDR")[["LBDHDD", "LBDLDL", "LBXTC"]].mean().round(1))
```

---

## Examples

Ready-to-run analyses in [`Examples/`](Examples/):

| Example | Topic |
|---------|-------|
| [Sleep & Depression](Examples/Sleep_Depression/) | PHQ-9 score vs sleep hours — U-shaped relationship |
| [Testosterone by Age & Gender](Examples/Testosterone_Age_Gender/) | Serum testosterone across the lifespan |
| [Estradiol by Age & Gender](Examples/Estradiol_Age_Gender/) | Estradiol with fitted curves and confidence bands |
| [Testosterone / Estrogen Ratio](Examples/Testosterone_Estrogen_Ratio/) | T/E2 ratio in men by age group |
| [Cholesterol by Age](Examples/Cholesterol_Age/) | HDL, LDL, and total cholesterol trends |
| [Bone Mineral Density](Examples/BMD_Age_Gender/) | BMD across 13 body regions by age and sex |
| [Correlation Matrix](Examples/Correlation_Matrix/) | Multi-cycle variable correlation explorer with scatter plots |

Feel free to open a PR adding your own analysis to `Examples/`.

---

## Website

The repository also contains an interactive website (`index.html`) with a carousel of example plots, a full variable explorer, and an on-the-fly correlation tool backed by pre-built JSON files in `data/`.

### Run locally

No Node.js required — Python's built-in server is enough:

```bash
cd /path/to/Pandas-Nhanes
python3 -m http.server 8080
# open http://localhost:8080
```

The variable explorer and plot carousel work immediately. The correlation tool additionally needs the `data/` directory (see below).

### Build the correlation data

`build_cycle_data.py` downloads all NHANES XPT files for every cycle, merges them, and writes compact per-cycle JSON files that the browser loads on demand.

```bash
# Full build — all 10 cycles (~several GB download, ~30 min first run)
python3 build_cycle_data.py

# Quick test — one cycle only (~200 MB, a few minutes)
python3 -c "
import build_cycle_data as b
b.CYCLES = ['2017-2018']
b.main()
"
```

Output goes to `data/` in the repo root:
- `data/manifest.json` — list of available cycles with variable counts
- `data/2017-2018.json` — sampled column data for that cycle (used for on-the-fly correlation + scatter plots)

After building, refresh `http://localhost:8080` — the correlation explorer will be fully functional.

### Install Python dev dependencies

```bash
pip install -e .
```
