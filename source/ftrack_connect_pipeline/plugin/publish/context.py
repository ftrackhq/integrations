# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base


class PublisherContextPlugin(base.BaseContextPlugin):
    ''' Class representing a Context Plugin
    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'comment' and 'status_id' of the current asset
    '''
    return_type = dict
    plugin_type = constants.PLUGIN_PUBLISHER_CONTEXT_TYPE
    _required_output = {'context_id': None, 'asset_name': None,
                        'comment': None, 'status_id': None}

    def __init__(self, session):
        '''Initialise ContextPlugin with *session*

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(PublisherContextPlugin, self).__init__(session)
