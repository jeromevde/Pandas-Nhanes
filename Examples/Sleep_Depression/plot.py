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

# Create scatter plot
fig = px.scatter(
    df_clean,
    x='SleepHours',
    y='DepressionScore',
    title='Sleep Hours vs Depression Score (PHQ-9) - NHANES 2015-2016',
    labels={
        'SleepHours': 'Hours of Sleep per Night',
        'DepressionScore': 'Depression Screening Score (PHQ-9, 0-27)',
    },
    opacity=0.5,
    hover_data=['SleepHours', 'DepressionScore']
)

# Add a text annotation with sample info
fig.add_annotation(
    text=f'n = {len(df_clean)} participants',
    xref='paper', yref='paper',
    x=0.02, y=0.98,
    showarrow=False,
    bgcolor='rgba(255,255,255,0.8)'
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
print("✅ Sleep vs Depression plot generated: index.html")
