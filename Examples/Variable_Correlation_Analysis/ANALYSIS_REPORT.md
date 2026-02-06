# NHANES Variable Correlation Analysis Report

## Executive Summary

- Analyzed 10 variables with 1,125 correlation calculations

- Applied 5 different transformations (original, log, sqrt, square, inverse)

- Identified top correlations and unexpected relationships


## Top 5 Strongest Correlations


### RIDAGEYR ↔ BPXSY1 (r=0.687)

- **Age in years at screening**

- **Systolic blood pressure (mm Hg)**

- Sample size: 4,507


### DPQ_TOTAL ↔ PAQ_MINS (r=-0.677)

- **Depression screening score (PHQ-9)**

- **Physical activity minutes per week**

- Sample size: 4,528


### BMXBMI ↔ LBXGLU (r=0.549)

- **Body Mass Index (kg/m²)**

- **Fasting glucose (mg/dL)**

- Sample size: 4,519


### BMXBMI ↔ BPXSY1 (r=0.483)

- **Body Mass Index (kg/m²)**

- **Systolic blood pressure (mm Hg)**

- Sample size: 4,512


### RIDAGEYR ↔ LBXTC (r=0.436)

- **Age in years at screening**

- **Total cholesterol (mg/dL)**

- Sample size: 4,497


## Key Insights for Further Investigation


### 1. Metabolic Relationships

- BMI shows strong positive correlation with glucose and blood pressure

- Suggests metabolic syndrome cluster - investigate BMI threshold effects


### 2. Unexpected Finding: BMI-Vitamin D Inverse Relationship

- Higher BMI correlates with LOWER Vitamin D levels

- Possible mechanisms: adipose tissue sequestration, less outdoor activity

- **Recommendation**: Investigate vitamin D supplementation in high BMI individuals


### 3. Mental Health-Behavior Links

- Depression scores inversely correlated with physical activity

- Sleep duration shows complex relationship (may be U-shaped)

- **Recommendation**: Analyze optimal sleep ranges and activity interventions


## Methodology

- **Data Source**: NHANES 2015-2016 cycle (simulated data for demonstration)

- **Variables**: 10 health/demographic variables

- **Transformations**: Original, log, sqrt, square, inverse

- **Sample Size**: ~5,000 participants per variable

- **Correlation Method**: Pearson correlation coefficient
