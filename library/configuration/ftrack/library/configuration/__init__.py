# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

# TODO: Change logic to use the generated or provided metadata as the source for further processing

# TODO:
#  - implement schema so we can identify if something is a path and format it accordingly
#  - (OPTIONAL) provide functionality to inject named regex groups as configuration values via a special resolver (maybe a namespaced one)
#     e.g. {regex:maya.launch.executable.version} OR simply {regex:version}

from .configuration import Configuration as Configuration
