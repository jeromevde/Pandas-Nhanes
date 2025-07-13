#!/usr/bin/env python3
"""
Script to automatically update README.md with all PNG files found in Examples directory
"""

import os
import glob
import re
from pathlib import Path

def update_readme_with_examples():
    """Update README.md to include all PNG files from Examples directory"""
    
    readme_path = "README.md"
    examples_dir = "Examples"
    
    # Find all PNG files in Examples directory
    png_files = glob.glob(os.path.join(examples_dir, "**/*.png"), recursive=True)
    png_files.sort()  # Sort alphabetically
    
    print(f"Found {len(png_files)} PNG files:")
    for png in png_files:
        print(f"  - {png}")
    
    # Read current README
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create new results section
    results_section = "## Results\n\n"
    
    for png_file in png_files:
        # Get relative path and create a nice title
        rel_path = png_file.replace("\\", "/")  # Normalize path separators
        filename = os.path.basename(png_file)
        title = filename.replace('.png', '').replace('_', ' ').title()
        
        # Handle special cases for better titles
        title = title.replace('T E2', 'T/E2')
        title = title.replace('2015 2016', '2015-2016')
        
        results_section += f"### {title}\n"
        results_section += f"![{filename.replace('.png', '')}]({rel_path})\n\n"
    
    # Find the existing Results section and replace it
    # Look for ## Results until the next ## section or end of file
    results_pattern = r'## Results.*?(?=##|\Z)'
    
    if re.search(results_pattern, content, re.DOTALL):
        # Replace existing Results section
        new_content = re.sub(results_pattern, results_section.rstrip(), content, flags=re.DOTALL)
    else:
        # Append Results section at the end
        new_content = content.rstrip() + "\n\n" + results_section
    
    # Write updated README
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Updated {readme_path} with {len(png_files)} example images")

if __name__ == "__main__":
    update_readme_with_examples()
