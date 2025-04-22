
#%%
import pandas as pd
import requests
import requests
import os
import pandas as pd
import io
import pandas as pd
from collections import OrderedDict
import qgrid

#%%
from itables import show
from itables import init_notebook_mode
init_notebook_mode(all_interactive=True)

#%%
def list_cycles():
    return list(pd.read_csv("nhanes_variables.csv")["cycle name"].unique())

# list_cycles()

def list_cycle_description():
    pass

#%%
def list_cycle_variables(cycle):
    data = pd.read_csv("nhanes_variables.csv")
    return data[data["cycle name"] == cycle][["variable name", "variable explanation"]]

# list_cycle_variables("1999-2004")


#%%
def get_variable_description(variable):
    data = pd.read_csv("nhanes_variables.csv")
    matching_rows = data[data["variable name"] == variable]
    if matching_rows.empty:
        raise ValueError(f"Variable {variable} not found.")
    return matching_rows.iloc[0]["variable explanation"]

get_variable_description("SSCYRRSG")

#%%

def download_xpt_as_csv(url):
    """Download an XPT file from the given URL and return it as a pandas DataFrame."""
    try:
        # Stream the file content
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Read the streamed content into a BytesIO buffer
        xpt_buffer = io.BytesIO()
        for chunk in response.iter_content(chunk_size=8192):
            xpt_buffer.write(chunk)
        xpt_buffer.seek(0)  # Reset buffer position to the beginning

        # Read the XPT file from the buffer into a DataFrame
        df = pd.read_sas(xpt_buffer, format='xport')
        
        return df

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        raise
    except Exception as e:
        print(f"Error processing XPT to DataFrame: {e}")
        raise

# download_xpt_as_csv("https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2009/DataFiles/ACQ_F.xpt")


# %%

def get_variable_data(variables, cycle):
    """
    Retrieve data for specified variables from a given NHANES cycle.

    Parameters:
    - variables (str or list of str): Variable name(s) to retrieve.
    - cycle (str): The NHANES cycle to retrieve data from, e.g., "1999-2004".

    Returns:
    - pd.DataFrame: A DataFrame with "SEQN" as index and the requested variables as columns.

    Raises:
    - ValueError: If any variables are not found in the specified cycle or in the dataset.
    """
    # If input is a single string, convert it to a list
    if isinstance(variables, str):
        variables = [variables]
    
    # Remove duplicates while preserving order
    variables = list(OrderedDict.fromkeys(variables))
    
    # Read the CSV file containing variable metadata
    data = pd.read_csv("nhanes_variables.csv")
    
    # Find rows matching the input variables and specified cycle
    matching_rows = data[(data["variable name"].isin(variables)) & (data["cycle name"] == cycle)]
    print(matching_rows)
    # Check if all variables are found in the specified cycle
    found_vars = set(matching_rows["variable name"])
    missing_vars = set(variables) - found_vars
    if missing_vars:
        raise ValueError(f"Variables not found in cycle {cycle}: {missing_vars}")
    
    # Group variables by their dataset link
    dataset_to_vars = matching_rows.groupby("cycle dataset link")["variable name"].apply(list).to_dict()
    
    # List to store DataFrames for each dataset
    dfs = []
    
    # Process each dataset
    for dataset_link, vars_in_dataset in dataset_to_vars.items():
        # Download the dataset
        df = download_xpt_as_csv(dataset_link)
        
        # Verify all expected variables are in the dataset
        missing_vars = set(vars_in_dataset) - set(df.columns)
        if missing_vars:
            raise ValueError(f"Variables {missing_vars} not found in dataset {dataset_link} for cycle {cycle}")
        
        # Extract SEQN and the relevant variables, set SEQN as index
        df_extracted = df[["SEQN"] + vars_in_dataset].set_index("SEQN")
        dfs.append(df_extracted)
    
    # Concatenate all DataFrames horizontally, aligning on SEQN index
    result = pd.concat(dfs, axis=1)
    
    return result
    

show(list_cycle_variables("2021-2023"))


df = get_variable_data([
    "LBXTST",
    #"LBDTSTSI",
    #"DSQTCAFF",
    #"DSQICAFF",
    #"DR2TCAFF",
    #"DR1ICAFF",
    "DR1TCAFF",
    #"DR2ICAFF"
    ], "2021-2023" )
# %%

import matplotlib.pyplot as plt
import seaborn as sns
df_clean = df.dropna(subset=['DR1TCAFF', 'LBXTST'])
sns.regplot(x='DR1TCAFF', y='LBXTST', data=df_clean)
plt.xlabel('DR1TCAFF')
plt.ylabel('LBXTST')
plt.show()


# %%
