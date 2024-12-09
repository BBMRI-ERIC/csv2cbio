#!/bin/bash

source "${0%/*}/utils.sh"

echo "Executing: 'python -m cbio_importer $@'"
set -a && source .env && set +a && poetry run python -m cbio_importer $@
