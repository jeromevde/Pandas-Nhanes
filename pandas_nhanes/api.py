import pandas as pd

def get_cycle_variables(cycle, *vars):
    """
    Load and sequentially merge variables from a specific NHANES cycle, logging the number of values kept/lost at each merge.
    Returns a DataFrame with SEQN and the requested variables.
    """
    variables = get_variables()
    var_to_file = {}
    for var in vars:
        match = variables[(variables['cycle name'] == cycle) & (variables['variable name'] == var)]
        if match.empty:
            print(f"[pandas_nhanes] Variable '{var}' not found in cycle '{cycle}'. Skipping.")
            continue
        file = match.iloc[0]['dataset']
        var_to_file[var] = file
    # Load and merge sequentially
    dfs = []
    for var, file in var_to_file.items():
        # Use pandas.read_sas directly
        import importlib.resources
        import pandas as pd
        import io
        import hashlib
        import os
        import requests
        variables = get_variables()
        match = variables[variables['dataset'] == file]
        if match.empty:
            print(f"[pandas_nhanes] Dataset '{file}' not found in variables table. Skipping.")
            continue
        dataset_link = match.iloc[0]['dataset link']
        cache_name = f"{file}.xpt"
        cache_dir = os.path.join(os.path.expanduser('~'), '.cache', 'pandas_nhanes')
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, cache_name)
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                xpt_data = f.read()
        else:
            response = requests.get(dataset_link)
            response.raise_for_status()
            xpt_data = response.content
            with open(cache_path, 'wb') as f:
                f.write(xpt_data)
        df = pd.read_sas(io.BytesIO(xpt_data), format='xport', encoding='utf-8')
        if 'SEQN' not in df.columns:
            print(f"[pandas_nhanes] Dataset '{file}' for variable '{var}' does not have SEQN. Skipping.")
            continue
        if var not in df.columns:
            print(f"[pandas_nhanes] Variable '{var}' not found in file '{file}'. Skipping.")
            continue
        dfs.append(df[['SEQN', var]])
    if not dfs:
        print("[pandas_nhanes] No variables with SEQN found. Returning empty DataFrame.")
        import pandas as pd
        return pd.DataFrame()
    # Merge sequentially, logging values kept/lost
    from functools import reduce
    def merge_log(left, right):
        before = len(left)
        merged = left.merge(right, on='SEQN', how='outer')
        after = len(merged)
        print(f"Merging: kept {after} rows (was {before}), lost {before - after} (NaNs may increase)")
        return merged
    result = reduce(merge_log, dfs)
    return result


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
