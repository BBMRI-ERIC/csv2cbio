#!/bin/bash

source "${0%/*}/utils.sh"

echo "Executing: '$python -m cbio_importer $@'"
poetry run $python -m cbio_importer $@
