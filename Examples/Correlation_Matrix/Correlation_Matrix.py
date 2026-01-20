#!/usr/bin/env python3
"""
NHANES Correlation Matrix Generator
Loads ALL variables from cached XPT files for a cohort and creates an interactive correlation matrix.
- Labels show real variable names (or code if not available)
- Hover shows variable code
- Click on cell shows X-Y scatter plot
"""

import pandas as pd
import json
import base64
import os
import numpy as np
import glob

# Configuration
COHORT = '2017-2018'  # 2017-2018 uses _J suffix
MIN_VALID = 100  # Minimum valid values required
MAX_VARS = 100  # Maximum variables to include

def load_cached_tables(cohort_suffix):
    """Load all cached XPT files for a cohort suffix."""
    cache_dir = os.path.expanduser("~/.cache/pandas_nhanes")
    
    # Find all XPT files for this cohort
    pattern = os.path.join(cache_dir, f"*_{cohort_suffix}.xpt")
    files = glob.glob(pattern)
    
    print(f"📂 Found {len(files)} cached tables for suffix '_{cohort_suffix}'")
    
    dfs = {}
    for f in files:
        table_name = os.path.basename(f).replace(f"_{cohort_suffix}.xpt", "")
        try:
            df = pd.read_sas(f)
            # Only include tables that have SEQN column
            if 'SEQN' not in df.columns:
                print(f"   ⊘ {table_name}: No SEQN column, skipping")
                continue
            dfs[table_name] = df
            print(f"   ✓ {table_name}: {len(df)} rows, {len(df.columns)} cols")
        except Exception as e:
            print(f"   ✗ {table_name}: {e}")
    
    # Merge all tables on SEQN
    if not dfs:
        print("❌ No tables loaded")
        return None
    
    # Start with the largest table
    main_df = None
    for name, df in sorted(dfs.items(), key=lambda x: len(x[1]), reverse=True):
        if main_df is None:
            main_df = df.copy()
        else:
            # Merge on SEQN (respondent sequence number)
            main_df = main_df.merge(df, on='SEQN', how='outer', suffixes=('', '_dup'))
            # Remove duplicate columns
            dup_cols = [c for c in main_df.columns if c.endswith('_dup')]
            if dup_cols:
                main_df = main_df.drop(columns=dup_cols)
    
    print(f"\n📊 Merged: {len(main_df)} rows, {len(main_df.columns)} columns")
    return main_df

def filter_numeric_vars(df, min_valid=100):
    """Filter to numeric columns with enough valid data."""
    numeric_cols = df.select_dtypes(include=[np.float64, np.int64, np.float32, np.int32]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c != 'SEQN']  # Exclude ID
    
    valid_cols = []
    for col in numeric_cols:
        try:
            n_valid = df[col].notna().sum()
            if n_valid >= min_valid and df[col].std() > 0:
                valid_cols.append((col, n_valid))
        except:
            continue
    
    # Sort by number of valid values, take top MAX_VARS
    valid_cols.sort(key=lambda x: x[1], reverse=True)
    valid_cols = [c[0] for c in valid_cols[:MAX_VARS]]
    
    return valid_cols

def get_variable_descriptions(valid_cols):
    """Get descriptions for variables from pandas_nhanes."""
    from pandas_nhanes.api import get_variables
    
    try:
        vars_df = get_variables()
        # Get descriptions for valid columns
        desc = {}
        for col in valid_cols:
            match = vars_df[vars_df['variable name'] == col]
            if not match.empty:
                desc[col] = match['variable explanation'].iloc[0]
            else:
                desc[col] = col
        return desc
    except Exception as e:
        print(f"   Warning: Could not get descriptions: {e}")
        return {c: c for c in valid_cols}

