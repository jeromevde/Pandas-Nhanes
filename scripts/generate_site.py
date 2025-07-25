#!/usr/bin/env python3
"""
Script to generate the HTML site for GitHub Pages.
Creates a custom index.html that displays NHANES variables interactively
and showcases all HTML examples from the Examples directory.
"""

import os
import sys
import pandas as pd
import glob
import json

# Add the package to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def generate_site():
    """Generate the HTML site for GitHub Pages"""
    
    # Create site directory
    site_dir = 'site'
    os.makedirs(site_dir, exist_ok=True)
    
    # Load NHANES variables CSV
    print("Loading NHANES variables CSV...")
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'pandas_nhanes', 'nhanes_variables.csv')
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} variables from CSV")
    
    # Convert DataFrame to JSON for JavaScript
    df_json = df.to_json(orient='records')
    
    # Find all HTML files in Examples directory
    print("Finding HTML examples...")
    examples_dir = os.path.join(os.path.dirname(__file__), '..', 'Examples')
    html_files = glob.glob(os.path.join(examples_dir, '*.html'))
    json_files = glob.glob(os.path.join(examples_dir, '*.json'))
    
    # Create example entries with metadata
    examples = []
    
    # Copy all HTML files to site directory
    for html_file in html_files:
        filename = os.path.basename(html_file)
        name = filename.replace('_interactive.html', '').replace('_', ' ').title()
        
        # Copy HTML file to site directory
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        output_path = os.path.join(site_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        examples.append({
            'name': name,
            'filename': filename,
            'path': filename
        })
    
    # Copy all JSON files to site directory
    json_count = 0
    for json_file in json_files:
        filename = os.path.basename(json_file)
        
        # Copy JSON file to site directory
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        output_path = os.path.join(site_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        json_count += 1
    
    print(f"Found {len(examples)} HTML examples and {json_count} JSON files")
    
    # Create the main index.html
    html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NHANES Data Explorer</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            background: white;
            border-radius: 15px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 3em;
            color: #4a5568;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.2em;
            color: #718096;
            margin-bottom: 20px;
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 20px;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .section {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .section h2 {{
            font-size: 2em;
            color: #4a5568;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .search-container {{
            margin-bottom: 20px;
        }}
        
        .search-box {{
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            outline: none;
            transition: border-color 0.3s;
        }}
        
        .search-box:focus {{
            border-color: #667eea;
        }}
        
        .table-container {{
            overflow-x: auto;
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        th {{
            background: #f7fafc;
            font-weight: 600;
            color: #4a5568;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        tr:hover {{
            background: #f7fafc;
        }}
        
        .examples-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .example-card {{
            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
            border-radius: 10px;
            padding: 20px;
            text-decoration: none;
            color: inherit;
            transition: transform 0.3s, box-shadow 0.3s;
            border: 2px solid transparent;
        }}
        
        .example-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.1);
            border-color: #667eea;
        }}
        
        .example-card h3 {{
            color: #4a5568;
            margin-bottom: 10px;
            font-size: 1.3em;
        }}
        
        .example-card p {{
            color: #718096;
            font-size: 0.9em;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            padding: 20px;
        }}
        
        .footer a {{
            color: white;
            text-decoration: none;
        }}
        
        .footer a:hover {{
            text-decoration: underline;
        }}
        
        .row-count {{
            margin-top: 10px;
            color: #718096;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>NHANES Data Explorer</h1>
            <p>Interactive exploration of National Health and Nutrition Examination Survey variables and analysis examples</p>
            <div class="stats">
                <div class="stat">
                    <div class="stat-number" id="total-variables">{len(df):,}</div>
                    <div class="stat-label">Variables</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{df['dataset'].nunique():,}</div>
                    <div class="stat-label">Datasets</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{len(examples)}</div>
                    <div class="stat-label">Examples</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🔍 NHANES Variables Database</h2>
            <div class="search-container">
                <input type="text" class="search-box" id="search-input" 
                       placeholder="Search variables by name, description, dataset, or cycle...">
            </div>
            <div class="table-container">
                <table id="variables-table">
                    <thead>
                        <tr>
                            <th>Variable</th>
                            <th>Description</th>
                            <th>Dataset</th>
                            <th>Cycle</th>
                            <th>Type</th>
                        </tr>
                    </thead>
                    <tbody id="table-body">
                        <!-- Table content will be populated by JavaScript -->
                    </tbody>
                </table>
            </div>
            <div class="row-count" id="row-count">Showing {len(df):,} variables</div>
        </div>
        
        <div class="section">
            <h2>📊 Interactive Analysis Examples</h2>
            <p>Explore comprehensive health and nutrition analysis examples with interactive visualizations:</p>
            <div class="examples-grid">
'''

    # Add example cards
    example_descriptions = {
        'BMD Age Gender': 'Comprehensive bone mineral density analysis across 13 body regions by age and gender',
        'Cholesterol Age': 'HDL, LDL, and total cholesterol levels distribution across age groups', 
        'Testosterone Age Gender': 'Testosterone hormone levels by age with gender-specific analysis',
        'Estradiol Age Gender': 'Estradiol hormone levels showing age-related patterns by gender',
        'Testosterone Estrogen Ratio': 'Testosterone to estrogen ratio analysis in men across age groups'
    }
    
    for example in examples:
        description = example_descriptions.get(example['name'], 'Interactive visualization and statistical analysis')
        html_content += f'''
                <a href="{example['path']}" class="example-card">
                    <h3>{example['name']}</h3>
                    <p>{description}</p>
                </a>
'''
    
    html_content += f'''
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>Generated by <a href="https://github.com/jeromevde/Pandas-Nhanes">pandas-nhanes</a> | 
           Data source: <a href="https://www.cdc.gov/nchs/nhanes/">CDC NHANES</a></p>
    </div>
    
    <script>
        // NHANES variables data
        const variablesData = {df_json};
        
        // DOM elements
        const searchInput = document.getElementById('search-input');
        const tableBody = document.getElementById('table-body');
        const rowCount = document.getElementById('row-count');
        const totalVariables = document.getElementById('total-variables');
        
        // Current filtered data
        let filteredData = variablesData;
        
        // Render table
        function renderTable(data) {{
            tableBody.innerHTML = '';
            
            data.forEach(row => {{
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${{row.variable || ''}}</strong></td>
                    <td>${{row.description || ''}}</td>
                    <td>${{row.dataset || ''}}</td>
                    <td>${{row['cycle name'] || ''}}</td>
                    <td>${{row.type || ''}}</td>
                `;
                tableBody.appendChild(tr);
            }});
            
            rowCount.textContent = `Showing ${{data.length.toLocaleString()}} of ${{variablesData.length.toLocaleString()}} variables`;
        }}
        
        // Filter data based on search term
        function filterData(searchTerm) {{
            if (!searchTerm) {{
                filteredData = variablesData;
            }} else {{
                const term = searchTerm.toLowerCase();
                filteredData = variablesData.filter(row => {{
                    return (row.variable && row.variable.toLowerCase().includes(term)) ||
                           (row.description && row.description.toLowerCase().includes(term)) ||
                           (row.dataset && row.dataset.toLowerCase().includes(term)) ||
                           (row['cycle name'] && row['cycle name'].toLowerCase().includes(term)) ||
                           (row.type && row.type.toLowerCase().includes(term));
                }});
            }}
            renderTable(filteredData);
        }}
        
        // Search input event listener
        searchInput.addEventListener('input', (e) => {{
            filterData(e.target.value);
        }});
        
        // Initial render
        renderTable(variablesData);
    </script>
</body>
</html>
'''
    
    # Write the HTML file
    html_path = os.path.join(site_dir, 'index.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Site generated successfully at: {html_path}")
    print(f"Total file size: {os.path.getsize(html_path) / 1024:.1f} KB")
    print(f"Included {len(examples)} HTML examples and {json_count} JSON files")

if __name__ == "__main__":
    generate_site()
