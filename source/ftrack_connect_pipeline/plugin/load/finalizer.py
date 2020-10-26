# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base


class LoaderFinalizerPlugin(base.BaseFinalizerPlugin):
    ''' Class representing a Finalizer Plugin

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''
    return_type = dict
    plugin_type = constants.PLUGIN_LOADER_FINALIZER_TYPE
    _required_output = {}

    def __init__(self, session):
        '''Initialise FinalizerPlugin with *session*

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(LoaderFinalizerPlugin, self).__init__(session)
