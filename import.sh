#!/bin/bash

if [ -f .env ]; then
    source .env
    echo "Env configured."
elif [ ! -z "${CBIO_STUDY_FOLDER}" ]; then
    echo "Using existing env configuration."
else
    echo "Env missing: .env file not found"
    exit 1
fi




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

cbio_path=$(realpath "$CBIO_DEPLOY_FOLDER")
echo $cbio_path
if [ ! -d "$cbio_path" ]; then
    echo "Error: Cbioportal folder '$cbio_path' does not exist."
    exit 3
fi

temp_folder_path=$(realpath "$CBIO_TEMP_FOLDER")

study_folder_path=$(realpath "$CBIO_STUDY_FOLDER")
if [ ! -d "$study_folder_path" ]; then
    echo "Error: Study folder '$study_folder_path' does not exist."
    exit 3
fi


cd $cbio_path

exists_temp=$("[ -d \"$study_folder_path\" ]")

# if [ -e "$temp_folder_path/portalinfo" ]; then
#     echo "Error: Folder '$temp_folder_path/portalinfo' must not exist - it will be rewritten with existing data."
#     exit 3
# fi

try_run "Could not export cbioportal image info for offline import!" \
    docker compose run \
    -v "$temp_folder_path/portalinfo:/portalinfo" \
    -w /core/scripts \
    cbioportal \
    ./dumpPortalInfo.pl /portalinfo

if [ ! -z "${CBIO_STUDY_FOLDER}" ]; then
    CBIO_IMPORT_ARGS=" $CBIO_IMPORT_ARGS"
else
    CBIO_IMPORT_ARGS=""
fi

echo "#######################################################################"
echo "Importing the content of '$study_folder_path'":
ls $study_folder_path
echo
echo Note: CBIO_IMPORT_ARGS $CBIO_IMPORT_ARGS
echo "\$> metaImport.py -p $temp_folder_path/portalinfo -s $study_folder_path --html=$study_folder_path/report.html ${CBIO_IMPORT_ARGS}"
echo


try_run "Study import failed!" \
    docker compose run \
    -v "$study_folder_path:/_to_import_" \
    -v "$temp_folder_path/portalinfo:/portalinfo:ro" \
    cbioportal \
    /core/scripts/importer/metaImport.py -p /portalinfo -s /_to_import_ --html=/_to_import_/report.html$CBIO_IMPORT_ARGS

if [ $exists_temp ]; then
    rm -rf "$temp_folder_path/portalinfo"
else
    rm -rf "$temp_folder_path"
fi