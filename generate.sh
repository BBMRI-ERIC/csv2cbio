#!/bin/bash

source "${0%/*}/utils.sh"

check_poetry
check_poetry_install
if [ $? -ne 0 ]; then
    echo "Failed to create venv!"
    exit $?
fi

echo "Executing: '$python -m cbio_importer $@'"
poetry run $python -m cbio_importer $@
