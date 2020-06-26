# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_qt.plugin import base


class LoaderImporterWidget(base.BaseImporterWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
    plugin_type = constants.PLUGIN_LOADER_IMPORTER_TYPE

