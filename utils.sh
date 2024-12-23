#!/bin/bash

function apply_realpath() {
    env_vars=("CBIO_DEPLOY_FOLDER" "CBIO_STUDY_FOLDER" "CBIO_CSV_PATH_PREFIX" "CBIO_FUNCTIONS" "CBIO_STUDY_DEFINITION" "CBIO_OUTPUT_PATH_PREFIX" "CBIO_TEMP_FOLDER") 
    for vname in "${env_vars[@]}"; do
    vvalue="${!vname}"
    if [ -z "$vvalue" ]; then
        echo "WARNING: Skipping unset or empty variable: $vname"
        continue
    fi
    # Enforce target directories/files exist, except some that can be created (output related)
    if [ -f "$vvalue" ]  || [ -d "$vvalue" ] || [ "$vname" == "CBIO_TEMP_FOLDER" ] || [ "$vname" == "CBIO_OUTPUT_PATH_PREFIX" ]; then
        vvalue=$(realpath "$vvalue")
        export "$vname"="$vvalue"
    fi
    #TODO: some prop might be ignored and error is hard to find... but the variable CBIO_STUDY_DEFINITION ca for example carry values,
    # or some are allowed to be missing, or we are running generate script that does not need all the options.. 
    done
}

ENV_SET=0
if [ -f .env ]; then
    source .env
    echo "Local Env configured." $(realpath .env)
    ENV_SET=1
    apply_realpath
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
    apply_realpath
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

docker_compose="${DOCKER_COMPOSE_BIN:=docker compose}"
python="${PYTHON_BIN:=python}"
pip="${PIP_BIN:=pip}"
