import os
import argparse
import subprocess
import sys
import json
import pathlib
import random

import yaml

from cbio_importer.study_templates._singletons import FunctionDefinitionFile, TemporaryFilesDirectory, SeedValue


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
    parser.add_argument('-c', '--csv_path_prefix', type=str, nargs="?", help='Prefix to add to all CSV file paths',
                        default=os.environ.get('CBIO_CSV_PATH_PREFIX', default=""))
    parser.add_argument('-o', '--output_path_prefix', type=str, nargs="?", help='Prefix to add to the output folder',
                        default=os.environ.get('CBIO_OUTPUT_PATH_PREFIX', default=""))
    parser.add_argument('-m', '--meta_helper_files_directory', type=str, nargs="?", help='Where to store output helper files',
                        default=os.environ.get('CBIO_OUTPUT_META_FILES_PREFIX', default=""))
    parser.add_argument('-s', '--seed', type=int, nargs="?", help='Seed value for (pseudo) random number generation',
                        default=os.environ.get('CBIO_SEED_VALUE', default=10))
    parser.add_argument('--clean-state', action='store_true', help="Erase all temporary files before processing")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output")
    
    args = parser.parse_args()
    verbose_env = os.environ.get('CBIO_VERBOSE', default=None)
    is_verbose = args.verbose or (verbose_env and verbose_env != "False" and verbose_env != "false")
    
    SeedValue(args.seed)

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
    
    meta_folder = args.meta_helper_files_directory
    if not meta_folder:
        meta_folder = pathlib.Path(prefix) / pathlib.Path(".csv2cbio")
    else:
        meta_folder = pathlib.Path(meta_folder)
    meta_folder_abspath = os.path.abspath(meta_folder)
    TemporaryFilesDirectory(meta_folder_abspath)
    print(f"Temporary & helper files will be saved to {meta_folder_abspath}.")
    
    if os.path.exists(meta_folder_abspath): 
        if os.path.isfile(meta_folder_abspath): 
            raise Exception(f"Target path {meta_folder} is a file! We need this path to store helper files into.")
        elif args.clean_state and os.path.isdir(meta_folder_abspath): 
            print("Cleaning contents of the folder.")
            try:
                for item in os.listdir(meta_folder_abspath):
                    item_path = os.path.join(meta_folder_abspath, item)
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.remove(item_path)
                    # else do not delete directories, at least for now
            except Exception as e:
                print(f"Failed to clean directory {meta_folder}. {e}")
    else:
        try:
            os.makedirs(meta_folder_abspath)  # Create the directory if it doesn't exist
        except Exception as e:
            print(f"Failed to create directory {meta_folder}. {e}")
    
    # Newline before processing begins
    print()
    
    # Processing beings
    from .study_templates import process
    print(f"Processing data using data path {prefix}, output to {target_folder}")
    if is_verbose:
        yaml.dump(study_meta, sys.stdout)
    process(target_folder=target_folder, study_yaml=study_meta, source_prefix=prefix)


if __name__ == "__main__":
    main()