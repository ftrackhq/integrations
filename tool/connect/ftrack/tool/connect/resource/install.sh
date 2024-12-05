#!/bin/sh
# TODO: Do we want to allow use/reuse of an existing uv installation and its corresponding cache?
# TODO: Do we want to use installed python versions if they match our requirements?
# TODO: Handle the case when connect is already installed. What do we do?
# TODO: Do we want to use system python interpreters or always download our own?
# TODO: Improve the readability of the output messages.

# Don't Echo any commands.
set echo off

# Don't allow unsetting of a variable (to prevent errors.)
set -u
# Stop the bash script when encountering an error
set -e


# Define bash styles
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
BOLD="\033[1m"
NC="\033[0m" # No Style

# Function to print info messages in green
message_info() {
  echo -e "$1"
}

# Function to print warning messages in yellow
message_warning() {
  echo -e "${YELLOW}$1${NC}"
}

# Function to print error messages in red
message_error() {
  echo -e "${RED}$1${NC}"
}

# Function to print error messages in green
message_success() {
  echo -e "${GREEN}$1${NC}"
}

# Check the arch of the system
os_name=$(uname -s)

if [[ "$os_name" =~ ^Linux ]]; then
    os_name="linux"
elif [[ "$os_name" =~ ^Darwin ]]; then
    os_name="darwin"
else
    message_error "Unsupported Operating System ${os_name}."
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

# TODO: Check and use the proper temp folder on mac.
fill_temp_root_variable() {
    if [[ -d "${TEMP:-false}" ]]; then
        temp_root="${TEMP}"
    elif [[ -d "${TMP:-false}" ]]; then
        temp_root="${TMP}"
    elif [[ -d "/var/tmp" ]]; then
        temp_root="/var/tmp"
    else
        return 1
    fi
    return 0
}

fill_config_root_variable() {
    if [ "${os_name}" = "linux" ]; then
      if [[ -d "${XDG_CONFIG_HOME:-false}" ]]; then
          config_root="${XDG_CONFIG_HOME}"
      elif [[ -d "${LOCALAPPDATA:-false}" ]]; then
          config_root="${LOCALAPPDATA}"
      elif [[ -d "${HOME}/.config" ]]; then
          config_root="${HOME}/.config"
      else
          return 1
      fi
    elif [ "${os_name}" = "darwin" ]; then
      if [[ -d "${HOME}/Library/Application Support" ]]; then
          config_root="${HOME}/Library/Application Support"
      else
        return 1
      fi
    fi
    return 0
}

fill_cache_root_variable() {
    if [[ -d "${XDG_CACHE_HOME:-false}" ]]; then
        cache_root="${XDG_CACHE_HOME}"
    elif [[ -d "${HOME}/.cache" ]]; then
        cache_root="${HOME}/.cache"
    else
        return 1
    fi
    return 0
}

usage() {
    cat <<EOF
    connect-installer.sh

    This is how you can use this installation script
EOF
}

require_cmd() {
    if ! test_cmd "$1"; then
        message_error "Requires '$1' (command not found)"
        exit 1
    fi
}

test_cmd() {
    command -v "$1" > /dev/null 2>&1
    return $?
}

execute_and_suppress_output() {
    command "$@" > /dev/null 2>&1
    return $?
}

