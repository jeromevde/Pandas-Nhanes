#!/usr/bin/env python3
"""
Sleep Hours vs Depression Score (PHQ-9)
Demonstrates relationship between sleep duration and mental health
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pandas_nhanes import get_cycle_variables

# Load data: Sleep hours and depression screening
df = get_cycle_variables("2015-2016", "SLD010H", "DPQ010", "RIAGENDR", use_name=True)

df_clean = df.dropna(subset=['SleepHours', 'DepressionScore'])

# Create scatter plot with regression
fig = px.scatter(
    df_clean,
    x='SleepHours',
    y='DepressionScore',
    color='Gender',
    title='Sleep Hours vs Depression Score (PHQ-9)',
    labels={
        'SleepHours': 'Hours of Sleep per Night',
        'DepressionScore': 'Depression Screening Score (PHQ-9)',
    },
    trendline="ols",
    hover_data=['SleepHours', 'DepressionScore', 'Gender']
)

# Add optimal sleep range annotation
fig.add_vrect(
    x0=7, x1=8,
    fillcolor="green", opacity=0.2,
    annotation_text="Optimal sleep range",
    annotation_position="top"
)

fig.update_layout(
    showlegend=True,
    height=600,
    width=900
)

# Save
fig.write_html("index.html")
fig.write_image("plot.png", width=1200, height=800)

print("✅ Sleep vs Depression plot generated")
