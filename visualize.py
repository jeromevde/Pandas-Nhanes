#%%
import pandas as pd
import requests
from io import BytesIO

url = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/FERTIN_L.xpt"

def download_xpt_to_pandas(url):
    """
    Downloads an .xpt file from the given URL and loads it into a pandas DataFrame.
    Args:
        url (str): The URL of the .xpt file.

    Returns:
        pandas.DataFrame: The loaded data as a DataFrame.
    """
    # Download the file
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    
    # Load the file into a pandas DataFrame
    with BytesIO(response.content) as file:
        df = pd.read_sas(file, format="xport")
    
    return df

# Download and load the .xpt file
data = download_xpt_to_pandas(url)

