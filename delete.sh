#!/bin/bash
source "${0%/*}/utils.sh"

if [ ! -d "$CBIO_DEPLOY_FOLDER" ]; then
    echo "Error: Cbioportal folder '$CBIO_DEPLOY_FOLDER' does not exist."
    exit 3
fi
if [ ! -d "$CBIO_STUDY_FOLDER" ]; then
    echo "Error: Study folder '$CBIO_STUDY_FOLDER' does not exist."
    exit 3
fi

echo "About to delete study defined in $CBIO_STUDY_FOLDER"
read -p "Are you sure? [y/n] " -n 1 -r
echo 
if [[ $REPLY =~ ^[Yy]$ ]]
then
    cd $CBIO_DEPLOY_FOLDER
    # First, start the container
    docker rm -f cbioportal-container-csv2cbio 2>/dev/null  #preemptive
    try_run "Failed to start the container!" \
        docker compose run \
        -v "$CBIO_STUDY_FOLDER:/_to_delete_" \
        -w /core/scripts \
        -d --rm --no-deps --name cbioportal-container-csv2cbio \
        cbioportal sleep infinity

    # Then, export the portalinfo metadata
    try_run "Failed to remove the study!" \
        docker exec cbioportal-container-csv2cbio  /core/scripts/importer/cbioportalImporter.py -c remove-study -meta "/_to_delete_/meta_study.txt"

    if [ ! -z "${CBIO_STUDY_FOLDER}" ]; then
        CBIO_IMPORT_ARGS=" $CBIO_IMPORT_ARGS"
    else
        CBIO_IMPORT_ARGS=""
    fi

    # Cleanup
    docker rm -f cbioportal-container-csv2cbio
fi


