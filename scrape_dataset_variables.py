#%%
import requests
from bs4 import BeautifulSoup
import pandas as pd

def extract_variable_info(doc_link):
    # Fetch the page
    response = requests.get(doc_link)
    response.raise_for_status()
    
    # Parse the HTML
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find the CodebookLinks section
    codebook_section = soup.find("ul", id="CodebookLinks")
    
    if not codebook_section:
        print("CodebookLinks section not found.")
        return pd.DataFrame()  # Return an empty DataFrame
    
    # Extract variables and their descriptions
    variables = []
    for li in codebook_section.find_all("li"):
        link_tag = li.find("a")
        if link_tag:
            href = link_tag.get("href")
            text = link_tag.text.strip()
            if " - " in text:
                variable_name, variable_explanation = text.split(" - ", 1)
                variables.append([variable_name, variable_explanation, doc_link + href])
    
    # Create a DataFrame
    df = pd.DataFrame(variables, columns=["variable name", "variable explanation", "variable_documentation"])
    return df



doc_link = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/AUQ_L.htm"
dataframe = extract_variable_info(doc_link)
dataframe
# %%
