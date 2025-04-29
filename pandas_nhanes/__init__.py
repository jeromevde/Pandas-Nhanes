# pandas_nhanes package init
"""
pandas_nhanes
=============

A package for accessing and processing NHANES data using pandas.

Public API functions can now be imported directly from the top-level package, e.g.:
    from pandas_nhanes import get_variable_data, list_cycle_variables, download_full_cycle_dataframe
"""

from .api import (
     get_variables, get_dataset, explore
)
