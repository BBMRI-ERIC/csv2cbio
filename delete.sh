#!/bin/bash

ENV_SET=0
if [ -f .env ]; then
    source .env
    echo "Local Env configured."
    echo $(realpath .env)
    ENV_SET=1
    cbio_path=$(realpath "$CBIO_DEPLOY_FOLDER")
    study_folder_path=$(realpath "$CBIO_STUDY_FOLDER")
fi



# Enter THIS directory
cd "${0%/*}"
if [ $ENV_SET == 0 ]; then
    if [ -f .env ]; then
        source .env
        echo "Env configured."
        echo $(realpath .env)
    elif [ ! -z "${CBIO_STUDY_FOLDER}" ]; then
        echo "Using existing env configuration."
    else
        echo "Env missing: .env file not found"
        exit 1
    fi
    cbio_path=$(realpath "$CBIO_DEPLOY_FOLDER")
    study_folder_path=$(realpath "$CBIO_STUDY_FOLDER")
fi

if [ ! -d "$cbio_path" ]; then
    echo "Error: Cbioportal folder '$cbio_path' does not exist."
    exit 3
fi
if [ ! -d "$study_folder_path" ]; then
    echo "Error: Study folder '$study_folder_path' does not exist."
    exit 3
fi

# Function runner
try_run() {
    local error_message="$1"
    shift

    # Exec
    "$@"

    if [ $? -ne 0 ]; then
        echo "Error '$*' EXIT $?: $error_message"
        exit $?
    fi
}

read -p "Are you sure? [y/n] " -n 1 -r
echo 
if [[ $REPLY =~ ^[Yy]$ ]]
then
    cd $cbio_path
    try_run "Could not delete study defined in $study_folder_path!" \
        docker compose run \
        -v "$study_folder_path:/_to_delete_" \
        cbioportal \
        /core/scripts/importer/cbioportalImporter.py -c remove-study -meta "/_to_delete_/meta_study.txt"

    if [ ! -z "${CBIO_STUDY_FOLDER}" ]; then
        CBIO_IMPORT_ARGS=" $CBIO_IMPORT_ARGS"
    else
        CBIO_IMPORT_ARGS=""
    fi
fi


