#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Paths
const rootDir = __dirname;
const examplesDir = path.join(rootDir, 'Examples');
const distDir = path.join(rootDir, 'dist');

// Create dist directory
if (!fs.existsSync(distDir)) {
  fs.mkdirSync(distDir, { recursive: true });
}

// Function to copy HTML files from Examples to dist
function copyExampleFiles() {
  console.log('Copying example files...');
  
  const htmlFiles = fs.readdirSync(examplesDir)
    .filter(file => file.endsWith('.html'))
    .map(file => ({
      name: file.replace('_interactive.html', '').replace(/_/g, ' '),
      path: file,
      originalName: file
    }));

  // Copy HTML files
  htmlFiles.forEach(example => {
    const srcPath = path.join(examplesDir, example.originalName);
    const destPath = path.join(distDir, example.originalName);
    fs.copyFileSync(srcPath, destPath);
  });

  console.log(`Copied ${htmlFiles.length} HTML files`);
  return htmlFiles;
}

// Function to load NHANES variables data
function loadNhanesData() {
  console.log('Loading NHANES variables data...');
  
  try {
    const csvPath = path.join(rootDir, 'pandas_nhanes', 'nhanes_variables.csv');
    if (!fs.existsSync(csvPath)) {
      console.warn('NHANES variables CSV not found');
      return [];
    }
    
    // Create a temporary Python script to convert CSV to JSON
    const tempScript = path.join(rootDir, 'temp_csv_to_json.py');
    const pythonCode = `import pandas as pd
import json
import sys

try:
    print("Loading CSV...", file=sys.stderr)
    df = pd.read_csv('${csvPath.replace(/\\/g, '/')}')
    print(f"Loaded {len(df)} rows", file=sys.stderr)
    
    # Convert to JSON with proper handling of large data
    print("Converting to JSON...", file=sys.stderr)
    json_data = df.to_json(orient='records', force_ascii=False)
    print(json_data)
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
`;
    
    fs.writeFileSync(tempScript, pythonCode);
    const { execSync } = require('child_process');
    
    // Use increased buffer size and timeout for large data
    const result = execSync(`python3 "${tempScript}"`, { 
      encoding: 'utf8',
      maxBuffer: 50 * 1024 * 1024, // 50MB buffer
      timeout: 30000 // 30 second timeout
    });
    
    // Clean up temp file
    fs.unlinkSync(tempScript);
    
    const data = JSON.parse(result);
    console.log(`Loaded ${data.length} NHANES variables`);
    return data;
  } catch (error) {
    console.warn('Could not load NHANES data:', error.message);
    console.warn('The variables explorer will be disabled. Install pandas and ensure sufficient memory.');
    // Clean up temp file if it exists
    const tempScript = path.join(rootDir, 'temp_csv_to_json.py');
    if (fs.existsSync(tempScript)) {
      fs.unlinkSync(tempScript);
    }
    return [];
  }
}

