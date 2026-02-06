# Automated Plot Manifest Generation

## Problem
Previously, when adding a new plot to the `Examples/` directory, you had to manually edit `index.html` and add the plot name to the hardcoded `plotExamples` array. This was error-prone and easy to forget.

## Solution
The plots are now automatically discovered and loaded dynamically:

1. **`generate_plots_manifest.py`** - A Python script that scans the `Examples/` directory and generates `plots.json`
2. **Updated `index.html`** - Now fetches plot information from `plots.json` instead of a hardcoded array
3. **GitHub Actions integration** - The manifest is automatically regenerated on every push to `main`

## How It Works

### Automatic (GitHub Actions)
Every time you push to `main`, the GitHub Pages workflow:
1. Runs `generate_plots_manifest.py` to scan `Examples/` 
2. Generates `plots.json` with all discovered plots
3. Deploys the site with the updated manifest

### Manual (Local Testing)
To regenerate the manifest locally:
```bash
python3 generate_plots_manifest.py
```

This creates/updates `plots.json` with all plots found in `Examples/`.

## Adding New Plots

Simply add your plot to `Examples/`:
```
Examples/
  └── YourNewPlot/
      ├── YourNewPlot.png   (required)
      ├── YourNewPlot.html  (optional)
      └── YourNewPlot.py    (optional)
```

The script looks for:
- **PNG file**: Either `<name>.png` or `plot.png` (required)
- **HTML file**: Either `<name>.html` or `index.html` (optional)

Push to GitHub, and your plot will automatically appear on the site!

## File Structure

- `generate_plots_manifest.py` - Manifest generator script
- `plots.json` - Auto-generated manifest (gitignored, created by CI)
- `index.html` - Updated to load plots dynamically from JSON

## Benefits

✅ No manual editing of `index.html` required  
✅ Automatically discovers new plots  
✅ Reduces human error  
✅ Supports flexible naming conventions  
✅ Works seamlessly with GitHub Pages deployment
