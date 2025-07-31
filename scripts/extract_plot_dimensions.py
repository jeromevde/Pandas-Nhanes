#!/usr/bin/env python3
"""
Extract plot dimensions from Plotly HTML files and generate JavaScript configuration.
This script automatically scans the Examples directory for HTML files and extracts
the width and height values from the Plotly layout configuration.
"""

import os
import re
import json
from pathlib import Path

def extract_plot_dimensions(html_file_path):
    """Extract width and height from a Plotly HTML file."""
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for the pattern: "height":600,"width":1000 or "width":1000,"height":600
        pattern = r'"(?:height|width)"\s*:\s*(\d+)\s*,\s*"(?:height|width)"\s*:\s*(\d+)'
        matches = re.findall(pattern, content)
        
        if matches:
            # Find the specific pattern that includes both height and width
            height_width_pattern = r'"height"\s*:\s*(\d+)\s*,\s*"width"\s*:\s*(\d+)'
            width_height_pattern = r'"width"\s*:\s*(\d+)\s*,\s*"height"\s*:\s*(\d+)'
            
            height_match = re.search(height_width_pattern, content)
            width_match = re.search(width_height_pattern, content)
            
            if height_match:
                height, width = int(height_match.group(1)), int(height_match.group(2))
                return width, height
            elif width_match:
                width, height = int(width_match.group(1)), int(width_match.group(2))
                return width, height
        
        print(f"Could not extract dimensions from {html_file_path}")
        return None, None
        
    except Exception as e:
        print(f"Error reading {html_file_path}: {e}")
        return None, None

def scan_examples_directory():
    """Scan the Examples directory for HTML files and extract their dimensions."""
    examples_dir = Path(__file__).parent.parent / "Examples"
    dimensions = {}
    
    if not examples_dir.exists():
        print(f"Examples directory not found: {examples_dir}")
        return dimensions
    
    html_files = list(examples_dir.glob("*.html"))
    print(f"Found {len(html_files)} HTML files in Examples directory")
    
    for html_file in html_files:
        print(f"Processing {html_file.name}...")
        width, height = extract_plot_dimensions(html_file)
        
        if width and height:
            dimensions[html_file.name] = {
                "width": width,
                "height": height,
                "aspect_ratio": round(width / height, 3)
            }
            print(f"  → {width}×{height} (aspect ratio: {width/height:.3f})")
        else:
            print(f"  → Failed to extract dimensions")
    
    return dimensions

def generate_javascript_config(dimensions):
    """Generate JavaScript configuration object for the website."""
    js_config = "        // Plot dimensions extracted from Plotly configurations\n"
    js_config += "        const plotDimensions = {\n"
    
    for filename, dims in dimensions.items():
        js_config += f"            '{filename}': {{ width: {dims['width']}, height: {dims['height']} }},\n"
    
    js_config += "        };"
    
    return js_config

def update_index_html(dimensions):
    """Update the index.html file with the new dimensions configuration."""
    index_path = Path(__file__).parent.parent / "index.html"
    
    if not index_path.exists():
        print(f"index.html not found: {index_path}")
        return False
    
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Generate new JavaScript config
        new_config = generate_javascript_config(dimensions)
        
        # Replace the existing plotDimensions object
        pattern = r'(\s+)// Plot dimensions extracted from Plotly configurations\s*\n\s+const plotDimensions = \{[^}]+\};'
        replacement = new_config
        
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        if updated_content != content:
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"✅ Updated index.html with new plot dimensions")
            return True
        else:
            print("❌ No changes made to index.html (pattern not found)")
            return False
            
    except Exception as e:
        print(f"Error updating index.html: {e}")
        return False

def main():
    """Main function to extract dimensions and update the website."""
    print("🔍 Extracting plot dimensions from HTML files...")
    print("=" * 50)
    
    dimensions = scan_examples_directory()
    
    if not dimensions:
        print("❌ No dimensions extracted. Exiting.")
        return
    
    print("\n📊 Summary of extracted dimensions:")
    print("=" * 50)
    for filename, dims in dimensions.items():
        print(f"{filename:35} → {dims['width']:4d}×{dims['height']:<4d} (ratio: {dims['aspect_ratio']:.3f})")
    
    print(f"\n🔧 Updating website configuration...")
    success = update_index_html(dimensions)
    
    if success:
        print("✅ Website updated successfully!")
        print("\n💡 The website will now automatically use the correct plot dimensions.")
    else:
        print("❌ Failed to update website.")
        print("\n📋 Generated JavaScript configuration:")
        print(generate_javascript_config(dimensions))

if __name__ == "__main__":
    main()
