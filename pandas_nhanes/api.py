import pandas as pd
import requests
import io


def get_variables():
    """
    Return the full NHANES variables table as a pandas DataFrame.
    """
    import importlib.resources
    with importlib.resources.path("pandas_nhanes", "nhanes_variables.csv") as csv_path:
        data = pd.read_csv(csv_path)
    return data


def explore():
    """
    Open the NHANES variables table in your default web browser as an interactive HTML table.
    The HTML file is written to your cache directory (~/.cache/pandas_nhanes/nhanes_variables.html).
    """
    import os
    import webbrowser
    import itables
    from itables import to_html_datatable

    # Get variables DataFrame
    df = get_variables()

    # Prepare cache directory and HTML path
    cache_dir = os.path.join(os.path.expanduser('~'), '.cache', 'pandas_nhanes')
    os.makedirs(cache_dir, exist_ok=True)
    html_path = os.path.join(cache_dir, 'nhanes_variables.html')

    # Generate HTML and write to file
    itables.options.maxBytes = 0
    html = to_html_datatable(df)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # Open in browser
    webbrowser.open('file://' + os.path.abspath(html_path))


import os
import hashlib


def get_dataset(dataset_or_link):
    """
    Download a dataset (SAS XPT file) by dataset name (e.g., 'AUXAR') or direct link and return as a pandas DataFrame.
    If a dataset name is provided, it will look up the correct link in nhanes_variables.csv.
    Uses a cache directory in the user's home (~/.cache/pandas_nhanes/) to avoid re-downloading datasets.
    """
    # Determine dataset link
    if dataset_or_link.startswith('http'):
        dataset_link = dataset_or_link
        cache_key = hashlib.sha256(dataset_link.encode('utf-8')).hexdigest()
        cache_name = f"{cache_key}.xpt"
    else:
        # Lookup by dataset name
        variables = get_variables()
        match = variables[variables['dataset'] == dataset_or_link]
        if match.empty:
            raise ValueError(f"Dataset '{dataset_or_link}' not found in variables table.")
        dataset_link = match.iloc[0]['dataset link']
        cache_name = f"{dataset_or_link}.xpt"

    # Set up cache directory
    cache_dir = os.path.join(os.path.expanduser('~'), '.cache', 'pandas_nhanes')
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, cache_name)

    # Use cache if available
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            xpt_data = f.read()
    else:
        response = requests.get(dataset_link)
        response.raise_for_status()
        xpt_data = response.content
        with open(cache_path, 'wb') as f:
            f.write(xpt_data)

    return pd.read_sas(io.BytesIO(xpt_data), format='xport', encoding='utf-8')
