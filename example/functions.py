import pathlib

# Group-by handlers:
def select_first(values):
    return values[0] if len(values) > 0 else None

def concat_paths(values, delimiter=",", prefix_remove=""):
    return delimiter.join([pathlib.Path(p).relative_to(prefix_remove).as_posix() for p in values])

# Value modifiers:
def template_string(input, string="{value}", template_dict={}):
    template_dict["value"] = input
    return string.format(**template_dict)