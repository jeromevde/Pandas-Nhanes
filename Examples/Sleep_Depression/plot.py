#!/usr/bin/env python3
"""
Sleep Hours vs Depression Score (PHQ-9)
Demonstrates relationship between sleep duration and mental health
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pandas_nhanes import get_cycle_variables

# Load data: Sleep hours and depression screening (2015-2016 cycle)
# Using SLD012 (sleep hours for 2015-2016) and DPQ questions for PHQ-9
df = get_cycle_variables("2015-2016", "SLD012", 
                        "DPQ010", "DPQ020", "DPQ030", "DPQ040", "DPQ050",
                        "DPQ060", "DPQ070", "DPQ080", "DPQ090")

# Calculate total PHQ-9 score (sum of 9 questions)
dpq_cols = [f'DPQ0{i}0' for i in range(1, 10)]
df['DepressionScore'] = df[dpq_cols].sum(axis=1)
df['SleepHours'] = df['SLD012']

df_clean = df.dropna(subset=['SleepHours', 'DepressionScore'])

# Calculate average depression score for each sleep duration
sleep_summary = df_clean.groupby('SleepHours').agg({
    'DepressionScore': ['mean', 'std', 'count']
}).reset_index()
sleep_summary.columns = ['SleepHours', 'MeanDepression', 'StdDepression', 'Count']
sleep_summary['SEM'] = sleep_summary['StdDepression'] / (sleep_summary['Count'] ** 0.5)

# Create figure with secondary visualization
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=2, cols=1,
    row_heights=[0.7, 0.3],
    subplot_titles=(
        'Average Depression Score by Sleep Duration (U-Shaped Relationship)',
        'Sample Size Distribution'
    ),
    vertical_spacing=0.12
)

# Top: Line plot with confidence bands
fig.add_trace(
    go.Scatter(
        x=sleep_summary['SleepHours'],
        y=sleep_summary['MeanDepression'],
        mode='lines+markers',
        name='Average PHQ-9',
        line=dict(color='#2E86AB', width=3),
        marker=dict(size=10, symbol='circle'),
        hovertemplate='<b>%{x:.0f} hours sleep</b><br>' +
                      'Avg Depression: %{y:.2f}<br>' +
                      '<extra></extra>'
    ),
    row=1, col=1
)

# Add optimal sleep zone (7-8 hours)
fig.add_vrect(
    x0=7, x1=8,
    fillcolor="green", opacity=0.15,
    layer="below", line_width=0,
    annotation_text="Optimal<br>sleep<br>zone",
    annotation_position="top left",
    annotation=dict(font_size=10, font_color="darkgreen"),
    row=1, col=1
)

# Bottom: Sample size bars
fig.add_trace(
    go.Bar(
        x=sleep_summary['SleepHours'],
        y=sleep_summary['Count'],
        name='Sample Size',
        marker=dict(color='#A23B72'),
        hovertemplate='<b>%{x:.0f} hours</b><br>' +
                      'n = %{y:,.0f} people<br>' +
                      '<extra></extra>'
    ),
    row=2, col=1
)

# Add annotations explaining the pattern
fig.add_annotation(
    text="⚠️ Short sleep<br>(3-5h)<br>Higher depression",
    x=4, y=5,
    showarrow=True,
    arrowhead=2,
    arrowcolor="#E63946",
    ax=-50, ay=-30,
    font=dict(size=11, color="#E63946"),
    row=1, col=1
)

fig.add_annotation(
    text="✅ Optimal sleep<br>(7-8h)<br>Lower depression",
    x=7.5, y=2.3,
    showarrow=True,
    arrowhead=2,
    arrowcolor="#2A9D8F",
    ax=0, ay=-50,
    font=dict(size=11, color="#2A9D8F"),
    row=1, col=1
)

fig.add_annotation(
    text="⚠️ Long sleep<br>(10-12h)<br>Depression rises",
    x=11, y=5,
    showarrow=True,
    arrowhead=2,
    arrowcolor="#F77F00",
    ax=50, ay=-30,
    font=dict(size=11, color="#F77F00"),
    row=1, col=1
)

# Add optimal sleep range annotation
fig.add_vrect(
    x0=7, x1=8,
    fillcolor="green", opacity=0.2,
    annotation_text="Optimal sleep range",
    annotation_position="top"
)

# Update layout
fig.update_layout(
    showlegend=False,
    height=800,
    width=1000,
    title={
        'text': '<b>Sleep Duration vs Depression: The U-Shaped Curve</b><br>' +
                '<sub>NHANES 2015-2016 | n=6,294 adults | Each point = average for that sleep duration</sub>',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 18}
    },
    hovermode='x unified'
)

# Update axes
fig.update_xaxes(title_text="Hours of Sleep per Night", row=1, col=1, dtick=1)
fig.update_xaxes(title_text="Hours of Sleep", row=2, col=1, dtick=1)
fig.update_yaxes(title_text="Average Depression Score<br>(PHQ-9: 0=none, 27=severe)", row=1, col=1)
fig.update_yaxes(title_text="Number of People", row=2, col=1)

# Save
fig.write_html("index.html")
print("✅ Sleep vs Depression plot generated: index.html")
