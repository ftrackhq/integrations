# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_framework_core import constants as core_constants
from ftrack_framework_qt.plugin import base


class LoaderPostFinalizerPluginWidget(base.BasePostFinalizerPluginWidget):
    plugin_type = core_constants.PLUGIN_LOADER_POST_FINALIZER_TYPE
