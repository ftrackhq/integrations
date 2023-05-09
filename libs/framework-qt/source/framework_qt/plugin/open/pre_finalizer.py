# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from framework_core import constants as core_constants
from framework_qt.plugin import base


class OpenerPreFinalizerPluginWidget(base.BasePreFinalizerPluginWidget):
    plugin_type = core_constants.PLUGIN_OPENER_PRE_FINALIZER_TYPE
