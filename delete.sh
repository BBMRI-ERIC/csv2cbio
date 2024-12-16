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
    try_run "Could not delete study defined in $CBIO_STUDY_FOLDER!" \
        $docker_compose run \
        -v "$CBIO_STUDY_FOLDER:/_to_delete_" \
        cbioportal \
        /core/scripts/importer/cbioportalImporter.py -c remove-study -meta "/_to_delete_/meta_study.txt"

    if [ ! -z "${CBIO_STUDY_FOLDER}" ]; then
        CBIO_IMPORT_ARGS=" $CBIO_IMPORT_ARGS"
    else
        CBIO_IMPORT_ARGS=""
    fi
fi


