import os
import argparse
import subprocess
import sys
import json
import pathlib

import yaml

from cbio_importer.study_templates._singletons import FunctionDefinitionFile, TemporaryFilesDirectory


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
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output")
    
    args = parser.parse_args()
    verbose_env = os.environ.get('CBIO_VERBOSE', default=None)
    is_verbose = args.verbose or (verbose_env and verbose_env != "False" and verbose_env != "false")
    
    input_string = None
    if not sys.stdin.isatty():
        input_string = sys.stdin.read().strip()
    if not input_string and args.input:
        input_string = args.input
    else:
        parser.error("No input provided. Either provide a filename, file content, or use stdin (directly or via CBIO_STUDY_DEFINITION variable).")

    study_meta = {}
    try:
        try:
            study_meta = json.loads(process_input(input_string))
        except Exception as e:
            study_meta = yaml.safe_load(process_input(input_string))
    except Exception as e:
        parser.error(f"Failed to load '{study_meta}' file! Is input {input_string} a valid JSON / YAML? Error {e}")

    if not isinstance(study_meta, dict):
        parser.error(f"Failed to load data! Is input {input_string} a valid JSON / YAML? Got: {study_meta}")

    FunctionDefinitionFile(args.functions)

    prefix = args.csv_path_prefix
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
    
    out_folder = pathlib.Path(prefix) / pathlib.Path(".csv2cbio")
    out_folder_abspath = os.path.abspath(out_folder)
    TemporaryFilesDirectory(out_folder_abspath)
    print(f"Temporary & helper files will be saved to {out_folder_abspath}.")
    
    if os.path.exists(out_folder): 
        if os.path.isfile(out_folder): 
            raise Exception(f"Target path {out_folder} is a file! We need this path to store helper files into.")
        elif os.path.isdir(out_folder): 
            print("Cleaning contents of the folder.")
            try:
                for item in os.listdir(out_folder):
                    item_path = os.path.join(out_folder, item)
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.remove(item_path)
                    # else do not delete directories, at least for now
            except Exception as e:
                print(f"Failed to clean directory {out_folder}. {e}")
    else:
        try:
            os.makedirs(out_folder)  # Create the directory if it doesn't exist
        except Exception as e:
            print(f"Failed to create directory {out_folder}. {e}")
    print()
    
    # Processing beings
    from .study_templates import process
    print(f"Processing data using data path {prefix}, output to {target_folder}")
    if is_verbose:
        yaml.dump(study_meta, sys.stdout)
    process(target_folder=target_folder, study_yaml=study_meta, source_prefix=prefix)


if __name__ == "__main__":
    main()