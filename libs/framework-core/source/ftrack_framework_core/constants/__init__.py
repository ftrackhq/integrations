# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

# TODO: re-check that all the constants in here are used. Remove the unused ones.

#: Default ui type for ftrack_framework_core
UI_TYPE = None
#: Default host type for ftrack_framework_core
HOST_TYPE = 'python'

# Valid Categories
#: Step Category.
STEP = 'step'
#: Stage Category.
STAGE = 'stage'
#: Plugin Category.
PLUGIN = 'plugin'

CATEGORIES = [STEP, STAGE, PLUGIN]

# Common steps.
#: Contexts step group.
CONTEXTS = 'contexts'
#: Finalizers step group.
FINALIZERS = 'finalizers'
#: Components step group.
COMPONENTS = 'components'

STEP_GROUPS = [CONTEXTS, COMPONENTS, FINALIZERS]

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

# Common definition/client types.
SCHEMA = 'schema'
#: Opener client and its definition.
OPENER = 'opener'
#: Loader client and its definition used with assembler
LOADER = 'loader'
#: Publisher client and its definition.
PUBLISHER = 'publisher'
# Asset manager
ASSET_MANAGER = 'asset_manager'
# Resolver
RESOLVER = 'resolver'
# Log viewer dialog
LOG_VIEWER = 'log_viewer'

DEFINITION_TYPES = [OPENER, LOADER, PUBLISHER, ASSET_MANAGER, RESOLVER]

# Misc
SNAPSHOT_COMPONENT_NAME = 'snapshot'
FTRACKREVIEW_COMPONENT_NAME = 'ftrackreview'

# Avoid circular dependencies.
from ftrack_framework_core.constants.plugin.load import *
from ftrack_framework_core.constants.plugin.open import *
from ftrack_framework_core.constants.plugin.publish import *
from ftrack_framework_core.constants.plugin.asset_manager import *
from ftrack_framework_core.constants.plugin.resolver import *
from ftrack_framework_core.constants.event import *
from ftrack_framework_core.constants.status import *
