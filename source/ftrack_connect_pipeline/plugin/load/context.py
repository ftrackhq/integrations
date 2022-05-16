# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base


class LoaderContextPlugin(base.BaseContextPlugin):
    '''
    Base Loader Context Plugin Class inherits from
    :class:`~ftrack_connect_pipeline.plugin.base.BaseContextPlugin`
    '''

    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_LOADER_CONTEXT_TYPE
    '''Type of the plugin'''
    _required_output = {
        'context_id': None,
        'asset_name': None,
        'comment': None,
        'status_id': None,
    }
    '''Required return exporters'''

    def __init__(self, session):
        super(LoaderContextPlugin, self).__init__(session)
