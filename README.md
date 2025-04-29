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
from pandas_nhanes import get_variables, get_dataset

# Get the full NHANES variable table
variables = get_variables()
print(variables.head())

# Download a dataset as a pandas DataFrame
# (use the 'dataset link' column from the variables table)
dataset = variables.iloc[0]['dataset']
df = get_dataset(dataset)
print(df.head())
```