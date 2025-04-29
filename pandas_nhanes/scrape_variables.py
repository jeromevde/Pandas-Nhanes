#%%

import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib
from concurrent.futures import ThreadPoolExecutor
import os
from tqdm import tqdm
import logging
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Target URL
TARGET_URL = "https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx"

# Optional logging configuration (disabled by default)
if False:
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

def extract_table_to_dataframe():
    """Fetch the main table with dataset information."""
    response = requests.get(TARGET_URL, verify=False, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, "lxml")
    table = soup.find("table", id="GridView1")
    
    if not table:
        print("Table not found on the page.")
        return pd.DataFrame()
    
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
    
    # Also extract dataset name from the dataset documentation link
    df = pd.DataFrame(data, columns=["cycle name", "dataset documentation link", "dataset link"])
    df["dataset"] = df["dataset documentation link"].apply(lambda x: os.path.splitext(os.path.basename(x))[0] if pd.notnull(x) else None)
    # Reorder columns
    df = df[["cycle name", "dataset", "dataset link", "dataset documentation link"]]
    return df

def extract_variable_info(doc_link):
    """Extract variable information from a documentation page."""
    response = requests.get(doc_link, verify=False, timeout=5)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, "lxml")
    codebook_section = soup.find("ul", id="CodebookLinks")
    
    if not codebook_section:
        return pd.DataFrame()
    
    variables = []
    for li in codebook_section.find_all("li"):
        link_tag = li.find("a")
        if link_tag:
            text = link_tag.text.strip()
            if " - " in text:
                variable_name, variable_explanation = text.split(" - ", 1)
                variables.append([variable_name, variable_explanation])
    
    return pd.DataFrame(variables, columns=["variable name", "variable explanation"])

def process_dataset(index, row):
    """Process a single dataset row and save its variables DataFrame."""
    try:
        cycle_name = row["cycle name"]
        dataset = row["dataset"]
        dataset_link = row["dataset link"]
        dataset_doc_link = row["dataset documentation link"]
        
        if dataset_doc_link:
            variables_df = extract_variable_info(dataset_doc_link)
            if not variables_df.empty:
                variables_df.insert(0, "cycle name", cycle_name)
                variables_df.insert(1, "dataset", dataset)
                variables_df.insert(2, "dataset link", dataset_link)
                variables_df.insert(3, "dataset documentation link", dataset_doc_link)
                # Save partial result
                filename = f"partial_results/dataset_{index}.csv"
                variables_df.to_csv(filename, index=False)
                return variables_df
        return pd.DataFrame()
    except Exception as e:
        print(f"Error processing {cycle_name}: {e}")
        return pd.DataFrame()

def main():
    """Main function to fetch and process datasets with progress bar and incremental saving."""
    # Fetch all datasets
    datasets_df = extract_table_to_dataframe()
    if datasets_df.empty:
        print("No datasets found.")
        return None

    # Set up directory for partial results
    partial_dir = "partial_results"
    os.makedirs(partial_dir, exist_ok=True)

    # Identify already processed datasets
    existing_files = [f for f in os.listdir(partial_dir) if f.startswith("dataset_") and f.endswith(".csv")]
    existing_indices = [int(f.split("_")[1].split(".")[0]) for f in existing_files]

    # Filter out already processed datasets
    remaining_df = datasets_df[~datasets_df.index.isin(existing_indices)]

    if not remaining_df.empty:
        print(f"Processing {len(remaining_df)} remaining datasets...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Process remaining datasets with progress bar
            list(tqdm(
                executor.map(process_dataset, remaining_df.index, remaining_df.to_dict("records")),
                total=len(remaining_df),
                desc="Processing datasets"
            ))
    else:
        print("All datasets already processed.")

    # Collect all partial results
    all_files = [f for f in os.listdir(partial_dir) if f.startswith("dataset_") and f.endswith(".csv")]
    all_dfs = []
    for f in sorted(all_files):  # Sort to maintain order if desired
        df = pd.read_csv(os.path.join(partial_dir, f))
        all_dfs.append(df)

    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        # Reorder columns as requested
        columns_order = [
            "cycle name",
            "dataset",
            "variable name",
            "variable explanation",
            "dataset link",
            "dataset documentation link"
        ]
        # Only keep columns that exist in the DataFrame
        columns_order = [col for col in columns_order if col in final_df.columns]
        final_df = final_df[columns_order]
        final_df.sort_values(by=["cycle name", "dataset", "variable name"], inplace=True)
        return final_df
    else:
        print("No variables found.")
        return pd.DataFrame()

if __name__ == "__main__":
    final_dataframe = main()
    if final_dataframe is not None and not final_dataframe.empty:
        print(final_dataframe)
        final_dataframe.to_csv("nhanes_variables.csv", index=False)
# %%
