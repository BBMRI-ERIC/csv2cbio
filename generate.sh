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

echo "Executing: 'python -m cbio_importer $@'"
set -a && source .env && set +a && poetry run python -m cbio_importer $@
