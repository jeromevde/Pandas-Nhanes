# Pandas-Nhanes

A Python package for accessing a cleaned subset of NHANES 
*National Health and Nutrition Examination Survey* data for quick prototyping—no API key required. https://jeromevde.github.io/Pandas-Nhanes 



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
from pandas_nhanes import get_variables, get_cycle_variables
# Get the full NHANES variable table
variables = get_variables()
# Download and merge variables from a specific cycle, logging merge stats
df = get_cycle_variables("2011-2012", "LBXTST", "RIDAGEYR", "RIAGENDR")
```

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