install_connect() {
    parse_args
    require_cmd mktemp
    require_cmd mkdir
    require_cmd rm

    ####################################################################################
    # Set up required paths                                                            #
    ####################################################################################

    # Temporary path for installation files which will go away once everything is properly installed
    # in the final destination.
    if ! fill_temp_root_variable -eq 0; then
        message_error "Can't determine temp directory. Please set your \$TEMP environment variable and try again."
        exit 1
    fi
    temp_installation_dir="$(mktemp -d $temp_root/ftrack-connect.XXXXXX)"
    message_info "Downloading temporary installation files to ${temp_installation_dir}"

    # Final destination install path.
    if ! fill_config_root_variable -eq 0; then
        message_error "Can't determine config directory. Please set your \$XDG_CONFIG_HOME environment variable and try again."
        exit 1
    fi
    installation_dir="${config_root}/ftrack/connect4"
    message_info "Installation directory is ${installation_dir}"

    ####################################################################################
    # Set up environment variables                                                     #
    ####################################################################################

    # Path for the uv cache. This should not really be needed/used when also setting UV_NO_CACHE.
    # We'll set it anyway, just in case.
    export UV_CACHE_DIR="${temp_installation_dir}/uv/cache"

    # Where to install UV when using the installation script
    export UV_INSTALL_DIR="${temp_installation_dir}/uv/bin"

    # Path to where uv will install its python distributions when using uv python install.
    export UV_PYTHON_INSTALL_DIR="${temp_installation_dir}/uv/python"

    # Don't use a cache when installing packages. We use this temporarily to not pollute our transient
    # installation even more
    export UV_NO_CACHE=1

    # Don't adjust bash profiles, bashrc or the PATH environment variable.
    export UV_UNMANAGED_INSTALL=1
    export UV_NO_MODIFY_PATH=1
    export INSTALLER_NO_MODIFY_PATH=1

    message_info "The environment for installing UV has been set:"
    message_info "${BOLD}UV_CACHE_DIR${NC}=${UV_CACHE_DIR}"
    message_info "${BOLD}UV_INSTALL_DIR${NC}=${UV_INSTALL_DIR}"
    message_info "${BOLD}UV_PYTHON_INSTALL_DIR${NC}=${UV_PYTHON_INSTALL_DIR}"
    message_info "${BOLD}UV_NO_CACHE${NC}=${UV_NO_CACHE}"
    message_info "${BOLD}UV_UNMANAGED_INSTALL${NC}=${UV_UNMANAGED_INSTALL}"
    message_info "${BOLD}UV_NO_MODIFY_PATH${NC}=${UV_NO_MODIFY_PATH}"
    message_info "${BOLD}INSTALLER_NO_MODIFY_PATH${NC}=${INSTALLER_NO_MODIFY_PATH}"

    ####################################################################################
    # Install UV                                                                       #
    ####################################################################################
    message_info "Installing UV"
    cd "${temp_installation_dir}"
    mkdir -p uv/python
    mkdir -p uv/bin
    curl -LsSf https://astral.sh/uv/install.sh | execute_and_suppress_output sh
    message_success "UV has been installed."

    ####################################################################################
    # Create venv and install required packages                                        #
    ####################################################################################
    message_info "Creating virtual environment for connect in final installation directory."
    # Create the final installation folder.
    mkdir -p "${installation_dir}"
    # Create initial connect venv which we'll use for any further actions
    execute_and_suppress_output ./uv/bin/uv venv "${installation_dir}/.venv" --python 3.11
    message_success "Virtual Environment has been created."

    message_info "Installing required packages and connect into the virtual environment."
    message_warning "This can take a while. Please don't interrupt the process or close the window."

    cd "${installation_dir}"
    . .venv/bin/activate
    execute_and_suppress_output "${temp_installation_dir}/uv/bin/uv" pip install uv
    # uv will now be automatically picked from the .venv subfolder
    execute_and_suppress_output uv pip install poetry
    message_success "Installation of required packages and connect has been completed."

    # Delete the temporary installation folder
    # This MUST run last, otherwise uv won't automatically recognize the .venv anymore.
    # This can be worked around by explicitly activating the venv again after the rm command.
    rm -r "${temp_installation_dir}"
    message_info "Temp Directory ${temp_installation_dir} has been removed."

    message_info "To run connect, activate the virtual environment:"
    message_info "source ${installation_dir}/.venv/bin/activate"
    message_info "Now you can run connect from the commandline."
}

current_working_directory="${PWD}"

install_connect "$@" || exit 1

cd "${current_working_directory}"
