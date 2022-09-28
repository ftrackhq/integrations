# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from {{cookiecutter.package_name}}.utils import custom_commands as {{cookiecutter.host_type}}_utils

# Load Modes
IMPORT_MODE = 'import'
REFERENCE_MODE = 'reference'
OPEN_MODE = 'open'

LOAD_MODES = {
    OPEN_MODE: {{cookiecutter.host_type}}_utils.open_file,
    IMPORT_MODE: {{cookiecutter.host_type}}_utils.import_file,
    REFERENCE_MODE: {{cookiecutter.host_type}}_utils.reference_file,
}
