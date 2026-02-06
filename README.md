# Pandas-Nhanes

A Python package for accessing a cleaned subset of NHANES 
*National Health and Nutrition Examination Survey* data for quick prototyping—no API key required. https://jeromevde.github.io/Pandas-Nhanes 

## Dataset Coverage

This package includes NHANES data from **1999-2023**, covering all standard biennial cycles and special COVID-19-adjusted cycles. For detailed information about cycle coverage, see [CYCLES.md](CYCLES.md).

**Quick check**: Run `python3 check_cycles.py` to verify dataset completeness. 



## Examples


The repository includes several examples of NHANES data analysis in the `Examples` folder. Each example demonstrates how to work with specific datasets and create visualizations.

<span style="font-size:2em;vertical-align:middle;">❗</span> Feel free to open a PR with your own ideas in the `Examples` folder 




## Installation

Install from PyPI:

```bash
pip install pandas_nhanes
```


## Usage


```python
from pandas_nhanes import get_variables, get_cycle_variables, list_cycles, check_dataset_coverage

# Get the full NHANES variable table
variables = get_variables()

# Download and merge variables from a specific cycle, logging merge stats
df = get_cycle_variables("2011-2012", "LBXTST", "RIDAGEYR", "RIAGENDR")

# List all available cycles
cycles = list_cycles()
print(cycles)  # ['1999-2000', '2001-2002', ...]

# Check dataset coverage
coverage = check_dataset_coverage()
# Prints: NHANES Dataset Coverage: ... 100% complete
```

### Available Cycles

To see all available NHANES cycles and check for completeness:

```python
from pandas_nhanes import check_dataset_coverage

# Get detailed coverage report
coverage = check_dataset_coverage(verbose=True)

# Or run the standalone checker
# python3 check_cycles.py
```

**Note**: The 2019-2020 cycle was disrupted by COVID-19. Data from this period is included in the `2017-2020` pre-pandemic cycle. See [CYCLES.md](CYCLES.md) for details.

## Development

To set up the development environment, you will need Node.js and npm.

1.  **Install dependencies:**
    ```bash
    npm install
    ```

2.  **Run the development server:**
    This command will build the site and start a live-reloading server.
    ```bash
    npm run dev
    ```
    You can view the site at `http://localhost:8080`.

