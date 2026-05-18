#%%

import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib
from concurrent.futures import ThreadPoolExecutor
import os
import json
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
    """Extract variable information and value labels from a documentation page.

    Returns
    -------
    variables_df : pd.DataFrame   columns: variable name, variable explanation
    value_labels : dict           {var_name: {code_str: label_str}}
    """
    SKIP_LABELS = {
        "missing", "don't know", "refused", "could not obtain",
        "no response", "not applicable",
    }
    response = requests.get(doc_link, verify=False, timeout=5)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "lxml")

    # ── Variable names & explanations (from the nav list) ────────────────────
    codebook_section = soup.find("ul", id="CodebookLinks")
    variables = []
    if codebook_section:
        for li in codebook_section.find_all("li"):
            link_tag = li.find("a")
            if link_tag:
                text = link_tag.text.strip()
                if " - " in text:
                    variable_name, variable_explanation = text.split(" - ", 1)
                    variables.append([variable_name, variable_explanation])

    # ── Value labels (from the codebook tables on the same page) ─────────────
    value_labels = {}
    for h3 in soup.find_all("h3"):
        var_id = h3.get("id", "").strip()
        if not var_id:
            continue
        table = h3.find_next("table")
        if not table:
            continue
        labels = {}
        for row in table.find_all("tr")[1:]:   # skip header row
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            code = cells[0].text.strip()
            desc = cells[1].text.strip()
            if code in (".", "", "Range of Values"):
                continue
            if desc.lower() in SKIP_LABELS:
                continue
            try:
                labels[str(int(float(code)))] = desc
            except (ValueError, OverflowError):
                pass
        if labels:
            value_labels[var_id] = labels

    return (
        pd.DataFrame(variables, columns=["variable name", "variable explanation"]),
        value_labels,
    )

def process_dataset(index, row):
    """Process a single dataset row and save its variables DataFrame."""
    try:
        cycle_name = row["cycle name"]
        dataset = row["dataset"]
        dataset_link = row["dataset link"]
        dataset_doc_link = row["dataset documentation link"]
        
        if dataset_doc_link:
            variables_df, value_labels = extract_variable_info(dataset_doc_link)
            if not variables_df.empty:
                variables_df.insert(0, "cycle name", cycle_name)
                variables_df.insert(1, "dataset", dataset)
                variables_df.insert(2, "dataset link", dataset_link)
                variables_df.insert(3, "dataset documentation link", dataset_doc_link)
                # Save partial CSV
                filename = f"partial_results/dataset_{index}.csv"
                variables_df.to_csv(filename, index=False)
                # Save partial value labels
                if value_labels:
                    vl_filename = f"partial_results/value_labels_{index}.json"
                    with open(vl_filename, "w") as f:
                        json.dump(value_labels, f, separators=(",", ":"))
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

    # Merge all partial value label JSONs into one file
    partial_dir = "partial_results"
    all_value_labels = {}
    vl_files = sorted(
        f for f in os.listdir(partial_dir)
        if f.startswith("value_labels_") and f.endswith(".json")
    )
    for fname in vl_files:
        with open(os.path.join(partial_dir, fname)) as fp:
            all_value_labels.update(json.load(fp))

    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(script_dir, "nhanes_value_labels.json")
    with open(out_path, "w") as f:
        json.dump(all_value_labels, f, separators=(",", ":"))
    print(f"Saved value labels for {len(all_value_labels)} variables → {out_path}")
