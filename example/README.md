# YAML Structure of study definition

Converts sets of your custom yaml files to cbio-compatible csvs and uploads them
in a secure way!

### The Basic Structure

````yaml
output_folder: absolute/or/relative/to/the/tool/

# Study Metadata
study_id:
cancer_type: colorectal
study_name:
study_description:

# Cancer types definition
cancer_types:
  gastrointestinal:
    name: Gastrointestinal Cancer
    ui_color: lightcoral  # color name to visualize
    parent: null  # can be ommited, no parent cancer type
  colorectal:
    name: Colorectal Cancer
    ui_color: lightcoral  # color name to visualize
    parent: gastrointestinal  # child of the above

# Patient Dataset
patients:
    file: "path/to/file"
    columns:
      - id: PATIENT_ID
        name: Patient ID
        description: ID of the patient
        data_type: STRING                  # one of STRING, NUMBER or BOOLEAN.

samples:
    ... same as patients ...
    
# Resource use arbitrary, non-reserved keys.
my_custom_resource:
    file: "path/to/file"
    resource:                          # Resource recognized by this key, note it is object not an array! 
      id: MY_RESOURCE_ID  
      name: My Awesome Resource
      description: Some resource description.
      resource_type: SAMPLE            # one of SAMPLE, PATIENT or STUDY.
      open_by_default: false           #this property supported only here
    columns:
      ... same as patients ...
````

Simple enough! Just describes the study and cancer, the client, their samples and possibly some custom resource file.
But dealing with data is usually not that simple, right?


### CBioPortal Specifics
Reserved keywords are all of the above: global variables (e.g. `delimier`), `patients`... etc.
Some have additional implicit rules which will be reported by the tool if not kept. Other rules
have just feature implications, they are not required. These are described here:

#### Special column IDs you can use for `samples`:
These columns have further meaning on what features are available with samples. Include these IDs in clumns to enable them.
````yaml
# CANCER_TYPE: Overrides study wide cancer type
# CANCER_TYPE_DETAILED
# KNOWN_MOLECULAR_CLASSIFIER
# GLEASON_SCORE: Radical prostatectomy Gleason score for prostate cancer
# HISTOLOGY
# TUMOR_STAGE_2009
# TUMOR_GRADE
# ETS_RAF_SPINK1_STATUS
# TMPRSS2_ERG_FUSION_STATUS
# ERG_FUSION_ACGH
# SERUM_PSA
# DRIVER_MUTATIONS
````


### Custom CSV Delimier & Study group

````yaml
delimiter: 
group: SOME_GROUP_NAME  # PUBLIC group is used for authorization bypassing
````

## Columns
We can do more with columns. If we want to order them manually, we can set
````yaml
    columns:
        ...
        priority: 5
````
When **our intput and output columns differ**, we can do:
````yaml
    columns:
      - id: <how cbio gets the column name>
        source_id: <what the source csv column name is>
````
To define a constant value, we can say:
````yaml
    columns:
      - id: my_constant
        value: constant
````
### Functions
Not only in columns, we can use _functions_. These might come from existing modules.
Just provide `name.of.module.function_name` path. But remember, ALL FUNCTIONS
get as a first value the main value - based on context. 

Custom functions are defined in custom functions file, which you need to specify path to.
````python
def fn(x, my_arg):
    return x + my_arg
````
using `` poetry run python -m cbio_importer  --functions=path/to/functions.py  path/to/study.yaml`` (or setting the value
via ENV) we can do something like
````yaml
    columns:
      - id: my_constant
        source_id: target_column_to_add_3
        function:
          name: fn
          my_arg: 3
````

Apart from built-in functions that python supports, you can also import library functions (`uuid.uuid4` for example)
if available, and there are even built-in functions for specific cbioportal scenarios. See
`study_templates/default_functions`. TODO: Have examples

Neat!


#### Function Types
Depending on a function use, different functions can be used for different purposes, for example functions that return boolean
should be used for filtering logics and so on. But generally, all functions are usable in every context, **but only if the 
first value type fits**.

In general there are two types of functions:
 - that take `pd.Series` first argument, these functions are typically applied to a list of values (.e.g used with `source_ids`)
 - that take a cell value like `str`, `int` or similar: these functions are typically applied to a single cell (.e.g used with `source_id`)

Of course, if given function expects an integer, you cannot supply it with an essay about your childhood. Please, check your functions
in question.

## Filtering
Filtering is **always done first**. To remove selected rows, simply do:

````yaml
patients:
  file: ...
  filter:
    - source_id: my_column_to_filter_by_allowed_set_of_values
      one_of: ['val1', 'val2']
    - source_id: my_column_to_filter_by_regex
      regex: "^\w$"
    - source_id: my_column_to_filter_by_operator
      operator:
        command: > # one of "<" "<=" "==" "=>" ">" "!="    value <op> arg
        arg: 3     # select values bigger than 3
````
Neat!

## Grouping
Okay, what about joining rows together? No problem!
> Note that if aggregation <source_id> and <id> differ, the column name changes!
Depending on the order of operations (filter -> gruop -> join -> columns) you **must
respect new column names**.
````yaml

patients:
  file: ...
  group:
    by: ["col1", "col2"]
    # optionally include other columns that are not used to group
    aggregate:  # optionally include other columns that are not used to group
      - id: my_new_column # respect the name change !!!
        source_id: non-grouped-column
        value: replace_by_a_constant
        # or use a function, but beware: the function first arguments will be array of all values in the group
  columns:
    - id: <whatever_if_i_want_different_name>
      source_id: my_new_column # !!!
      ...
````
Also valid:

````yaml
patients:
  file: ...
  group:
    by: ["col1", "col2"]
````
Hmm are we trying to build an SQL here?

## Joins
Almost. But under the hood we are just calling pandas, so it is actually not really that difficult.

To join with any other csv files, simple define join rule and which columns to match on.
````yaml
patients:
  file: ...
  join_last: false  #optional, default false
  join:
     - file: /path/to/file.csv
       how: "inner" 
       lsuffix: "x_"  #optional, used on column name collision
       rsuffix: "y_"  #optional, used on collision
       left_on: "match_source_file"  # or array
       right_on: "match_target"  # or array
````
<br>

> EACH of these can be used multiple times. You can filter using multiple rules, 
 join multiple tables and define grouping logics for multiple columns.
> Just <h3>REMEMBER TO KEEP THE OPERATION ORDER IN MIND WHEN RENAMING COLUMNS</h3>
