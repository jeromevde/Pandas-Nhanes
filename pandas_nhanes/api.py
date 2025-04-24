import pandas as pd
import requests
import io
from collections import OrderedDict
from tqdm import tqdm

def list_cycle_variables(cycle):
    """
    List all variables available for a given NHANES cycle.

    Parameters
    ----------
    cycle : str
        The NHANES cycle (e.g., '2021-2023').

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns: 'variable name', 'variable explanation', 'cycle dataset link'.

    Examples
    --------
    >>> from pandas_nhanes import list_cycle_variables
    >>> vars_df = list_cycle_variables('2021-2023')
    >>> print(vars_df.head())
    """
    import importlib.resources
    with importlib.resources.path("pandas_nhanes", "nhanes_variables.csv") as csv_path:
        data = pd.read_csv(csv_path)
    return data[data["cycle name"] == cycle][["variable name", "variable explanation", "cycle dataset link"]]


def list_cycles():
    """
    List all available NHANES cycles.

    Returns
    -------
    list of str
        List of unique NHANES cycle names.
    """
    import importlib.resources
    with importlib.resources.path("pandas_nhanes", "nhanes_variables.csv") as csv_path:
        data = pd.read_csv(csv_path)
    return list(data["cycle name"].unique())


def get_variable_data(variables, cycle):
    """
    Retrieve data for specific variables from a given NHANES cycle.

    Parameters
    ----------
    variables : list of str or str
        List of variable names (or single variable name) to retrieve.
    cycle : str
        The NHANES cycle (e.g., '2021-2023').

    Returns
    -------
    pandas.DataFrame
        DataFrame containing SEQN as index and columns for each requested variable.

    Raises
    ------
    ValueError
        If any variables are not found in the specified cycle or in the dataset.

    Examples
    --------
    >>> from pandas_nhanes.api import get_variable_data
    >>> df = get_variable_data(['LBXTST', 'DR1TCAFF'], '2021-2023')
    >>> print(df.head())
    """
    # If input is a single string, convert it to a list
    if isinstance(variables, str):
        variables = [variables]
    # Find all rows in the variable metadata for the given cycle and requested variables
    import importlib.resources
    with importlib.resources.path("pandas_nhanes", "nhanes_variables.csv") as csv_path:
        data = pd.read_csv(csv_path)
    matching_rows = data[(data["cycle name"] == cycle) & (data["variable name"].isin(variables))]
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


def download_full_cycle_dataframe(cycle, replace_names_with_descriptions=False):
    """
    Download and merge all datasets for a given NHANES cycle, joining on SEQN.

    Parameters
    ----------
    cycle : str
        The NHANES cycle (e.g., '2021-2023').
    replace_names_with_descriptions : bool, optional
        If True, replace variable names with their descriptions for clarity (default: False).

    Returns
    -------
    pandas.DataFrame
        The full merged DataFrame for the cycle, indexed by SEQN.

    Raises
    ------
    ValueError
        If no datasets are found for the given cycle.

    Examples
    --------
    >>> from pandas_nhanes.api import download_full_cycle_dataframe
    >>> df = download_full_cycle_dataframe('2021-2023', replace_names_with_descriptions=True)
    >>> print(df.head())
    """
    # Get the DataFrame listing all datasets for the cycle
    cycle_variables = list_cycle_variables(cycle)
    print("DEBUG: cycle_variables columns:", cycle_variables.columns)
    # Get unique dataset links for the cycle
    dataset_links = cycle_variables["cycle dataset link"].unique()
    dfs = []
    for dataset_link in tqdm(dataset_links, desc="Downloading datasets"):
        df = download_xpt_as_csv(dataset_link)
        if "SEQN" in df.columns:
            df = df.groupby("SEQN").mean(numeric_only=True)
            dfs.append(df)
    # Merge all DataFrames on SEQN (outer join to preserve all SEQN values)
    if dfs:
        full_df = pd.concat(dfs, axis=1, join="outer")
        if replace_names_with_descriptions:
            # Build mapping from variable name to description
            var_desc = cycle_variables.set_index("variable name")["variable explanation"].to_dict()
            # Prepare new columns: keep SEQN as is if present, otherwise replace variable names
            new_columns = []
            for col in full_df.columns:
                if col == "SEQN":
                    new_columns.append(col)
                else:
                    new_columns.append(var_desc.get(col, col))
            full_df.columns = new_columns
        return full_df
    else:
        raise ValueError(f"No datasets found for cycle {cycle}")
