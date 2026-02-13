#!/usr/bin/env python3
"""
Generate correlation matrices for NHANES data using pandas_nhanes package.
Downloads actual data from NHANES and generates interactive HTML visualizations.
"""

import pandas as pd
import plotly.graph_objects as go
import json
import base64
import os
import numpy as np

# Variables to analyze (common across many cycles)
VARIABLES = ['BMXBMI', 'LBXGLU', 'LBXTC', 'LBXTR', 'BPXSY1', 'BPXDI1']

# Cohorts to analyze
COHORTS = ['2017-2018', '2015-2016', '2013-2014', '2011-2012']

def load_cohort_data(cycle, variables):
    """Load data for a specific NHANES cycle."""
    from pandas_nhanes import get_cycle_variables
    
    print(f"\n📥 Loading {cycle}...")
    df = get_cycle_variables(cycle, *variables)
    print(f"   Loaded {len(df)} rows with {len(df.columns)} columns")
    return df

def generate_complete_html(df, cohort_name, output_file):
    """
    Generate a complete HTML page with clickable correlation matrix.
    """
    # Get numeric columns
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    # Filter to valid columns with variance
    valid_cols = []
    for col in numeric_columns:
        if df[col].std() > 0 and df[col].notna().sum() > 10:
            valid_cols.append(col)
    
    if len(valid_cols) < 2:
        print(f"⚠️ Not enough valid numeric columns for {cohort_name}")
        return None
    
    # Calculate correlation matrix
    corr_matrix = df[valid_cols].corr()
    
    # Create JSON data for the scatter plots
    scatter_data = {}
    for i, y_col in enumerate(valid_cols):
        for j, x_col in enumerate(valid_cols):
            if i != j:
                key = f"{x_col}|{y_col}"
                plot_df = df[[x_col, y_col]].dropna()
                if len(plot_df) >= 3:
                    scatter_data[key] = {
                        'x': plot_df[x_col].tolist(),
                        'y': plot_df[y_col].tolist(),
                        'xlabel': x_col,
                        'ylabel': y_col,
                        'correlation': round(plot_df[x_col].corr(plot_df[y_col]), 3),
                        'n': len(plot_df)
                    }
    
    # Convert to JSON and encode
    scatter_json = json.dumps(scatter_data)
    scatter_b64 = base64.b64encode(scatter_json.encode()).decode()
    
    # Generate correlation matrix as JSON for JavaScript
    corr_json = corr_matrix.to_json()
    corr_b64 = base64.b64encode(corr_json.encode()).decode()
    
    # Variable descriptions for better labels
    var_descriptions = {
        'BMXBMI': 'BMI (Body Mass Index)',
        'LBXGLU': 'Glucose (mg/dL)',
        'LBXTC': 'Total Cholesterol (mg/dL)',
        'LBXTR': 'Triglycerides (mg/dL)',
        'BPXSY1': 'Systolic Blood Pressure',
        'BPXDI1': 'Diastolic Blood Pressure'
    }
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NHANES Correlation Matrix - {cohort_name}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        h2 {{
            color: #666;
            text-align: center;
            font-weight: normal;
        }}
        .matrix-container {{
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }}
        #correlation-matrix {{
            width: 100%;
            max-width: 800px;
        }}
        #scatter-plot {{
            width: 100%;
            height: 600px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background: white;
            display: none;
        }}
        #scatter-plot.visible {{
            display: block;
        }}
        .instructions {{
            text-align: center;
            color: #666;
            margin-bottom: 20px;
            padding: 15px;
            background: #e8f4f8;
            border-radius: 5px;
        }}
        .data-info {{
            text-align: center;
            color: #888;
            font-size: 14px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>NHANES Correlation Matrix</h1>
        <h2>Cohort: {cohort_name}</h2>
        
        <div class="data-info">
            Variables: {', '.join([var_descriptions.get(v, v) for v in valid_cols])}
        </div>
        
        <div class="instructions">
            <strong>👆 Click on any cell</strong> in the correlation matrix below to see an X-Y scatter plot!
        </div>
        
        <div class="matrix-container">
            <div id="correlation-matrix"></div>
        </div>
        
        <div id="scatter-plot"></div>
    </div>

    <script>
        const corrData = JSON.parse(atob('{corr_b64}'));
        const scatterData = JSON.parse(atob('{scatter_b64}'));
        const validCols = {json.dumps(valid_cols)};
        const varDescriptions = {json.dumps(var_descriptions)};
        
        // Extract matrix values
        const zValues = [];
        const textValues = [];
        
        for (let i = 0; i < validCols.length; i++) {{
            const row = [];
            const textRow = [];
            for (let j = 0; j < validCols.length; j++) {{
                const corr = corrData[validCols[i]][validCols[j]];
                row.push(corr);
                textRow.push(corr.toFixed(3));
            }}
            zValues.push(row);
            textValues.push(textRow);
        }}
        
        // Create heatmap
        const data = [{{
            z: zValues,
            x: validCols.map(c => varDescriptions[c] || c),
            y: validCols.map(c => varDescriptions[c] || c),
            text: textValues,
            texttemplate: "%{{text}}",
            textfont: {{size: 12}},
            type: 'heatmap',
            colorscale: 'RdBu_r',
            zmin: -1,
            zmax: 1,
            hoverongaps: false,
            hovertemplate: '<b>X:</b> %{{x}}<br><b>Y:</b> %{{y}}<br><b>Correlation:</b> %{{z:.3f}}<extra></extra>'
        }}];
        
        const layout = {{
            title: 'Click on a cell to see scatter plot',
            xaxis: {{title: 'Variables', tickangle: 45}},
            yaxis: {{title: 'Variables', automargin: true}},
            width: 800,
            height: 800,
            clickmode: 'event+select'
        }};
        
        Plotly.newPlot('correlation-matrix', data, layout);
        
        // Handle click events
        document.getElementById('correlation-matrix').on('plotly_click', function(data) {{
            const xCol = data.points[0].x;
            const yCol = data.points[0].y;
            
            // Find original column names
            const xOrig = validCols.find(c => (varDescriptions[c] || c) === xCol);
            const yOrig = validCols.find(c => (varDescriptions[c] || c) === yCol);
            
            if (xOrig === yOrig) return;
            
            showScatterPlot(xOrig, yOrig, xCol, yCol);
        }});
        
        function showScatterPlot(xCol, yCol, xLabel, yLabel) {{
            const key = xCol + '|' + yCol;
            const plotDiv = document.getElementById('scatter-plot');
            
            if (scatterData[key]) {{
                const d = scatterData[key];
                
                const trace = {{
                    x: d.x,
                    y: d.y,
                    mode: 'markers',
                    type: 'scatter',
                    marker: {{
                        size: 8,
                        opacity: 0.6,
                        color: 'steelblue'
                    }},
                    hovertemplate: '<b>X:</b> %{{x:.2f}}<br><b>Y:</b> %{{y:.2f}}<extra></extra>'
                }};
                
                const layout = {{
                    title: {{
                        text: xLabel + ' vs ' + yLabel + '<br><sub>Correlation: ' + d.correlation + ', n=' + d.n + '</sub>',
                        font: {{size: 18}}
                    }},
                    xaxis: {{title: xLabel}},
                    yaxis: {{title: yLabel}},
                    hovermode: 'closest'
                }};
                
                Plotly.newPlot('scatter-plot', [trace], layout);
                plotDiv.classList.add('visible');
                
                plotDiv.scrollIntoView({{behavior: 'smooth', block: 'start'}});
            }} else {{
                plotDiv.innerHTML = '<p style="text-align:center;padding:20px;">Not enough data for this pair.</p>';
                plotDiv.classList.add('visible');
            }}
        }}
    </script>
</body>
</html>'''
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Generated: {output_file}")
    return output_file

def main():
    """Main function to generate correlation matrices for all NHANES cohorts."""
    
    print("=" * 60)
    print("NHANES Correlation Matrix Generator")
    print("=" * 60)
    
    # Process each cohort
    for cohort in COHORTS:
        print(f"\n{'='*60}")
        print(f"Processing: {cohort}")
        print("=" * 60)
        
        # Load data using pandas_nhanes
        df = load_cohort_data(cohort, VARIABLES)
        
        if df.empty or len(df) < 10:
            print(f"⚠️ Not enough data for {cohort}")
            continue
        
        # Generate HTML (output to same directory as script)
        output_file = f'correlation_matrix_{cohort.replace("-", "_")}.html'
        generate_complete_html(df, cohort, output_file)
    
    print(f"\n{'='*60}")
    print("✅ All correlation matrices generated!")
    print(f"📁 Output directory: {output_dir}")
    print("=" * 60)

if __name__ == '__main__':
    main()
