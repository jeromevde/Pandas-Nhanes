#!/usr/bin/env python3
"""
Analysis of Testosterone/Estradiol ratio distribution in men from NHANES 2015-2016.

This script visualizes the T/E2 ratio distribution for men over 16 years old,
including statistics for different age groups.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pandas_nhanes import get_dataset

# --- Data Loading and Preprocessing ---

def load_and_clean_data():
    """Loads and cleans hormone and demographic data from NHANES 2015-2016."""
    tst_data = get_dataset("TST_I")[['SEQN', 'LBXTST', 'LBXEST']]
    demo_data = get_dataset("DEMO_I")[['SEQN', 'RIAGENDR', 'RIDAGEYR']]

    merged_data = pd.merge(tst_data, demo_data, on='SEQN', how='inner')
    merged_data = merged_data.dropna(subset=['LBXTST', 'LBXEST', 'RIAGENDR', 'RIDAGEYR'])

    # Filter for men over 16
    men_data = merged_data[(merged_data['RIAGENDR'] == 1) & (merged_data['RIDAGEYR'] > 16)].copy()
    
    # Calculate T/E2 ratio
    men_data['T_E2_ratio'] = men_data['LBXTST'] / men_data['LBXEST']

    # Remove extreme outliers
    q1 = men_data['T_E2_ratio'].quantile(0.25)
    q3 = men_data['T_E2_ratio'].quantile(0.75)
    iqr = q3 - q1
    upper_bound = q3 + 2.0 * iqr
    
    men_data_clean = men_data[men_data['T_E2_ratio'] <= upper_bound].copy()
    
    # Create age groups
    men_data_clean['age_group'] = pd.cut(
        men_data_clean['RIDAGEYR'],
        bins=[16, 20, 30, 40, 50, 60, 70, 120],
        labels=['17-20', '21-30', '31-40', '41-50', '51-60', '61-70', '70+']
    )
    
    return men_data_clean

# --- Visualization ---

def create_plot(data):
    """Creates an interactive plot of the T/E2 ratio distribution."""
    fig = make_subplots(
        rows=1, cols=1,
        subplot_titles=['T/E2 Ratio Distribution in Men > 16 years (NHANES 2015-2016)']
    )

    # Histogram of the overall distribution
    fig.add_trace(
        go.Histogram(
            x=data['T_E2_ratio'],
            name='T/E2 Ratio',
            marker_color='steelblue',
            opacity=0.7
        )
    )

    # Add statistics for each age group as annotations
    age_groups = sorted(data['age_group'].unique())
    annotations = []
    for i, group in enumerate(age_groups):
        group_data = data[data['age_group'] == group]
        mean = group_data['T_E2_ratio'].mean()
        std = group_data['T_E2_ratio'].std()
        n = len(group_data)
        annotations.append(
            dict(
                xref='paper', yref='paper',
                x=0.98, y=0.98 - (i * 0.05),
                text=f"{group}: μ={mean:.2f}, σ={std:.2f} (n={n})",
                showarrow=False,
                xanchor='right',
                yanchor='top'
            )
        )
    
    overall_mean = data['T_E2_ratio'].mean()
    overall_std = data['T_E2_ratio'].std()
    annotations.insert(0, dict(
        xref='paper', yref='paper',
        x=0.98, y=0.98 - (len(age_groups) * 0.05),
        text=f"Overall: μ={overall_mean:.2f}, σ={overall_std:.2f} (n={len(data)})",
        showarrow=False,
        xanchor='right',
        yanchor='top'
    ))

    fig.update_layout(
        annotations=annotations,
        xaxis_title='Testosterone/Estradiol Ratio (ng/dL ÷ pg/mL)',
        yaxis_title='Frequency',
        height=600,
        width=1000,
        template="plotly_white",
        showlegend=False
    )
    return fig

# --- Main Execution ---

def main():
    """Main function to run the analysis and generate the plot."""
    data = load_and_clean_data()
    
    print(f"Men over 16 years old with complete hormone data: {len(data)}")
    
    fig = create_plot(data)
    fig.write_html("Testosterone_Estrogen_Ratio.html")
    #fig.write_image("Testosterone_Estrogen_Ratio.png", scale=2)

if __name__ == "__main__":
    main()
