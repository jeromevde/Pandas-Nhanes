# Pandas-Nhanes

A Python package for accessing a cleaned subset of NHANES 
*National Health and Nutrition Examination Survey* data for quick prototyping—no API key required.

Caching is implemented to avoid re-downloading datasets.

## Installation

Install from PyPI:

```bash
pip install pandas_nhanes
```

Or from source:

```bash
git clone https://github.com/jeromevde/pandas_nhanes.git
cd pandas_nhanes
pip install -e .
```

## Usage

```python
from pandas_nhanes import get_variables, get_dataset, explore
```
```python
# Get the full NHANES variable table
variables = get_variables()
```

```python
# Explore the variables table in an interactive HTML table in browser
explore()
```
```python
# Download a dataset as a pandas DataFrame
TST_L = get_dataset("TST_L")
```

## Results

### Cycle 2021-2023 Estradiol
![estradiol](Examples/estradiol.png)

### Cycle 2021-2023 Testosterone
![testosterone](Examples/testosterone.png)