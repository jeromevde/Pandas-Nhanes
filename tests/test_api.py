import pandas_nhanes

def test_import():
    assert hasattr(pandas_nhanes, 'download_full_cycle_dataframe')
