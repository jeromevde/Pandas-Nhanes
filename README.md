# pandas_nhanes

A Python package for accessing and processing NHANES (National Health and Nutrition Examination Survey) data using pandas.

- Clean API for variable selection and data download
- Easily merge and analyze NHANES cycles
- Well-documented and pip-installable

## Installation

Install from PyPI:

```bash
pip install pandas_nhanes
```

Or install from source:

```bash
git clone https://github.com/jeromevde/pandas_nhanes.git
cd pandas_nhanes
pip install .
```

## Example Usage

```python
from pandas_nhanes import (
    list_cycles,
    list_cycle_variables,
    get_variable_description,
    get_variable_data,
    download_full_cycle_dataframe,
)

# List all available NHANES cycles
print(list_cycles())

# List all variables for a given cycle
vars_df = list_cycle_variables("2021-2023")
print(vars_df.head())

# Get the description for a specific variable
print(get_variable_description("LBXTST"))

# Get data for specific variables from a cycle
variables = ["LBXTST", "DR1TCAFF"]
df = get_variable_data(variables, "2021-2023")[project]
name = "pandas_nhanes"
version = "0.1.1"
...
print(df.head())

# Download and merge all datasets for a cycle
full_df = download_full_cycle_dataframe("2021-2023", replace_names_with_descriptions=True)
print(full_df.head())
```


## Further improvement
- caching
- variable exploration
- website explorer & deploy to github pages that can be opened through explore()
