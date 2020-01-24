# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_qt.plugin import BasePluginWidget


class ContextWidget(BasePluginWidget):
    ''' Class representing a Context Widget
    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'comment' and 'status_id' of the current asset
    '''
    plugin_type = constants.PLUGIN_CONTEXT_TYPE


