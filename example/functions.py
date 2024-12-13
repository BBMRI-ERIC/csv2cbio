import pathlib
import pandas as pd

# Retrieve the root sourcs path to fecth custom file etc..
data_folder = os.getenv("CBIO_CSV_PATH_PREFIX")

# Group-by handlers: the first arugment is pd.Series
def select_first(values: pd.Series):
    return values.iloc[0] if len(values) > 0 else None

def concat_paths(values: pd.Series, delimiter: str=",", prefix_remove: str=""):
    return delimiter.join([pathlib.Path(p).relative_to(prefix_remove).as_posix() for p in values])

# Value modifiers: the first argument is whatever comes from the data (e.g. if you decide to use it on a number column, it is a number)
def template_string(input:str, string:str="{value}", template_dict:dict={}):
    template_dict["value"] = input
    return string.format(**template_dict)