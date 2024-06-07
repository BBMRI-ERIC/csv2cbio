# Cbio Importer

A arbitrary CSV convertor to cBioPortal-compatible csv study set.

On more information, see ``example/`` folder.
To run the cli on your machine, use:

`````bash
poetry install && poetry build && poetry run python -m cbio_importer
`````
which will print usage information. We recommend running the docker compose
which can connect to existing cbio deployment and import necessary data.
First, define ``.env`` file from `env_default`:
`````bash
cp env_default .env
`````
modify it as needed, and run

`````bash
docker compose up
`````

Example study generation from the host machine:
`````bash
poetry run python -m cbio_importer \
  --csv_path_prefix=example \
  --functions=example/functions.py \
  --output_path_prefix=example/output \
  example/study.yaml
`````


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