# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base

class LoaderFinaliserPlugin(base.BaseFinaliserPlugin):
    ''' Class representing a Finaliser Plugin

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''
    return_type = dict
    plugin_type = constants.PLUGIN_LOADER_FINALISER_TYPE
    _required_output = {}

    def __init__(self, session):
        '''Initialise FinaliserPlugin with *session*

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(LoaderFinaliserPlugin, self).__init__(session)
