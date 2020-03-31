# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_qt.plugin import BasePluginWidget


class ImporterWidget(BasePluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List '''
    plugin_type = constants.PLUGIN_IMPORTER_TYPE

