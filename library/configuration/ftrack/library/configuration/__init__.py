# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

# TODO: separate process into three distinct steps:
#  - metadata creation
#  - composition of config files
#  - resolution of configuration
# TODO: Change logic to use the generated or provided metadata as the source for further processing
# TODO: Remove delete-after-compose from the final configuration
# TODO: Provide functionality to decide how to deal with conflicts

# TODO:
#  - keys to be deleted should be deleted and moved by a separate function
#  - implement optional ordering mechanism:
#    - the ordering.yaml file can be created automatically
#    - ordering will only be required if an actual confict is discovered
#    - for sorting the configurations, we would like to allow each package to set its internal order and then order on the package level
#  - implement schema so we can identify if something is a path and format it accordingly
#  - (OPTIONAL) provide functionality to inject named regex groups as configuration values via a special resolver (maybe a namespaced one)
#     e.g. {regex:maya.launch.executable.version} OR simply {regex:version}

from .configuration import Configuration as Configuration