def generate_html(df, valid_cols, var_desc, cohort, output_file):
    """Generate interactive HTML correlation matrix."""
    
    print(f"\n📊 Computing correlations for {len(valid_cols)} variables...")
    
    # Calculate correlation matrix
    corr_matrix = df[valid_cols].corr()
    
    # Create scatter data for top pairs
    MAX_SCATTER_SAMPLES = 200
    strong_corrs = []
    for i, y_col in enumerate(valid_cols):
        for j, x_col in enumerate(valid_cols):
            if i < j:
                try:
                    corr_val = corr_matrix.loc[y_col, x_col]
                    if not np.isnan(corr_val):
                        strong_corrs.append((x_col, y_col, abs(corr_val), corr_val))
                except:
                    continue
    
    strong_corrs.sort(key=lambda x: x[2], reverse=True)
    top_pairs = strong_corrs[:400]
    
    scatter_data = {}
    for x_col, y_col, _, corr_val in top_pairs:
        key = f"{x_col}|{y_col}"
        plot_df = df[[x_col, y_col]].dropna()
        if len(plot_df) >= 5:
            if len(plot_df) > MAX_SCATTER_SAMPLES:
                plot_df = plot_df.sample(n=MAX_SCATTER_SAMPLES, random_state=42)
            scatter_data[key] = {
                'x': plot_df[x_col].tolist(),
                'y': plot_df[y_col].tolist(),
                'correlation': round(corr_val, 3),
                'n': len(df[[x_col, y_col]].dropna())
            }
    
    print(f"   Generated {len(scatter_data)} scatter plots")
    
    # Encode data
    scatter_json = json.dumps(scatter_data)
    scatter_b64 = base64.b64encode(scatter_json.encode()).decode()
    corr_json = corr_matrix.to_json()
    corr_b64 = base64.b64encode(corr_json.encode()).decode()
    desc_json = json.dumps(var_desc)
    desc_b64 = base64.b64encode(desc_json.encode()).decode()
    
    matrix_size = min(1200, max(600, len(valid_cols) * 14))
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NHANES Correlation Matrix - {cohort}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1600px; margin: 0 auto; }}
        h1 {{ color: #333; text-align: center; margin-bottom: 5px; }}
        h2 {{ color: #666; text-align: center; font-weight: normal; margin-top: 0; }}
        .stats {{ text-align: center; color: #555; font-size: 13px; margin-bottom: 15px; }}
        .instructions {{ text-align: center; color: #444; margin-bottom: 20px; padding: 15px; background: #e8f4f8; border-radius: 5px; border-left: 4px solid #2196F3; }}
        #matrix-container {{ width: 100%; display: flex; justify-content: center; }}
        #correlation-matrix {{ width: 100%; }}
        #scatter-plot {{ width: 100%; height: 550px; border: 1px solid #ddd; border-radius: 5px; background: white; display: none; margin-top: 20px; }}
        #scatter-plot.visible {{ display: block; }}
        .loading {{ text-align: center; padding: 20px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>NHANES Correlation Matrix</h1>
        <h2>Cohort: {cohort}</h2>
        <div class="stats">Variables: {len(valid_cols)} | Sample size: {len(df)} | Top pairs preloaded: {len(scatter_data)}</div>
        <div class="instructions">
            <strong>👆 Click on any cell</strong> in the matrix to see the X-Y scatter plot!<br>
            <small>Hover over cells to see correlation values. Hover over axis labels to see variable codes.</small>
        </div>
        <div id="matrix-container">
            <div id="correlation-matrix"></div>
        </div>
        <div id="scatter-plot">
            <div class="loading">Click on a cell to view scatter plot...</div>
        </div>
    </div>

    <script>
        const corrData = JSON.parse(atob('{corr_b64}'));
        const scatterData = JSON.parse(atob('{scatter_b64}'));
        const varDesc = JSON.parse(atob('{desc_b64}'));
        const validCols = {json.dumps(valid_cols)};
        
        // Display labels: show description, but fallback to code
        const displayLabels = validCols.map(c => varDesc[c] || c);
        
        // Build correlation matrix
        const zValues = [];
        const textValues = [];
        for (let i = 0; i < validCols.length; i++) {{
            const row = [], textRow = [];
            for (let j = 0; j < validCols.length; j++) {{
                const corr = corrData[validCols[i]][validCols[j]];
                row.push(corr);
                textRow.push(corr !== null ? corr.toFixed(2) : '-');
            }}
            zValues.push(row);
            textValues.push(textRow);
        }}
        
        // Create heatmap
        const data = [{{
            z: zValues,
            x: displayLabels,
            y: displayLabels,
            text: textValues,
            texttemplate: "%{{text}}",
            textfont: {{size: 8}},
            type: 'heatmap',
            colorscale: 'RdBu_r',
            zmin: -1,
            zmax: 1,
            hoverongaps: false,
            hovertemplate: '<b>%{{x}}</b> vs <b>%{{y}}</b><br>r: %{{z:.3f}}<extra></extra>'
        }}];
        
        const layout = {{
            title: '{{Click on a cell to view scatter plot}}',
            xaxis: {{
                title: 'Variables (hover for code)',
                tickangle: 45,
                tickfont: {{size: 8}},
                automargin: true
            }},
            yaxis: {{
                title: 'Variables (hover for code)',
                tickfont: {{size: 8}},
                automargin: true
            }},
            width: {matrix_size},
            height: {matrix_size},
            clickmode: 'event+select',
            hovermode: 'closest'
        }};
        
        Plotly.newPlot('correlation-matrix', data, layout);
        
        // Handle click
        document.getElementById('correlation-matrix').on('plotly_click', function(data) {{
            if (!data.points || !data.points[0]) return;
            
            const pt = data.points[0];
            const xLabel = pt.x;
            const yLabel = pt.y;
            
            // Find original column names
            const xCol = validCols.find(c => varDesc[c] === xLabel) || xLabel;
            const yCol = validCols.find(c => varDesc[c] === yLabel) || yLabel;
            
            if (xCol === yCol) return;
            
            showScatterPlot(xCol, yCol, xLabel, yLabel);
        }});
        
        function showScatterPlot(xCol, yCol, xLabel, yLabel) {{
            const plotDiv = document.getElementById('scatter-plot');
            
            let key = xCol + '|' + yCol;
            let reverse = false;
            if (!scatterData[key]) {{
                key = yCol + '|' + xCol;
                reverse = true;
            }}
            
            if (scatterData[key]) {{
                const d = scatterData[key];
                const xData = reverse ? d.y : d.x;
                const yData = reverse ? d.x : d.y;
                const r = reverse ? -d.correlation : d.correlation;
                
                Plotly.newPlot('scatter-plot', [{{
                    x: xData,
                    y: yData,
                    mode: 'markers',
                    type: 'scatter',
                    marker: {{ size: 6, opacity: 0.5, color: 'steelblue' }},
                    hovertemplate: '<b>' + xCol + ':</b> %{{x:.2f}}<br><b>' + yCol + ':</b> %{{y:.2f}}<extra></extra>'
                }}], {{
                    title: {{
                        text: xLabel + ' vs ' + yLabel + '<br><sub>Code: ' + xCol + ' vs ' + yCol + ' | r = ' + r.toFixed(3) + ', n = ' + d.n + '</sub>',
                        font: {{size: 14}}
                    }},
                    xaxis: {{title: xLabel + ' (' + xCol + ')'}},
                    yaxis: {{title: yLabel + ' (' + yCol + ')'}},
                    hovermode: 'closest'
                }});
                plotDiv.classList.add('visible');
                plotDiv.scrollIntoView({{behavior: 'smooth', block: 'start'}});
            }} else {{
                plotDiv.innerHTML = '<div class="loading"><p>Scatter plot not available.</p><p>Only top 400 correlation pairs are preloaded.</p></div>';
                plotDiv.classList.add('visible');
            }}
        }}
    </script>
</body>
</html>'''
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    size_mb = os.path.getsize(output_file) / 1024 / 1024
    print(f"✅ Generated: {output_file} ({size_mb:.1f} MB)")
    return output_file

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate NHANES correlation matrix')
    parser.add_argument('--cohort', '-c', default='2017-2018', help='NHANES cycle (e.g., 2017-2018)')
    parser.add_argument('--output', '-o', default=None, help='Output HTML file')
    parser.add_argument('--min-valid', '-m', type=int, default=MIN_VALID, help='Min valid values per variable')
    parser.add_argument('--max-vars', '-n', type=int, default=MAX_VARS, help='Max variables')
    args = parser.parse_args()
    
    # Map cohort to suffix
    suffix_map = {'2009-2010': 'F', '2011-2012': 'G', '2013-2014': 'H', '2015-2016': 'I', '2017-2018': 'J'}
    suffix = suffix_map.get(args.cohort, 'J')
    
    print("=" * 60)
    print(f"NHANES Correlation Matrix: {args.cohort}")
    print(f"Max variables: {args.max_vars}, Min valid: {args.min_valid}")
    print("=" * 60)
    
    # Load cached data
    df = load_cached_tables(suffix)
    
    if df is None:
        return
    
    # Filter to valid numeric columns
    valid_cols = filter_numeric_vars(df, args.min_valid)
    print(f"\n✅ Selected {len(valid_cols)} valid numeric variables")
    
    # Get descriptions
    var_desc = get_variable_descriptions(valid_cols)
    
    # Generate HTML
    output_file = args.output or f'correlation_matrix_{args.cohort.replace("-", "_")}.html'
    generate_html(df, valid_cols, var_desc, args.cohort, output_file)
    
    print(f"\n🎉 Done! Open {output_file} in your browser")

if __name__ == '__main__':
    main()
