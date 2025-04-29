#%%

from pandas_nhanes import get_variables, get_dataset, explore
import pandas as pd
from scipy.stats import zscore
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
#%%

#explore()


steroid_panel = get_dataset("TST_L")
steroid_panel = steroid_panel[["SEQN","LBXEST", "LBXTST"]]
steroid_panel = steroid_panel.rename(columns={
    "LBXEST": "Estradiol (pg/mL)", "LBXTST": 
    "Testosterone, total (ng/dL)"})

demographics = get_dataset("DEMO_L")
demographics = demographics[["SEQN","RIAGENDR"]]
demographics = demographics.rename(columns={"RIAGENDR": "Gender"})


steroid_panel = pd.merge(steroid_panel, demographics, on="SEQN")



# Assign gender labels and concatenate
male = steroid_panel["Gender"] == 1
male_steroid_panel = steroid_panel[male].copy()
female_steroid_panel = steroid_panel[~male].copy()
male_steroid_panel['Gender'] = 'Men'
female_steroid_panel['Gender'] = 'Women'
df = pd.concat([male_steroid_panel, female_steroid_panel], ignore_index=True)

# Remove outliers using z-score (threshold=3)
df = df[(np.abs(zscore(df[["Estradiol (pg/mL)", "Testosterone, total (ng/dL)"]], nan_policy='omit')) < 3).all(axis=1)]


# Estradiol distribution by gender
sns.displot(
    data=df, x="Estradiol (pg/mL)", col="Gender", hue="Gender",
    bins=30, kde=True, palette={"Men": "#D7263D", "Women": "#1B7CED"},
    col_order=["Men", "Women"], height=4, aspect=1.2
)
plt.suptitle("Estradiol Distribution by Gender", y=1.05)
plt.show()

# Testosterone distribution by gender
sns.displot(
    data=df, x="Testosterone, total (ng/dL)", col="Gender", hue="Gender",
    bins=30, kde=True, palette={"Men": "#D7263D", "Women": "#1B7CED"},
    col_order=["Men", "Women"], height=4, aspect=1.2
)
plt.suptitle("Testosterone Distribution by Gender", y=1.05)
plt.show()

# %%
