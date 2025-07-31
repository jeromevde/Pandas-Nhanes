# Pandas-Nhanes

A Python package for accessing a cleaned subset of NHANES 
*National Health and Nutrition Examination Survey* data for quick prototyping—no API key required.

Access via https://jeromevde.github.io/Pandas-Nhanes 

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
from pandas_nhanes import get_variables, get_dataset
```
```python
# Get the full NHANES variable table
variables = get_variables()
```

```python
# Download a dataset as a pandas DataFrame
TST_L = get_dataset("TST_L")
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

3.  **Build the site:**
    This command will generate the static site in the root directory.
    ```bash
    npm run build
    ```

## Examples

The repository includes several examples of NHANES data analysis in the `Examples` folder. Each example demonstrates how to work with specific datasets and create visualizations.

To run all examples and regenerate the plots:

```bash 
(cd Examples && for script in *.py; do echo "Running $script..."; python "$script"; echo "Completed $script"; echo ""; done)
```

### Variables Explorer

You can explore the NHANES variables on the main page of the website.



