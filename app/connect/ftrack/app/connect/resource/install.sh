#!/bin/bash
# TODO: Do we want to allow use/reuse of an existing uv installation and its corresponding cache?
# TODO: Do we want to use installed python versions if they match our requirements?

# Don't allow unsetting of a variable (to prevent errors.)
set -u
# Stop the bash script when encountering an error
set -e

# Check the arch of the system
os_name=$(uname -s)

if [[ "$os_name" =~ ^CYGWIN ]]; then
    echo "Running in Cygwin on Windows."
    os_name="cygwin"
elif [[ "$os_name" =~ ^Linux ]]; then
    echo "Running on Linux."
    os_name="linux"
elif [[ "$os_name" =~ ^Darwin ]]; then
    echo "Running on Mac"
    os_name="darwin"
else
    echo "Unsupported Operating System."
fi

parse_args() {
    # Handle commandline arguments
    for arg in "$@"; do
        case "$arg" in
        --help)
            usage
            exit 0
            ;;
        esac
    done
}

function fill_temp_root() {
    if [[ -d "${TEMP:-false}" ]]; then
        temp_root="${TEMP}"
    elif [[ -d "${TMP:-false}" ]]; then
        temp_root="${TMP}"
    else
        return -1
    fi
    return 0
}

function fill_config_root() {
    if [[ -d "${XDG_CONFIG_HOME:-false}" ]]; then
        config_root="${XDG_CONFIG_HOME}"
    elif [[ -d "${LOCALAPPDATA:-false}" ]]; then
        config_root="${LOCALAPPDATA}"
    elif [[ -d "${HOME}/.config" ]]; then
        config_root="${HOME}/.config"
    else
        return -1
    fi
    return 0
}

function fill_cache_root() {
    if [[ -d "${XDG_CACHE_HOME:-false}" ]]; then
        cache_root="$XDG_CACHE_HOME"
    elif [[ -d "$HOME/.cache" ]]; then
        cache_root="$HOME/.cache"
    elif [[ -d "$APPDATA/Local/Cache" ]]; then
        cache_root="$APPDATA/Local/Cache"
    else
        return -1
    fi
    return 0
}

function usage() {
    cat <<EOF
    connect-installer.sh

    This is how you can use this installation script
EOF
}

function require_cmd() {
    if ! test_cmd "$1"; then
        echo "Requires '$1' (command not found)"
        exit 1
    fi
}

function test_cmd() {
    command -v "$1" > /dev/null 2>&1
    return $?
}

function conform_path() {
    if [[ "$os_name" == "cygwin" ]]; then
        cygpath -w "$1"
        return $?
    fi
    # TODO: bash on ubuntu/linux does not like the return of a non integer type
    return $1
}

function download_and_extract() {
    mkdir -p uv/{python,bin}
    if [[ "$os_name" == "cygwin" ]]; then
        curl -LsSf "https://github.com/astral-sh/uv/releases/download/0.5.5/uv-x86_64-pc-windows-msvc.zip" -o ./uv/uv.zip
        unzip ./uv/uv.zip -d ./uv/bin
    elif [[ "$os_name" == "linux" ]]; then
        curl -LsSf "https://github.com/astral-sh/uv/releases/download/0.5.5/uv-i686-unknown-linux-gnu.tar.gz" -o ./uv/uv.tar.gz
        tar -xzvf  ./uv/uv.tar.gz --strip-components=1 -C ./uv/bin
    elif [[ "$os_name" == "darwin" ]]; then
        curl -LsSf "https://github.com/astral-sh/uv/releases/download/0.5.5/uv-aarch64-apple-darwin.tar.gz" -o ./uv/uv.tar.gz
        tar -xzvf  ./uv/uv.tar.gz --strip-components=1 -C ./uv/bin
    fi
    chmod +x ./uv/bin/*
}

function install_connect() {
    parse_args

    require_cmd mktemp
    require_cmd mkdir
    require_cmd pushd
    require_cmd popd
    require_cmd rm
    require_cmd chmod
    require_cmd curl
    require_cmd unzip
    require_cmd tar

    ####################################################################################
    # Set up required paths                                                            #
    ####################################################################################

    # Temporary path for installation files which will go away once everything is properly installed
    # in the final destination.
    if ! fill_temp_root -eq 0; then
        echo "Can't determine temp directory. Please set your \$TEMP environment variable and try again."
        exit 1
    fi
    temp_installation_dir="$(mktemp -d $temp_root/ftrack-connect.XXXXXX)"

    # Final destination install path.
    if ! fill_config_root -eq 0; then
        echo "Can't determine config directory. Please set your \$XDG_CONFIG_HOME environment variable and try again."
        exit 1
    fi
    installation_dir="$config_root/ftrack/connect4"

    # Path for the uv cache. This should not really be needed/used when also setting UV_NO_CACHE.
    # We'll set it anyway, just in case.
    export UV_CACHE_DIR="${temp_installation_dir}/uv/cache"

    # Path to where uv will install its python distributions when using uv python install.
    export UV_PYTHON_INSTALL_DIR="$(conform_path '${temp_installation_dir}/uv/python')"

    # Don't use a cache when installing packages. We use this temporarily to not pollute our transient
    # installation even more
    export UV_NO_CACHE=1

    # Don't adjust bash profiles, bashrc or the PATH environment variable.
    # These should only be needed when using the installer and NOT downloading uv as a zip.
    export UV_UNMANAGED_INSTALL=1
    export INSTALLER_NO_MODIFY_PATH=1
    ##################### These are needed when using the uv installation script and NOT the manual download/unzip method.`
    #export UV_INSTALL_PATH=appdata\ftrack\connect\.venv
    ####################

    ####################################################################################
    # Download and unzip uv                                                            #
    ####################################################################################
    pushd $temp_installation_dir
    # Download and deploy/unzip uv.
    download_and_extract
    # Create the final installation folder.
    mkdir -p "${installation_dir}"
    # Create initial connect venv which we'll use for any further actions
    ./uv/bin/uv venv $(conform_path "${installation_dir}/.venv") --python 3.10.15
    popd

    ####################################################################################
    # Create venv and install required packages                                        #
    ####################################################################################
    pushd "${installation_dir}"
    source .venv/Scripts/activate
    "${temp_installation_dir}/uv/bin/uv" pip install uv
    # uv will now be automatically picked from the .venv subfolder
    # TODO: Download connect lockfile
    uv pip install poetry
    popd

    # delete the temporary installation folder
    # This MUST run last, otherwise uv won't automatically recognize the .venv anymore.
    # This can be worked around by explicitly activating the venv again after the rm command.
#    rm -r "${temp_installation_dir}"
}

install_connect "$@" || exit 1
