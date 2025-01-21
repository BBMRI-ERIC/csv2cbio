#!/bin/bash

source "${0%/*}/utils.sh"

check_poetry
check_poetry_install

echo "Executing: '$python -m cbio_importer $@'"
poetry run $python -m cbio_importer $@
