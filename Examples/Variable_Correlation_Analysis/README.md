# Variable Correlation Analysis

This example demonstrates a comprehensive approach to exploring relationships between NHANES variables using correlation analysis with non-linear transformations.

## Overview

The analysis:
- Selects 10 random numeric variables from NHANES
- Computes correlations between all 45 pairs (10 choose 2)
- Applies 5 different transformations to each variable
- Generates 1,125 total correlation calculations
- Identifies interesting and unexpected relationships

## Key Features

### 1. Multiple Transformations
Rather than just computing linear correlations, the script applies:
- **Original**: Standard linear correlation
- **Log**: Reveals exponential relationships
- **Square Root**: Moderates extreme values
- **Square**: Amplifies relationships
- **Inverse**: Detects reciprocal relationships

### 2. Smart Variable Selection
Prioritizes health-relevant variables:
- Laboratory measurements (LBX*)
- Body measurements (BMX*)
- Blood pressure (BPX*)
- Dietary intake (DR1*)
- Mental health (DPQ*)
- Sleep patterns (SLD*)
- Physical activity (PAQ*)

### 3. Comprehensive Reporting
Generates three types of insights:
1. **Strongest Linear Correlations**: Direct relationships
2. **Hidden Relationships**: Non-linear patterns revealed by transformations
3. **Cross-Domain Findings**: Unexpected connections between different health domains

## Files

- `correlation_analysis.py` - Main script for real NHANES data (requires API access)
- `correlation_analysis_demo.py` - Demonstration with simulated data
- `correlation_analysis_results.csv` - Full correlation results
- `ANALYSIS_REPORT.md` - Summary report with key findings

## Usage

### With Real NHANES Data (when API is available)
```bash
python correlation_analysis.py
```

### Demo Version (works offline)
```bash
python correlation_analysis_demo.py
```

## Sample Findings

From the demonstration analysis:

### 1. Strong Positive Correlations
- **Age ↔ Blood Pressure** (r=0.69): Classic cardiovascular aging
- **BMI ↔ Glucose** (r=0.55): Metabolic syndrome indicator

### 2. Strong Negative Correlations  
- **Depression ↔ Physical Activity** (r=-0.68): Exercise as intervention target

### 3. Non-Linear Relationships Discovered
- **Sleep ↔ Depression**: Transformation reveals U-shaped relationship
  - Original correlation: -0.31
  - With inverse/square transformation: 0.49
  - Interpretation: Both too little and too much sleep correlate with depression

### 4. Unexpected Cross-Domain Findings
- **BMI ↔ Vitamin D**: Inverse relationship suggesting adipose sequestration
- **Age ↔ Various Metabolic Markers**: Aging effects on multiple systems

## Methodology

The analysis follows this approach:

1. **Variable Selection**: Random sampling with preference for numeric health variables
2. **Data Cleaning**: Remove missing values, require minimum sample size (n≥30)
3. **Transformation**: Apply 5 transformations to each variable
4. **Correlation**: Compute Pearson correlation for all transformation pairs
5. **Analysis**: Identify strongest correlations and transformation improvements
6. **Reporting**: Generate human-readable summaries and CSV results

## Advantages Over Traditional Plotting

As suggested in the issue, this approach has several benefits:

1. **Efficiency**: Analyzes 100+ relationships in seconds vs. hours of plotting
2. **Quantitative**: Numerical correlations vs. subjective visual assessment
3. **Automated**: Flags interesting patterns without manual review
4. **Scalable**: Can easily expand to more variables
5. **Transformation Discovery**: Reveals non-linear relationships that might be missed visually

## Extending This Analysis

To expand the analysis:

1. **More Variables**: Change `n=10` to analyze more relationships
2. **Different Cycles**: Modify `cycle="2015-2016"` to compare across time
3. **Custom Transformations**: Add domain-specific transformations (e.g., BMI categories)
4. **Stratification**: Analyze separately by age groups, gender, etc.
5. **Multivariate**: Extend to partial correlations controlling for confounders

## Key Insights for Researchers

This example is particularly useful for:

- **Hypothesis Generation**: Quickly identify relationships worth investigating
- **Data Exploration**: Understand variable distributions and relationships
- **Anomaly Detection**: Find unexpected correlations suggesting data issues or novel findings
- **Feature Selection**: Identify correlated variables for machine learning models
- **Research Planning**: Prioritize relationships for deeper statistical analysis

## Dependencies

- pandas
- numpy
- pandas_nhanes (for real data access)

## Notes

- The demo version uses simulated data with realistic health relationships
- Real NHANES data will have different correlation values
- Always validate findings with domain expertise before drawing conclusions
- Correlation does not imply causation - use these findings to guide further research
