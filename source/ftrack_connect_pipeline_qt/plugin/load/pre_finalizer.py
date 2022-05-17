# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline_qt.plugin import base


class LoaderPreFinalizerPluginWidget(base.BasePreFinalizerPluginWidget):
    plugin_type = core_constants.PLUGIN_LOADER_PRE_FINALIZER_TYPE
