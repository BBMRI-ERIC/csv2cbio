# Cbio Importer

A arbitrary CSV convertor to cBioPortal-compatible csv study set. It is using the **offline study import** for cbioportal docker deployment.

> [!IMPORTANT]  
> Still under development!

On more information, see ``example/`` folder.
To run app on your machine use:

`````bash
poetry install && poetry build && poetry run python -m cbio_importer --help
`````
which will print usage information. 

Example study generation from the host machine:
`````bash
poetry run python -m cbio_importer \
  --csv_path_prefix=example \
  --functions=example/functions.py \
  --output_path_prefix=example/output \
  example/study.yaml
`````
Or, provide arguments as .env configuration and run instead:
```bash
set -a && source .env && set +a && poetry run python -m cbio_importer
```

Once ready, you can import your data using `import.sh`:
```
# you have to provide these in `.env` file or manually export in your shell
CBIO_DEPLOY_FOLDER=../../cbioportal-deployment               # path to cbioportal docker-compose.yml
CBIO_IMAGE_NAME=cbioportal-6.0.17-7-g631429dbb8-dirty-bbmri  # docker image name to use
CBIO_TEMP_FOLDER=temp                                        # any folder (best non-existent) to use for temp data
CBIO_STUDY_FOLDER=example/output                             # study folder where .csv files for import exist
```
and run
`./import.sh`


# Features:
Supported cbioportal entities:
 - study
   - patient
   - sample
   - resource
     - sample resource
     - patient resource
     - study resource

Supported operations:
 - [x] custom functions
 - [x] filtering
 - [x] joins
 - [x] grouping