import os
import argparse
import subprocess
import sys
import json

import yaml

from cbio_importer.study_templates._singletons import FunctionDefinitionFile


def process_input(input_string):
    if input_string is None:
        raise ValueError("None is not a valid input yaml/json!")
    if os.path.isfile(input_string):
        with open(input_string, 'r') as file:
            content = file.read()
    else:
        content = input_string
    return content


def main():
    parser = argparse.ArgumentParser(description="Provide a study metadata file.")
    parser.add_argument('input', type=str, nargs="?", help='File path or study metadata content.', 
                        default=os.environ.get('CBIO_STUDY_DEFINITION', default=None))
    parser.add_argument('-f', '--functions', type=str, nargs="?", help='Optional functions file',
                        default=os.environ.get('CBIO_FUNCTIONS', default="functions.py"))
    parser.add_argument('--csv_path_prefix', type=str, nargs="?", help='Prefix to add to all CSV file paths',
                        default=os.environ.get('CBIO_CSV_PATH_PREFIX', default=""))
    parser.add_argument('--output_path_prefix', type=str, nargs="?", help='Prefix to add to the output folder',
                        default=os.environ.get('CBIO_OUTPUT_PATH_PREFIX', default=""))

    args = parser.parse_args()
    input_string = None
    if not sys.stdin.isatty():
        input_string = sys.stdin.read().strip()
    if not input_string and args.input:
        input_string = args.input
    else:
        parser.error("No input provided. Either provide a filename, file content, or use stdin.")

    study_meta = {}
    try:
        try:
            study_meta = json.loads(process_input(input_string))
        except Exception as e:
            study_meta = yaml.safe_load(process_input(input_string))
    except Exception as e:
        parser.error(f"Failed to load '{study_meta}' file! Is it a valid JSON / YAML?")

    if not isinstance(study_meta, dict):
        parser.error(f"Failed to load '{study_meta}' file! Is it a valid JSON / YAML? Got: {study_meta}")

    FunctionDefinitionFile(args.functions)

    prefix = args.csv_path_prefix
    print(os.environ.get('CBIO_CSV_PATH_PREFIX', default="prdel"))
    if isinstance(prefix, str) and prefix:
        if not prefix.endswith("/"):
            prefix = f"{prefix}/"
    else:
        prefix = ""

    out_prefix = args.output_path_prefix
    if isinstance(out_prefix, str) and out_prefix:
        if not out_prefix.endswith("/"):
            out_prefix = f"{prefix}/"
    else:
        out_prefix = ""
    target_folder = f"{out_prefix}{study_meta['output_folder'] or '.tmp/'}"
    os.makedirs(target_folder, exist_ok=True)
    from .study_templates import process
    process(target_folder=target_folder, study_yaml=study_meta, source_prefix=prefix)


if __name__ == "__main__":
    main()