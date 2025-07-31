# Pandas-Nhanes

A Python package for accessing a cleaned subset of NHANES 
*National Health and Nutrition Examination Survey* data for quick prototyping—no API key required.

Access via https://jeromevde.github.io/Pandas-Nhanes 

![](website.png)

Caching is implemented to avoid re-downloading datasets.

# Todo
- include demographics data automatically in df

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

## Examples

### Analysis Examples

The repository includes several examples of NHANES data analysis in the `Examples` folder. Each example demonstrates how to work with specific datasets and create visualizations.

Rerun all examples in the examples folder:

```bash 
cd Examples
for script in *.py; do echo "Running $script..."; python "$script"; echo "Completed $script"; echo ""; done
```

### Variables Explorer

You can explore the NHANES variables online at: https://jeromevde.github.io/Pandas-Nhanes

To run the variables explorer locally (interactive mode):

```bash
# Run the local development server (generates the site and serves it)
python run_local_site.py
```

This will automatically generate the site, start a local server, and open your browser to view it.



