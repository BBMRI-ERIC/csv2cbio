import random
import hashlib

from ._utilities import write_meta_file, get_template_file_by_name, read_opt

from .patient import process as process_patient
from .sample import process as process_sample
from .resource import process as process_resources
from .cancer_type import process as process_cancer_types
from .time_series import process as process_time_series

reserved_keys = []


def _process_item(name, fn, options, study_yaml, data_selector=None):
    data = data_selector(study_yaml) if data_selector is not None else study_yaml.get(name, None)
    reserved_keys.append(name)
    if data is not None:
        fn(options, data)
        print(f"{name.capitalize()} generated.")
    else:
        print(f"{name.capitalize()} not defined - skipping.")


# generic simple item collector:
def _collect_top_level_nodes_that_have_child(study_yaml, child_name, child_type):
    result = []
    for key in study_yaml:
        if key in reserved_keys:
            continue
        item = study_yaml[key]
        if not isinstance(item, dict):
            continue
        resource = item.get(child_name, None)
        if isinstance(resource, child_type):
            resource["__key"] = key
            result.append(item)
        elif resource is not None:
            print(f"WARN: object {key} defines resource, but the resource is not a {child_type}! skipping...")
    return result

# resources are arbitrary keys that contain resource child
def _collect_resources(study_yaml):
    return _collect_top_level_nodes_that_have_child(study_yaml, "resource", dict)


# timelines are arbitrary keys that define
def _collect_time_series(study_yaml):
    return _collect_top_level_nodes_that_have_child(study_yaml, "series", dict)



def process(target_folder, study_yaml, source_prefix=""):
    # ensure stable results per study
    random.seed(int(hashlib.sha1(read_opt("study_id", study_yaml, assert_type=str).encode("utf-8"))
                    .hexdigest(), 16) % (10 ** 8))

    # Replaces meta {keys} with values from study_yaml object,
    # possibly specify default value for optionals using ':'
    write_meta_file(get_template_file_by_name("study.txt"), f"{target_folder}/meta_study.txt", study_yaml, [
        "cancer_type", "study_id", "study_name", "study_description", "group:PUBLIC"
    ])

    options = {
        "target_folder": target_folder,
        "source_prefix": source_prefix,
        "delimiter": study_yaml.get("delimiter", "\t"),
        "study_id": study_yaml["study_id"]
    }
    _process_item("cancer_types", fn=process_cancer_types, options=options, study_yaml=study_yaml)
    _process_item("patients", fn=process_patient, options=options, study_yaml=study_yaml)
    _process_item("samples", fn=process_sample, options=options, study_yaml=study_yaml)
    _process_item("resources", fn=process_resources, options=options, study_yaml=study_yaml,
                  data_selector=_collect_resources)
    _process_item("time_series", fn=process_time_series, options=options, study_yaml=study_yaml,
                  data_selector=_collect_time_series)
