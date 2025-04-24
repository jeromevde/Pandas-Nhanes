from pandas_nhanes import download_full_cycle_dataframe, list_cycle_variables, get_variable_data

# Example: Download full cycle dataframe with variable descriptions
res = download_full_cycle_dataframe("2021-2023", replace_names_with_descriptions=True)

# Show variables available for a cycle
print(list_cycle_variables("2021-2023"))

# Example: Get data for specific variables

df = get_variable_data([
    "LBXTST",
    "DR1TCAFF"
], "2021-2023")

# Example: Other variables you might want to query
other_vars = [
    "LBDTSTSI",
    "DSQTCAFF",
    "DSQICAFF",
    "DR2TCAFF",
    "DR1ICAFF",
    "DR2ICAFF"
]
# Uncomment to use:
# df_other = get_variable_data(other_vars, "2021-2023")

# Example: Plotting (requires matplotlib and seaborn)
import matplotlib.pyplot as plt
import seaborn as sns
df_clean = df.dropna(subset=['DR1TCAFF', 'LBXTST'])
sns.regplot(x='DR1TCAFF', y='LBXTST', data=df_clean)
plt.xlabel('DR1TCAFF')
plt.ylabel('LBXTST')
plt.show()
