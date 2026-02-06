#!/usr/bin/env python3
"""
Generate plots.json manifest from Examples/ directory.
Scans for subdirectories containing .png and .html files.
"""
import json
from pathlib import Path


def find_plots(examples_dir="Examples"):
    """Scan Examples/ directory and find all plot examples."""
    examples_path = Path(examples_dir)
    plots = []
    
    if not examples_path.exists():
        print(f"Warning: {examples_dir} directory not found")
        return plots
    
    # Iterate through subdirectories
    for subdir in sorted(examples_path.iterdir()):
        if not subdir.is_dir():
            continue
        
        base_name = subdir.name
        
        # Look for PNG file (either <name>.png or plot.png)
        png_candidates = [
            subdir / f"{base_name}.png",
            subdir / "plot.png",
        ]
        
        png_file = None
        for candidate in png_candidates:
            if candidate.exists():
                png_file = candidate
                break
        
        # Look for HTML file (either <name>.html or index.html)
        html_candidates = [
            subdir / f"{base_name}.html",
            subdir / "index.html",
        ]
        
        html_file = None
        for candidate in html_candidates:
            if candidate.exists():
                html_file = candidate
                break
        
        # Only include if we have at least a PNG
        if png_file:
            plot_info = {
                "base": base_name,
                "png": png_file.relative_to(Path(".")).as_posix(),
                "html": html_file.relative_to(Path(".")).as_posix() if html_file else None,
            }
            plots.append(plot_info)
            print(f"✓ Found: {base_name}")
        else:
            print(f"⚠ Skipped {base_name} (no PNG found)")
    
    return plots


def main():
    plots = find_plots()
    
    # Write to plots.json
    output_file = Path("plots.json")
    with output_file.open("w") as f:
        json.dump(plots, f, indent=2)
    
    print(f"\n✅ Generated {output_file} with {len(plots)} plots")


if __name__ == "__main__":
    main()
