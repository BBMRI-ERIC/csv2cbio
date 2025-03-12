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


check_poetry() {
    COMMAND=poetry
    if ! command -v "$COMMAND" &> /dev/null; then
        echo "Command '$COMMAND' is not installed."
        read -p "Do you wish to install it? (y/n): " answer
        case $answer in
            [Yy]* )
                echo "Using $python"
                curl -sSL https://install.python-poetry.org | $python -
                if ! command -v "$COMMAND" &> /dev/null; then
                    add_to_path "$HOME/.local/bin" ~/.bashrc
                fi
                poetry env use $python
                ;;
            [Nn]* )
                echo "Skipping installation of '$COMMAND'."
                ;;
            * )
                echo "Invalid response. Skipping installation."
                ;;
        esac
    fi
}

check_poetry_install() {
    VENV_PATH=$(poetry env info --path 2>/dev/null)

    if [ -d "$VENV_PATH" ]; then
        echo "Poetry environment found at: $VENV_PATH"
        poetry run python -c "import yaml" &>/dev/null
        if [ $? -eq 0 ]; then
            echo
        else
            echo "Dependencies are missing. Running 'poetry install'..."
            poetry lock
            poetry install
        fi
    else
        echo "No Poetry environment found. Running 'poetry install'..."
        poetry install
        echo "finished with $?"
        if [ $? -ne 0 ]; then
            echo "The creation failed: attempting to run poetry lock..."
            poetry lock
            poetry install
        fi
    fi
}

add_to_path() {
    DIR=$1
    SHELL_RC=$2

    export PATH="$DIR:$PATH"
    if ! grep -Fxq "export PATH=\"$DIR:\$PATH\"" "$SHELL_RC"; then
        echo "export PATH=\"$DIR:\$PATH\"" >> "$SHELL_RC"
    fi
}