#!/usr/bin/env python3
"""
Script to generate the HTML site for GitHub Pages with fullscreen examples.
Creates a custom i        .search-container {
            margin-bottom: 20px;
            position: relative;
        }
        
        .search-box {
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .spinner {
            display: none;
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            width: 20px;
            height: 20px;
            border: 3px solid rgba(102, 126, 234, 0.3);
            border-radius: 50%;
            border-top-color: #667eea;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: translateY(-50%) rotate(360deg); }
        }t displays NHANES variables interactively
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
    <title>NHANES Variables Explorer</title>
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
            color: inherit;
            transition: transform 0.3s, box-shadow 0.3s;
            border: 2px solid transparent;
            cursor: pointer;
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
        
        /* Modal Styles */
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
            justify-content: center;
            align-items: center;
        }}
        
        .modal.show {{
            opacity: 1;
        }}
        
        .modal-content {{
            position: relative;
            width: 95%;
            height: 95%;
            background-color: white;
            border-radius: 10px;
            overflow: hidden;
            transform: scale(0.9);
            transition: transform 0.3s ease;
        }}
        
        .modal.show .modal-content {{
            transform: scale(1);
        }}
        
        .close-modal {{
            position: absolute;
            right: 15px;
            top: 10px;
            font-size: 30px;
            font-weight: bold;
            color: #333;
            cursor: pointer;
            z-index: 1001;
            opacity: 0;
            transition: opacity 0.3s ease;
        }}
        
        .modal.show .close-modal {{
            opacity: 1;
        }}
        
        #example-iframe {{
            width: 100%;
            height: 100%;
            border: none;
            opacity: 0;
            transition: opacity 0.5s ease;
        }}
        
        .iframe-loaded {{
            opacity: 1 !important;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="section">
            <h2> Interactive Analysis Examples</h2>
            <p>Explore comprehensive health and nutrition analysis examples with interactive visualizations:</p>
            <div class="examples-grid">
'''

    # Add example cards with data-src attribute for modal loading
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
                <div class="example-card" data-src="{example['path']}">
                    <h3>{example['name']}</h3>
                    <p>{description}</p>
                </div>
'''
    
    html_content += f'''
            </div>
        </div>
        
        <div class="section">
            <h2>🔍 NHANES Variables Database</h2>
            <div class="search-container">
                <input type="text" class="search-box" id="search-input" 
                       placeholder="Search variables by name, description, dataset, or cycle...">
                <div class="spinner" id="search-spinner"></div>
            </div>
            <div class="table-container">
                <table id="variables-table">
                    <thead>
                        <tr>
                            <th>Variable Name</th>
                            <th>Variable Explanation</th>
                            <th>Dataset</th>
                            <th>Cycle</th>
                            <th>Dataset Links</th>
                        </tr>
                    </thead>
                    <tbody id="table-body">
                        <!-- Table content will be populated by JavaScript -->
                    </tbody>
                </table>
            </div>
            <div class="row-count" id="row-count">Showing {len(df):,} variables</div>
        </div>
    </div>
'''
    
    html_content += f'''
            </div>
        </div>
    </div>
    
    <!-- Modal for fullscreen examples -->
    <div class="modal" id="example-modal">
        <div class="modal-content">
            <span class="close-modal">&times;</span>
            <iframe id="example-iframe" frameborder="0"></iframe>
        </div>
    </div>
    
    <div class="footer">
        <p>Generated by <a href="https://github.com/jeromevde/Pandas-Nhanes">pandas-nhanes</a> | 
           Data source: <a href="https://www.cdc.gov/nchs/nhanes/">CDC NHANES</a></p>
    </div>
    
    <script>
        // Modal functionality
        const modal = document.getElementById('example-modal');
        const modalIframe = document.getElementById('example-iframe');
        const closeModalBtn = document.querySelector('.close-modal');
        const exampleCards = document.querySelectorAll('.example-card');
        
        exampleCards.forEach(function(card) {{
            card.addEventListener('click', function() {{
                const src = card.getAttribute('data-src');
                modal.style.display = 'flex';
                document.body.style.overflow = 'hidden';
                
                // Clear previous iframe content
                modalIframe.src = '';
                modalIframe.style.opacity = '0';
                
                // Add show class for animation
                setTimeout(() => {{
                    modal.classList.add('show');
                }}, 10);
                
                // Set the new src after a short delay
                setTimeout(() => {{
                    modalIframe.src = src;
                    
                    // When iframe loads, fade it in
                    modalIframe.onload = function() {{
                        modalIframe.style.opacity = '1';
                    }};
                }}, 300);
            }});
        }});
        
        closeModalBtn.addEventListener('click', function() {{
            modal.classList.remove('show');
            modalIframe.style.opacity = '0';
            
            // Hide modal after animation completes
            setTimeout(() => {{
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
                modalIframe.src = '';
            }}, 300);
        }});
        
        window.addEventListener('click', function(event) {{
            if (event.target === modal) {{
                modal.classList.remove('show');
                modalIframe.style.opacity = '0';
                
                // Hide modal after animation completes
                setTimeout(() => {{
                    modal.style.display = 'none';
                    document.body.style.overflow = 'auto';
                    modalIframe.src = '';
                }}, 300);
            }}
        }});
        
        // NHANES variables data
        const variablesData = {df_json};
        
        // DOM elements
        const searchInput = document.getElementById('search-input');
        const tableBody = document.getElementById('table-body');
        const rowCount = document.getElementById('row-count');
        const searchSpinner = document.getElementById('search-spinner');
        
        // Current filtered data and search state
        let filteredData = variablesData;
        let searchInProgress = false;
        let pendingSearchTerm = null;
        
        // Render table
        function renderTable(data) {{
            tableBody.innerHTML = '';
            
            data.forEach(function(row) {{
                const tr = document.createElement('tr');
                
                // Format dataset links
                let datasetLink = '';
                if (row['dataset link']) {{
                    datasetLink = `<a href="${{row['dataset link']}}" target="_blank">Data</a>`;
                }}
                if (row['dataset documentation link']) {{
                    datasetLink += ` | <a href="${{row['dataset documentation link']}}" target="_blank">Docs</a>`;
                }}
                
                tr.innerHTML = `
                    <td><strong>${{row['variable name'] || ''}}</strong></td>
                    <td>${{row['variable explanation'] || ''}}</td>
                    <td>${{row['dataset'] || ''}}</td>
                    <td>${{row['cycle name'] || ''}}</td>
                    <td>${{datasetLink}}</td>
                `;
                tableBody.appendChild(tr);
            }});
            
            rowCount.textContent = `Showing ${{data.length.toLocaleString()}} of ${{variablesData.length.toLocaleString()}} variables`;
        }}
        
        // Filter data based on search term - completely non-blocking
        function filterData(searchTerm) {{
            // Show spinner immediately
            searchSpinner.style.display = 'block';
            
            // If a search is already in progress, store this term to be processed next
            if (searchInProgress) {{
                pendingSearchTerm = searchTerm;
                return;
            }}
            
            // Mark that we're starting a search
            searchInProgress = true;
            
            // Start the actual filtering in the next event loop tick
            setTimeout(() => {{
                // Process the search
                processSearch(searchTerm);
                
                // After search completes, check if we have a pending search
                searchInProgress = false;
                if (pendingSearchTerm !== null) {{
                    const nextSearch = pendingSearchTerm;
                    pendingSearchTerm = null;
                    filterData(nextSearch); // Process the most recent pending search
                }}
            }}, 0);
        }}
        
        // Actual search processing function
        function processSearch(searchTerm) {{
            if (!searchTerm) {{
                filteredData = variablesData;
                renderTable(filteredData);
                searchSpinner.style.display = 'none';
                return;
            }}
            
            const term = searchTerm.toLowerCase();
            filteredData = variablesData.filter(function(row) {{
                return (row['variable name'] && row['variable name'].toLowerCase().includes(term)) ||
                       (row['variable explanation'] && row['variable explanation'].toLowerCase().includes(term)) ||
                       (row.dataset && row.dataset.toLowerCase().includes(term)) ||
                       (row['cycle name'] && row['cycle name'].toLowerCase().includes(term)) ||
                       (row.type && row.type.toLowerCase().includes(term));
            }});
            
            renderTable(filteredData);
            searchSpinner.style.display = 'none';
        }}
        
        // Debounce function with immediate spinner feedback
        function debounce(func, wait) {{
            let timeout;
            return function(...args) {{
                // Show spinner when user types (gives immediate feedback)
                searchSpinner.style.display = 'block';
                
                // Clear any previous timeout
                clearTimeout(timeout);
                
                // Set a new timeout
                timeout = setTimeout(() => {{
                    // Only execute if we still have this timeout (it wasn't cleared)
                    func.apply(this, args);
                }}, wait);
            }};
        }}
        
        // Search input event listener with debounce
        const debouncedSearch = debounce(function(e) {{
            filterData(e.target.value);
        }}, 300);
        
        searchInput.addEventListener('input', debouncedSearch);
        
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
