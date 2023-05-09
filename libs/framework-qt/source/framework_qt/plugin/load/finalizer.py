# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from framework_core import constants as core_constants
from framework_qt.plugin import base


class LoaderFinalizerPluginWidget(base.BaseFinalizerPluginWidget):
    plugin_type = core_constants.PLUGIN_LOADER_FINALIZER_TYPE
