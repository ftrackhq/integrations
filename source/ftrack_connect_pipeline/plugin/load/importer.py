# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base


class LoaderImporterPlugin(base.BaseImporterPlugin):
    ''' Class representing an Loader Import Plugin
    .. note::

        _required_output a Dictionary
    '''
    return_type = dict
    plugin_type = constants.PLUGIN_LOADER_IMPORTER_TYPE
    _required_output = {}

    load_modes = {}

    def __init__(self, session):
        '''Initialise LoaderImporterPlugin with *session*

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(LoaderImporterPlugin, self).__init__(session)
