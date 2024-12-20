import pathlib
import pandas as pd
import os
import csv
# Keep imported!
import uuid

# Do not use relative imports here, since it is being dynamically imported!
from cbio_importer.study_templates._singletons import TemporaryFilesDirectory


"""
Single Value Transformers
"""


def template_string(value: str, string: str = "{value}", template_dict: dict = {}):
    """
    Format string argument. The input value is passed as 'value' to the formatter.
    :param value: argument passed by the library - the reference value
    :param string: the string to substitute values with
    :param template_dict: additional values to substitute in the string if desired
    :return:
    """
    template_dict["value"] = value
    return string.format(**template_dict)


def os_status_alive_deceased(value: str, compare: str = "alive"):
    """
    Remap custom 'alive' / 'deceased' marks to cbioportal syntax
    :param value: argument passed by the library - the reference value
    :param compare: compare the value axainst this value (lowercase), if it euquals
    :return: cbioportal-comparible syntax
    """
    return "0:LIVING" if value.lower() == compare else "1:DECEASED"


"""
Multi-value Transformers
"""


def select_first(values: pd.Series):
    """
    Select first of the value list
    :param values: argument passed by the library - the reference values
    :return: the first value
    """
    return values.iloc[0] if len(values) > 0 else None


def concat_paths(values: pd.Series, delimiter: str = ",", prefix_remove: str=""):
    """
    Concatenate path values to a string, useful for WSI service concatenated list of IDs / paths
    :param values: argument passed by the library - the reference values
    :param delimiter: delimiter to concatenate with, default ","
    :param prefix_remove: all paths are relative to this prefix, and if they start with it - it is removed
    :return: concatenated paths
    """
    return delimiter.join([pathlib.Path(p).relative_to(prefix_remove).as_posix() for p in values])


def template_string_list(values: pd.Series, string: str = "{value}", template_dict: dict = {}):
    """
    Format string argument. The input value is passed as 'value' to the formatter.
    :param values: argument passed by the library - the reference values
    :param string: the string to substitute values with
    :param template_dict: additional values to substitute in the string if desired
    :return:
    """
    return template_string(values.tolist(), string=string, template_dict=template_dict)



"""
Single-value Predicates
"""


unique_sets = {}
def is_unique(value: str, context: str):
    """
    Check if value already encountered or not. Useful to select only first occurrence in filters.
    :param value: argument passed by the library - the reference value
    :param context: unique id of the selection process, use the same value for comparing in the same context
    :return: True if first occurrence
    """
    global unique_sets
    ctx = unique_sets.get(context, None)
    if ctx is None:
        ctx = set()
        unique_sets[context] = ctx
    if value not in ctx:
        ctx.add(value)
        return True
    return False


# Patient ID unique on biopsy number
def anonymize(value, mapper_filename: str = "anonym_mappings.csv", generator: str = "increment", *args, **kwargs):
    """
    Anonymize given value. Store mappings in a temporary file 'mapper_filename'.
    :param value: argument passed by the library - the reference value
    :param mapper_filename: filename to store mappings in
    :param generator: generator name for the IDs. 'value' is given as the first argument. Usage:
        "increment" (default) increment will provide numbers from 1, use kwargs: "zfill" to control padding of zeros,
                    "prefix" to add custom prefix at the beginning of the number
                    NOTE: order of numbers will LEAK the order in which data comes, 100% safe only if rows are ordered
                    randomly
        "uuid.uuid4" use random UUIDs, no additional values necessary
        "uuid.uuid5" need to set kwarg "namespace", an uuid value

        ... etc ... use any function with module prefix you like

    :param args: arguments for the ID generator function
    :param kwargs: arguments for the ID generator function
    :return: unique ID
    """
    data_folder = TemporaryFilesDirectory(None).path
    dealer = _get_function_by_name(generator)
    nid = dealer(value, *args, **kwargs)
    with open(f"{data_folder}/{mapper_filename}", 'a') as file:
        print(nid, value, sep="\t", file=file)
    return nid


def deanonymize(value, mapper_filename: str = "anonym_mappings.csv"):
    """
    Find original ID of anonymized value
    :param value: argument passed by the library - the reference value
    :param mapper_filename: filename to store mappings in
    :return: unique ID added as 'anonymize'
    """
    data_folder = TemporaryFilesDirectory(None).path
    value = str(int(value))
    with open(f"{data_folder}/{mapper_filename}", mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter="\t")
        for row in reader:
            if row[1] == value:
                return row[0]
    raise Exception(f"Unknow anonymized ID (reading {mapper_filename}): {value}")


def anonymize_list(values: pd.Series, mapper_filename: str = "anonym_mappings.csv", generator: str = "increment", *args, **kwargs):
    return anonymize(values.str.cat(sep='~'), mapper_filename=mapper_filename, generator=generator, *args, **kwargs)


def deanonymize_list(values: pd.Series, mapper_filename: str = "anonym_mappings.csv"):
    return deanonymize(values.str.cat(sep='~'), mapper_filename=mapper_filename)


def gen_simple_patient_id(value, mapper_filename: str = "patient_mappings.csv"):
    return anonymize(value, mapper_filename=mapper_filename, generator="increment", prefix="P")


def ret_simple_patient_id(value, mapper_filename: str = "patient_mappings.csv"):
    return deanonymize(value, mapper_filename=mapper_filename)


def gen_simple_sample_id(value, mapper_filename: str = "sample_mappings.csv"):
    return anonymize(value, mapper_filename=mapper_filename, generator="increment", prefix="S")


def ret_simple_sample_id(value, mapper_filename: str = "sample_mappings.csv"):
    return deanonymize(value, mapper_filename=mapper_filename)


"""
Helpers, not for direct use
"""


def _get_function_by_name(full_name):
    parts = full_name.split('.')
    if len(parts) == 1:
        func = globals().get(full_name)
    else:
        module_name = '.'.join(parts[:-1])
        func_name = parts[-1]
        try:
            module = globals().get(module_name) or __import__(module_name)
            func = getattr(module, func_name)
        except (ImportError, AttributeError) as e:
            raise NameError(f"Function '{full_name}' not found. Error: {e}")
    if callable(func):
        return func
    else:
        raise ValueError(f"{full_name} is not callable.")


id_dealer = 0
def increment(_, prefix: str = "", zfill: int = 5):
    global id_dealer
    id_dealer = id_dealer + 1
    return prefix + str(id_dealer).zfill(zfill)