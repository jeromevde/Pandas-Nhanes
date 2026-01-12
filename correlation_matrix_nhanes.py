#!/usr/bin/env python3
"""
Interactive Correlation Matrix Generator for NHANES Data
Generates HTML with clickable correlation matrix that shows X-Y scatter plots on click.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import base64
from io import StringIO

def generate_interactive_correlation_html(df, cohort_name, numeric_columns=None):
    """
    Generate an interactive HTML correlation matrix for a given cohort.
    
    Args:
        df: DataFrame with NHANES data
        cohort_name: Name of the cohort (e.g., "2017-2018")
        numeric_columns: List of numeric columns to include (optional)
    
    Returns:
        HTML string with interactive correlation matrix
    """
    # Select numeric columns if not provided
    if numeric_columns is None:
        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    # Filter to only numeric columns with sufficient variance
    valid_cols = []
    for col in numeric_columns:
        if df[col].std() > 0 and df[col].notna().sum() > 10:  # Need some variance and data
            valid_cols.append(col)
    
    if len(valid_cols) < 2:
        return None
    
    # Calculate correlation matrix
    corr_matrix = df[valid_cols].corr()
    
    # Create hover text with correlation values
    hover_text = corr_matrix.round(3).astype(str)
    
    # Create the heatmap
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        text=corr_matrix.round(3).values,
        texttemplate="%{text}",
        textfont={"size": 10},
        colorscale='RdBu_r',
        zmin=-1,
        zmax=1,
        hoverongaps=False,
        hovertemplate='<b>X:</b> %{x}<br><b>Y:</b> %{y}<br><b>Correlation:</b> %{z:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'Correlation Matrix - {cohort_name}',
        xaxis_title='Variables',
        yaxis_title='Variables',
        width=800,
        height=800
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def generate_scatter_html(df, x_col, y_col, cohort_name):
    """
    Generate an HTML scatter plot for two variables.
    """
    # Remove NaN values for the two columns
    plot_df = df[[x_col, y_col]].dropna()
    
    if len(plot_df) < 3:
        return "<p>Not enough data points to generate scatter plot.</p>"
    
    fig = px.scatter(
        plot_df, 
        x=x_col, 
        y=y_col,
        title=f'{x_col} vs {y_col} ({cohort_name})',
        trendline="ols",
        opacity=0.6
    )
    
    # Add correlation to title
    corr = plot_df[x_col].corr(plot_df[y_col])
    fig.update_layout(
        title=f'{x_col} vs {y_col} ({cohort_name})<br><sub>Correlation: {corr:.3f}, n={len(plot_df)}</sub>'
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def generate_complete_html(df, cohort_name, output_file):
    """
    Generate a complete HTML page with clickable correlation matrix.
    Clicking on a cell shows the scatter plot.
    """
    # Get numeric columns
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    valid_cols = []
    for col in numeric_columns:
        if df[col].std() > 0 and df[col].notna().sum() > 10:
            valid_cols.append(col)
    
    if len(valid_cols) < 2:
        print(f"Not enough valid numeric columns for {cohort_name}")
        return
    
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
                    # Create hover text
                    hover_text = [f"{x}: {plot_df[x].iloc[k]:.2f}<br>{y}: {plot_df[y].iloc[k]:.2f}" 
                                  for k in range(len(plot_df))]
                    
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
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Correlation Matrix - {cohort_name}</title>
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
        .cohort-selector {{
            text-align: center;
            margin-bottom: 20px;
        }}
        select {{
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 5px;
            border: 1px solid #ccc;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Interactive Correlation Matrix - {cohort_name}</h1>
        
        <div class="instructions">
            <strong>👆 Click on any cell</strong> in the correlation matrix below to see an X-Y scatter plot of those two variables!
        </div>
        
        <div class="matrix-container">
            <div id="correlation-matrix"></div>
        </div>
        
        <div id="scatter-plot"></div>
    </div>

    <script>
        // Embedded correlation matrix data
        const corrData = JSON.parse(atob('{corr_b64}'));
        const scatterData = JSON.parse(atob('{scatter_b64}'));
        const validCols = {json.dumps(valid_cols)};
        
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
            x: validCols,
            y: validCols,
            text: textValues,
            texttemplate: "%{text}",
            textfont: {{size: 10}},
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
            
            if (xCol === yCol) return; // Skip diagonal
            
            showScatterPlot(xCol, yCol);
        }});
        
        function showScatterPlot(xCol, yCol) {{
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
                        text: xCol + ' vs ' + yCol + '<br><sub>Correlation: ' + d.correlation + ', n=' + d.n + '</sub>',
                        font: {{size: 18}}
                    }},
                    xaxis: {{title: xCol}},
                    yaxis: {{title: yCol}},
                    hovermode: 'closest'
                }};
                
                Plotly.newPlot('scatter-plot', [trace], layout);
                plotDiv.classList.add('visible');
                
                // Scroll to scatter plot
                plotDiv.scrollIntoView({{behavior: 'smooth', block: 'start'}});
            }} else {{
                plotDiv.innerHTML = '<p style="text-align:center;padding:20px;">Not enough data for this pair of variables.</p>';
                plotDiv.classList.add('visible');
            }}
        }}
    </script>
</body>
</html>'''
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"Generated: {output_file}")
    return output_file

def main():
    """
    Main function to generate interactive correlation matrices for all NHANES cohorts.
    """
    # Example: Load your NHANES data
    # Replace this with your actual data loading code
    # df = pd.read_csv('your_nhanes_data.csv')
    
    # If you have multiple cohorts in separate files:
    # cohorts = {
    #     '2017-2018': pd.read_csv('nhanes_2017_2018.csv'),
    #     '2015-2016': pd.read_csv('nhanes_2015_2016.csv'),
    #     '2013-2014': pd.read_csv('nhanes_2013_2014.csv'),
    # }
    
    # For demo, create sample data
    import numpy as np
    
    # Sample NHANES-like data
    np.random.seed(42)
    n = 500
    
    cohorts = {{
        '2017-2018': pd.DataFrame({{
            'Age': np.random.randint(18, 80, n),
            'BMI': np.random.normal(28, 6, n),
            'Systolic_BP': np.random.normal(120, 15, n),
            'Diastolic_BP': np.random.normal(80, 10, n),
            'Cholesterol': np.random.normal(200, 40, n),
            'Glucose': np.random.normal(100, 20, n),
            'Hemoglobin': np.random.normal(14, 2, n),
            'Creatinine': np.random.normal(1, 0.3, n)
        }}),
        '2015-2016': pd.DataFrame({{
            'Age': np.random.randint(18, 80, n),
            'BMI': np.random.normal(27, 6, n),
            'Systolic_BP': np.random.normal(118, 15, n),
            'Diastolic_BP': np.random.normal(78, 10, n),
            'Cholesterol': np.random.normal(195, 40, n),
            'Glucose': np.random.normal(98, 20, n),
            'Hemoglobin': np.random.normal(13.8, 2, n),
            'Creatinine': np.random.normal(0.95, 0.3, n)
        }})
    }}
    
    # Add some correlations to make it realistic
    for cohort_name, df in cohorts.items():
        # BMI and BP correlation
        df['Systolic_BP'] += df['BMI'] * 0.5 + np.random.normal(0, 10, n)
        df['Diastolic_BP'] += df['BMI'] * 0.3 + np.random.normal(0, 8, n)
        # Glucose and Cholesterol correlation
        df['Cholesterol'] += df['Glucose'] * 0.3 + np.random.normal(0, 30, n)
    
    # Generate HTML files for each cohort
    output_dir = 'correlation_matrices'
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    for cohort_name, df in cohorts.items():
        output_file = os.path.join(output_dir, f'correlation_matrix_{cohort_name.replace("-", "_")}.html')
        generate_complete_html(df, cohort_name, output_file)
    
    print(f"\\n✅ Generated interactive correlation matrices for {len(cohorts)} cohorts!")
    print(f"📁 Output directory: {output_dir}")

if __name__ == '__main__':
    main()