// Function to generate the main index.html
function generateIndexHtml(examples, nhanesData = []) {
  console.log('Generating index.html...');
  
  const exampleDescriptions = {
    'BMD Age Gender': 'Comprehensive bone mineral density analysis across 13 body regions by age and gender',
    'Cholesterol Age': 'HDL, LDL, and total cholesterol levels distribution across age groups',
    'Testosterone Age Gender': 'Testosterone hormone levels by age with gender-specific analysis',
    'Estradiol Age Gender': 'Estradiol hormone levels showing age-related patterns by gender',
    'Testosterone Estrogen Ratio': 'Testosterone to estrogen ratio analysis in men across age groups'
  };

  const exampleCards = examples.map(example => {
    const description = exampleDescriptions[example.name] || 'Interactive visualization and statistical analysis';
    return `
                <div class="example-card" data-src="${example.path}">
                    <h3>${example.name}</h3>
                    <p>${description}</p>
                </div>`;
  }).join('');

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NHANES Variables Explorer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .section h2 {
            font-size: 2em;
            color: #4a5568;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        
        .search-container {
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
        
        .search-box:focus {
            border-color: #667eea;
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
        }
        
        .table-container {
            overflow-x: auto;
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        
        th {
            background: #f7fafc;
            font-weight: 600;
            color: #4a5568;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        tr:hover {
            background: #f7fafc;
        }
        
        .row-count {
            margin-top: 10px;
            color: #718096;
            font-style: italic;
        }
        
        .no-data-message {
            text-align: center;
            color: #718096;
            font-style: italic;
            padding: 40px;
        }
        
        .examples-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .example-card {
            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
            border-radius: 10px;
            padding: 20px;
            color: inherit;
            transition: transform 0.3s, box-shadow 0.3s;
            border: 2px solid transparent;
            cursor: pointer;
        }
        
        .example-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.1);
            border-color: #667eea;
        }
        
        .example-card h3 {
            color: #4a5568;
            margin-bottom: 10px;
            font-size: 1.3em;
        }
        
        .example-card p {
            color: #718096;
            font-size: 0.9em;
        }
        
        .footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            padding: 20px;
        }
        
        .footer a {
            color: white;
            text-decoration: none;
        }
        
        .footer a:hover {
            text-decoration: underline;
        }
        
        /* Modal Styles */
        .modal {
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
        }
        
        .modal.show {
            opacity: 1;
        }
        
        .modal-content {
            position: relative;
            width: 95%;
            height: 95%;
            background-color: white;
            border-radius: 10px;
            overflow: hidden;
            transform: scale(0.9);
            transition: transform 0.3s ease;
        }
        
        .modal.show .modal-content {
            transform: scale(1);
        }
        
        .close-modal {
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
        }
        
        .modal.show .close-modal {
            opacity: 1;
        }
        
        #example-iframe {
            width: 100%;
            height: 100%;
            border: none;
            opacity: 0;
            transition: opacity 0.5s ease;
        }
        
        .iframe-loaded {
            opacity: 1 !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="section">
            <h2>📊 Interactive Analysis Examples</h2>
            <p>Explore comprehensive health and nutrition analysis examples with interactive visualizations:</p>
            <div class="examples-grid">${exampleCards}
            </div>
        </div>
        
        <div class="section">
            <h2>🔍 NHANES Variables Database</h2>
            ${nhanesData.length > 0 ? `
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
            <div class="row-count" id="row-count">Showing ${nhanesData.length.toLocaleString()} variables</div>
            ` : `
            <div class="no-data-message">
                <p>NHANES variables data not available. Install pandas with <code>pip install pandas</code> to enable the variables database.</p>
            </div>
            `}
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
        
        exampleCards.forEach(function(card) {
            card.addEventListener('click', function() {
                const src = card.getAttribute('data-src');
                modal.style.display = 'flex';
                document.body.style.overflow = 'hidden';
                
                // Clear previous iframe content
                modalIframe.src = '';
                modalIframe.style.opacity = '0';
                
                // Add show class for animation
                setTimeout(() => {
                    modal.classList.add('show');
                }, 10);
                
                // Set the new src after a short delay
                setTimeout(() => {
                    modalIframe.src = src;
                    
                    // When iframe loads, fade it in
                    modalIframe.onload = function() {
                        modalIframe.style.opacity = '1';
                    };
                }, 300);
            });
        });
        
        closeModalBtn.addEventListener('click', function() {
            modal.classList.remove('show');
            modalIframe.style.opacity = '0';
            
            // Hide modal after animation completes
            setTimeout(() => {
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
                modalIframe.src = '';
            }, 300);
        });
        
        window.addEventListener('click', function(event) {
            if (event.target === modal) {
                modal.classList.remove('show');
                modalIframe.style.opacity = '0';
                
                // Hide modal after animation completes
                setTimeout(() => {
                    modal.style.display = 'none';
                    document.body.style.overflow = 'auto';
                    modalIframe.src = '';
                }, 300);
            }
        });
        
        // NHANES variables functionality (only if data is available)
        ${nhanesData.length > 0 ? `
        // NHANES variables data
        const variablesData = ${JSON.stringify(nhanesData)};
        
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
        function renderTable(data) {
            tableBody.innerHTML = '';
            
            data.forEach(function(row) {
                const tr = document.createElement('tr');
                
                // Format dataset links
                let datasetLink = '';
                if (row['dataset link']) {
                    datasetLink = \`<a href="\${row['dataset link']}" target="_blank">Data</a>\`;
                }
                if (row['dataset documentation link']) {
                    datasetLink += \` | <a href="\${row['dataset documentation link']}" target="_blank">Docs</a>\`;
                }
                
                tr.innerHTML = \`
                    <td><strong>\${row['variable name'] || ''}</strong></td>
                    <td>\${row['variable explanation'] || ''}</td>
                    <td>\${row['dataset'] || ''}</td>
                    <td>\${row['cycle name'] || ''}</td>
                    <td>\${datasetLink}</td>
                \`;
                tableBody.appendChild(tr);
            });
            
            rowCount.textContent = \`Showing \${data.length.toLocaleString()} of \${variablesData.length.toLocaleString()} variables\`;
        }
        
        // Filter data based on search term
        function filterData(searchTerm) {
            searchSpinner.style.display = 'block';
            
            if (searchInProgress) {
                pendingSearchTerm = searchTerm;
                return;
            }
            
            searchInProgress = true;
            
            setTimeout(() => {
                processSearch(searchTerm);
                searchInProgress = false;
                if (pendingSearchTerm !== null) {
                    const nextSearch = pendingSearchTerm;
                    pendingSearchTerm = null;
                    filterData(nextSearch);
                }
            }, 0);
        }
        
        function processSearch(searchTerm) {
            if (!searchTerm) {
                filteredData = variablesData;
                renderTable(filteredData);
                searchSpinner.style.display = 'none';
                return;
            }
            
            const term = searchTerm.toLowerCase();
            filteredData = variablesData.filter(function(row) {
                return (row['variable name'] && row['variable name'].toLowerCase().includes(term)) ||
                       (row['variable explanation'] && row['variable explanation'].toLowerCase().includes(term)) ||
                       (row.dataset && row.dataset.toLowerCase().includes(term)) ||
                       (row['cycle name'] && row['cycle name'].toLowerCase().includes(term)) ||
                       (row.type && row.type.toLowerCase().includes(term));
            });
            
            renderTable(filteredData);
            searchSpinner.style.display = 'none';
        }
        
        function debounce(func, wait) {
            let timeout;
            return function(...args) {
                searchSpinner.style.display = 'block';
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    func.apply(this, args);
                }, wait);
            };
        }
        
        const debouncedSearch = debounce(function(e) {
            filterData(e.target.value);
        }, 300);
        
        searchInput.addEventListener('input', debouncedSearch);
        
        // Initial render
        renderTable(variablesData);
        ` : ''}
    </script>
</body>
</html>`;

  return html;
}

// Main build function
function build() {
  console.log('Starting build process...');
  
  try {
    // Copy example files
    const examples = copyExampleFiles();
    
    // Load NHANES data
    const nhanesData = loadNhanesData();
    
    // Generate index.html
    const indexHtml = generateIndexHtml(examples, nhanesData);
    
    // Write index.html
    const indexPath = path.join(distDir, 'index.html');
    fs.writeFileSync(indexPath, indexHtml, 'utf8');
    
    console.log('✅ Build completed successfully!');
    console.log(`📁 Output directory: ${distDir}`);
    console.log(`📄 Main file: ${indexPath}`);
    console.log(`📊 Included ${examples.length} interactive examples`);
    console.log(`🔍 Loaded ${nhanesData.length} NHANES variables`);
    
  } catch (error) {
    console.error('❌ Build failed:', error.message);
    process.exit(1);
  }
}

// Run build if this script is executed directly
if (require.main === module) {
  build();
}

module.exports = { build };
