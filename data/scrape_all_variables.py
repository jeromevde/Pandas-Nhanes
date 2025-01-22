#%%
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib
import time 

TARGET_URL = "https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx"

import logging
import http.client as http_client
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

def extract_table_to_dataframe():
    # Fetch the main table with dataset information
    response = requests.get(TARGET_URL, verify=False)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", id="GridView1")
    
    if not table:
        print("Table not found on the page.")
        return pd.DataFrame()  # Return an empty DataFrame
    
    rows = table.find_all("tr")[1:]  # Skip header row
    
    data = []
    for row in rows:
        columns = row.find_all("td")
        if len(columns) < 4:
            continue
        
        cycle = columns[0].text.strip()
        doc_link_tag = columns[1].find("a")
        data_link_tag = columns[2].find("a")
        
        doc_link = urllib.parse.urljoin(TARGET_URL, doc_link_tag["href"]) if doc_link_tag and doc_link_tag.get("href") else None
        data_link = urllib.parse.urljoin(TARGET_URL, data_link_tag["href"]) if data_link_tag and data_link_tag.get("href") else None
        
        data.append([cycle, doc_link, data_link])
    
    return pd.DataFrame(data, columns=["cycle name", "cycle documentation link", "cycle dataset link"])

def extract_variable_info(doc_link):
    time.sleep(1) # avoid server slow down
    response = requests.get(doc_link, verify=False, timeout=5)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, "html.parser")
    codebook_section = soup.find("ul", id="CodebookLinks")
    
    if not codebook_section:
        return pd.DataFrame()  # Return an empty DataFrame
    
    variables = []
    for li in codebook_section.find_all("li"):
        link_tag = li.find("a")
        if link_tag:
            href = link_tag.get("href")
            text = link_tag.text.strip()
            if " - " in text:
                variable_name, variable_explanation = text.split(" - ", 1)
                variable_doc_link = doc_link + href
                variables.append([variable_name, variable_explanation, variable_doc_link])
    
    return pd.DataFrame(variables, columns=["variable name", "variable explanation", "variable documentation link"])

def main():
    # Fetch all datasets
    datasets_df = extract_table_to_dataframe()
    if datasets_df.empty:
        print("No datasets found.")
        return

    # Collect variable info for all datasets
    all_variables = []
    for i, row in datasets_df.iterrows():
        print(f"{i} on {len(datasets_df)}")
        cycle_name = row["cycle name"]
        cycle_doc_link = row["cycle documentation link"]
        cycle_data_link = row["cycle dataset link"]
        
        if cycle_doc_link:  # Proceed only if a documentation link is available
            variables_df = extract_variable_info(cycle_doc_link)
            if not variables_df.empty:
                # Add cycle-specific information to the variables
                variables_df.insert(2, column="cycle name", value=cycle_name) # insert third pos
                variables_df["cycle documentation link"] = cycle_doc_link
                variables_df["cycle dataset link"] = cycle_data_link
                all_variables.append(variables_df)

    # Concatenate all variables into a single DataFrame
    if all_variables:
        final_df = pd.concat(all_variables, ignore_index=True)
        final_df.set_index("variable name", inplace=True)
        final_df.sort_values(by="cycle name", inplace=True)
        return final_df
    else:
        print("No variables found.")
        return pd.DataFrame()

if __name__ == "__main__":
    final_dataframe = main()
    if not final_dataframe.empty:
        print(final_dataframe)
        # Save to a CSV file for further use
        final_dataframe.to_csv("nhanes_variables.csv")
