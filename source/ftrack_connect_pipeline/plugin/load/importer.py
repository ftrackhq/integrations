# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base


class LoaderImporterPlugin(base.BaseImporterPlugin):
    '''
    Base Loader Importer Plugin Class inherits from
    :class:`~ftrack_connect_pipeline.plugin.base.BaseImporterPlugin`
    '''
    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_LOADER_IMPORTER_TYPE
    '''Type of the plugin'''
    _required_output = {}
    '''Required return output'''

    load_modes = {}
    '''Available load modes for an asset'''

    def __init__(self, session):
        super(LoaderImporterPlugin, self).__init__(session)
