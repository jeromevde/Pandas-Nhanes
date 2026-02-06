# GitHub Copilot Instructions for Pandas-Nhanes

## Project Overview

Pandas-Nhanes is a Python package that provides easy access to cleaned NHANES (National Health and Nutrition Examination Survey) data for quick prototyping and data analysis. The package allows researchers and data scientists to download and merge NHANES variables without needing an API key.

**Key Features:**
- Simplified API for accessing NHANES data
- Automatic data caching in `~/.cache/pandas_nhanes/`
- Interactive variable exploration via web browser
- Sequential merging of variables with logging
- No API key required

**Public API:**
- `get_variables()` - Returns the full NHANES variables table
- `get_cycle_variables(cycle, *vars)` - Downloads and merges specific variables from a cycle
- `explore()` - Opens interactive HTML table for browsing variables

## Technology Stack

- **Language:** Python 3.8+
- **Key Dependencies:** pandas (≥2.2.3), requests, tqdm, itables
- **Build System:** setuptools
- **Website:** Static HTML with live-server for development
- **Package Distribution:** PyPI
- **Documentation:** GitHub Pages

## Development Setup

### Python Package Development

```bash
# Install the package in development mode
pip install -e .

# Install development dependencies
pip install pandas>=2.2.3 requests>=2.32.3 tqdm>=4.66.4 itables>=2.3.0
```

### Website Development

The repository includes a static website for exploring NHANES variables:

```bash
# Install Node.js dependencies
npm install

# Run development server (opens browser automatically)
npm run dev

# The site will be available at http://localhost:8080
```

## Project Structure

```
pandas_nhanes/
├── .github/
│   └── workflows/          # CI/CD workflows
├── Examples/               # Example analyses demonstrating package usage
│   ├── Sleep_Depression/  # Each example has plot.py, README.md, and outputs
│   ├── Testosterone_Age_Gender/
│   └── ...
├── pandas_nhanes/         # Main package source
│   ├── __init__.py        # Package exports
│   ├── api.py             # Core API functions
│   ├── nhanes_variables.csv  # NHANES variables metadata
│   └── scrape_variables.py   # Script to update variables table
├── index.html             # Website entry point
├── setup.py               # Package configuration
└── README.md              # Package documentation
```

## Code Style and Conventions

### Python Code

- **Style:** Follow PEP 8 conventions
- **Imports:** Standard library first, then third-party, then local imports
- **Docstrings:** Use concise docstrings explaining purpose and return values
- **Error Handling:** Print informative messages prefixed with `[pandas_nhanes]`
- **Data Handling:** Always check for `SEQN` column (unique identifier in NHANES)

### Example Code Style

```python
def get_cycle_variables(cycle, *vars):
    """
    Load and sequentially merge variables from a specific NHANES cycle.
    Returns a DataFrame with SEQN and the requested variables.
    """
    # Implementation with informative logging
    print(f"[pandas_nhanes] Variable '{var}' not found in cycle '{cycle}'. Skipping.")
```

### Examples

- Place in `Examples/` directory with descriptive folder names
- Include `plot.py`, `README.md`, and output files (`.html`, `.png`)
- Use plotly for visualizations
- Document research question, data sources, and key findings in README
- Use emojis for visual appeal (✅, ⚠️, etc.)

## Testing

**Current State:** No formal test suite exists in this repository.

When adding tests in the future:
- Use pytest as the testing framework
- Test core functions in `api.py`
- Mock HTTP requests to NHANES data sources
- Validate data merging logic
- Test error handling for missing variables

## Build and Deployment

### PyPI Publishing

- Triggered by push to `main` branch with `[pypi]` in commit message
- Workflow: `.github/workflows/publish.yml`
- Version bumping is automated via `bump_version.sh`
- Package is built with `python -m build`
- Published to PyPI using twine

### GitHub Pages

- Automatically deploys on push to `main` or `dev` branches
- Workflow: `.github/workflows/github-pages.yml`
- Serves `index.html` and Examples for interactive exploration
- No build step required (static files)

## Data Sources and Caching

- **NHANES Data:** Downloaded from CDC's NHANES website (.xpt SAS transport files)
- **Caching:** All downloaded datasets cached in `~/.cache/pandas_nhanes/`
- **Variables Table:** `pandas_nhanes/nhanes_variables.csv` contains metadata
- **Data Format:** SAS XPORT format, read with `pandas.read_sas()`

## Common Tasks

### Adding a New Example Analysis

1. Create a new folder in `Examples/` with a descriptive name
2. Add `plot.py` with the analysis code
3. Add `README.md` documenting the research question and findings
4. Generate output files (`.html` and `.png`)
5. Update main README.md to reference the new example

### Updating NHANES Variables Table

1. Run `pandas_nhanes/scrape_variables.py` to fetch latest variables
2. Review changes to `nhanes_variables.csv`
3. Commit updated CSV file
4. Version bump if API-breaking changes

### Making Code Changes

1. Edit source files in `pandas_nhanes/`
2. Test changes locally by installing in development mode
3. Ensure backward compatibility with existing examples
4. Update version in `setup.py` if needed
5. Commit with descriptive message
6. Add `[pypi]` to commit message only for releases

## Important Conventions

- **Merge Strategy:** Sequential outer joins on `SEQN` with logging
- **Missing Data:** Print warnings, never fail silently
- **Variable Names:** Preserve exact NHANES variable names (e.g., `LBXTST`, `RIDAGEYR`)
- **Cycle Format:** Use "YYYY-YYYY" format (e.g., "2015-2016")
- **User Feedback:** Use descriptive print statements for data operations

## Dependencies Management

- Keep dependencies minimal and version-pinned in `setup.py`
- Only add dependencies that are essential for core functionality
- Example-specific dependencies (like plotly) should be documented in example READMEs
- Update `install_requires` when adding new dependencies

## Contributing Guidelines

When contributing examples:
- Follow the existing example structure
- Include data source citations
- Provide clear research questions
- Add visual annotations to plots
- Keep code readable and well-commented
- Ensure reproducibility

## Gotchas and Known Issues

- **SEQN:** Not all NHANES datasets have `SEQN` - check before merging
- **Variable Availability:** Variables may not exist in all cycles
- **Data Quality:** NHANES data may have missing values - always clean data
- **File Downloads:** First run may be slow due to downloading .xpt files
- **File Format:** SAS XPORT files (.xpt) are binary format - use `pandas.read_sas()` which handles the encoding automatically

## Resources

- [NHANES Website](https://www.cdc.gov/nchs/nhanes/index.htm)
- [NHANES Variables Documentation](https://wwwn.cdc.gov/nchs/nhanes/)
- [Package Website](https://jeromevde.github.io/Pandas-Nhanes)
- [PyPI Package](https://pypi.org/project/pandas_nhanes/)
