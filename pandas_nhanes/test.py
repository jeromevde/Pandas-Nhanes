#%%
from pandas_nhanes import get_variables, get_dataset, explore

df = get_variables()
explore()

#%%

res = get_dataset("TST_L")
res

# %%
