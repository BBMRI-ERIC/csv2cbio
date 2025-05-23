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

cd $CBIO_DEPLOY_FOLDER
if [ -d "$CBIO_TEMP_FOLDER" ]; then
  exists_temp=0
else
  exists_temp=1
fi

# if [ -e "$CBIO_TEMP_FOLDER/portalinfo" ]; then
#     echo "Error: Folder '$CBIO_TEMP_FOLDER/portalinfo' must not exist - it will be rewritten with existing data."
#     exit 3
# fi


# First, start the container
docker rm -f cbioportal-container-csv2cbio 2>/dev/null  #preemptive
try_run "" \
    docker compose run \
    -v "$CBIO_STUDY_FOLDER:/_to_import_" \
    -v "$CBIO_TEMP_FOLDER/portalinfo:/portalinfo" \
    -w /core/scripts \
    -d --rm --no-deps --name cbioportal-container-csv2cbio \
    cbioportal sleep infinity

# Then, export the portalinfo metadata
try_run "Failed to export cbioportal page metadata required for study validation!" \
    docker exec cbioportal-container-csv2cbio ./dumpPortalInfo.pl /portalinfo


if [ ! -z "${CBIO_STUDY_FOLDER}" ]; then
    CBIO_IMPORT_ARGS=" $CBIO_IMPORT_ARGS"
else
    CBIO_IMPORT_ARGS=""
fi

echo "#######################################################################"
echo "Importing the content of '$CBIO_STUDY_FOLDER'":
ls $CBIO_STUDY_FOLDER
echo
echo Note: CBIO_IMPORT_ARGS $CBIO_IMPORT_ARGS
echo "\$> metaImport.py -p $CBIO_TEMP_FOLDER/portalinfo -s $CBIO_STUDY_FOLDER --html=$CBIO_STUDY_FOLDER/report.html ${CBIO_IMPORT_ARGS}"
echo

try_run "Failed to import study!" \
    docker exec cbioportal-container-csv2cbio /core/scripts/importer/metaImport.py -p /portalinfo -s /_to_import_ --html=/_to_import_/report.html$CBIO_IMPORT_ARGS


if [ $exists_temp ]; then
    rm -rf "$CBIO_TEMP_FOLDER/portalinfo"
else
    rm -rf "$CBIO_TEMP_FOLDER"
fi
# Cleanup
docker rm -f cbioportal-container-csv2cbio 
