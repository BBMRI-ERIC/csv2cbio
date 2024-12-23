# Cbio Importer

A arbitrary CSV convertor to cBioPortal-compatible csv study set. It is using the **offline study import** for cbioportal docker deployment.
This importer expects cbioportal usage with docker compose, and uses this to automate study validation & import.

Python, Poetry, and Linux or WSL subsystem required.

## How to Setup
> [!IMPORTANT]  
> For usage examples, see ``example/`` folder.

In general, you need to have a csv files with data, `study.yaml` file that
describes how to transform csvs to cbioportal-compatible csvs. And `.env` definitions in case you want to avoid passing
all the options manually through CLI.

## How to Run Study Generator
Once a study is ready, run the study generator. Install required libraries if you haven't already:

`````bash
poetry install && poetry build
`````
Recommeded usage is to create `.env` file with configurations. Note that you can basically copy this example below AS-IS.
`functions.py` and `study.yml` should exist in the desired directory of course (functions file might actually not exist if unused).
```bash
CBIO_CSV_PATH_PREFIX=.
CBIO_FUNCTIONS=functions.py
CBIO_STUDY_DEFINITION=study.yml
CBIO_OUTPUT_PATH_PREFIX=.
```
and simply run `generate.sh` **from the folder of `.env` file**. Do **NOT** use the repository folder for generating studies. Simply run
the generate script relative (or absolute) path relative to the folder that defines env file.

Alternatively, provide arguments manually:
`````bash
poetry run python -m cbio_importer \
  --csv_path_prefix=example \
  --functions=example/functions.py \
  --output_path_prefix=example/output \
  example/study.yaml
`````
Or, provide arguments as desired .env configuration and run instead:
```bash
set -a && source .env && set +a && poetry run python -m cbio_importer
```

## How to Import studies
CBioPortal must be running in a docker compose setup. If you have custom docker compose with custom
service names, this will not work for you - you should keep to the official docker compose. Of course,
generated studies can be imported in any way you would like, but this process automates it for you.


Add the following to the env file:
```
# you have to provide these in `.env` file or manually export in your shell
CBIO_DEPLOY_FOLDER=../../cbioportal-deployment               # path to cbioportal docker-compose.yml
CBIO_IMAGE_NAME=cbioportal-6.0.17-7-g631429dbb8-dirty-bbmri  # docker image name to use
CBIO_TEMP_FOLDER=temp                                        # any folder (best non-existent) to use for temp data
CBIO_STUDY_FOLDER=example/output                             # study folder where .csv files for import exist
```
and run `[path]/[to]/import.sh` to create or update study data.

To delete a study, simply run ``[path]/[to]/delete.sh``.


# Features:
Each data entity must be supported. For now, only few are supported. Adding support for new entries should be farily easy. 

Supported cbioportal entities:
 - [ ] study
   - [x] patient
   - [x] sample
   - [x] resource
     - [x] sample resource
     - [x] patient resource
     - [x] study resource
   - [ ] ... request other types

Supported operations on csv files:
 - [x] custom functions
 - [x] custom new variables, value derivation
 - [x] filtering
 - [x] joins
 - [x] grouping

## Commands & Binaries Used
By default, `docker compose` is used to run the commands. You can override this 
 by setting `DOCKER_COMPOSE_BIN="docker-compose"`.

By default, `python` is used to run cbio2csv. You can override this 
 by setting for example `PYTHON_BIN="python3"`. You might also want to set `PIP_BIN="pip3"` in this case.
