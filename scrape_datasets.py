#%%
import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE_URL = "https://wwwn.cdc.gov"
TARGET_URL = "https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx"

def extract_table_to_dataframe():
    # Fetch the page
    response = requests.get(TARGET_URL)
    response.raise_for_status()
    
    # Parse the HTML
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", id="GridView1")
    
    if not table:
        print("Table not found on the page.")
        return pd.DataFrame()  # Return an empty DataFrame
    
    rows = table.find_all("tr")[1:]  # Skip header row
    
    # Data storage
    data = []
    
    for row in rows:
        columns = row.find_all("td")
        if len(columns) < 4:
            continue
        
        cycle = columns[0].text.strip()
        
        # Safely extract links
        doc_link_tag = columns[1].find("a")
        data_link_tag = columns[2].find("a")
        doc_link = BASE_URL + doc_link_tag["href"] if doc_link_tag and doc_link_tag.get("href") else None
        data_link = BASE_URL + data_link_tag["href"] if data_link_tag and data_link_tag.get("href") else None
        
        data.append([cycle, doc_link, data_link])
    
    # Create a DataFrame
    df = pd.DataFrame(data, columns=["cycle", "dataset documentation", "dataset link"])
    return df

if __name__ == "__main__":
    dataframe = extract_table_to_dataframe()
    print(dataframe)

# %%
