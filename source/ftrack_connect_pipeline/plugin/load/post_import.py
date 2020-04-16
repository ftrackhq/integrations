# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base


class LoaderPostImportPlugin(base.BasePostImportPlugin):
    ''' Class representing an Loader Post Import Plugin
    .. note::

        _required_output a Dictionary
    '''
    return_type = dict
    plugin_type = constants.PLUGIN_LOADER_POST_IMPORT_TYPE
    _required_output = {}

    def __init__(self, session):
        '''Initialise LoaderPostImportPlugin with *session*

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(LoaderPostImportPlugin, self).__init__(session)
