# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

# Valid Categories
#: Step Category.
STEP = 'step'
#: Stage Category.
STAGE = 'stage'
#: Plugin Category.
PLUGIN = 'plugin'

# Common steps.
#: Contexts step group.
CONTEXTS = 'contexts'
#: Finalizers step group.
FINALIZERS = 'finalizers'
#: Components step group.
COMPONENTS = 'components'

# Common steps types.
#: Contexts step type.
CONTEXT = 'context'
#: Finalizers step type.
FINALIZER = 'finalizer'
#: Components step type.
COMPONENT = 'component'

# Component stages.
#: Collector component stage name.
COLLECTOR = 'collector'
#: Validator component stage name.
VALIDATOR = 'validator'
#: Output component stage name.
EXPORTER = 'exporter'
#: Importer component stage name.
IMPORTER = 'importer'
#: Post_import component stage name.
POST_IMPORTER = 'post_importer'

# Common tool_config types.
SCHEMA = 'schema'
#: Opener client and its tool_config.
OPENER = 'opener'
#: Loader client and its tool_config used with assembler
LOADER = 'loader'
#: Publisher client and its tool_config.
PUBLISHER = 'publisher'
# Asset manager
ASSET_MANAGER = 'asset_manager'
# Resolver
RESOLVER = 'resolver'
# Log viewer dialog
LOG_VIEWER = 'log_viewer'
