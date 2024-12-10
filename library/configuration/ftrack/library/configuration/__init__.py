# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

# TODO:
#  - discover all the configuration files in the namespace
#  - load and merge configuration files based on basic yaml rules
#  - inject builtin/runtime configuration values (username, hostname, python_version etc.)
#  - apply value interpolation using omegaconf
#  - provide functionality to inject named regex groups as configuration values via a special resolver (maybe a namespaced one)
#     e.g. {regex:maya.launch.executable.version} OR simply {regex:version}

from .configuration import *
