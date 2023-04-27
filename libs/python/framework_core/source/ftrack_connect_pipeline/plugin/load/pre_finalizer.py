# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base


class LoaderPreFinalizerPlugin(base.BasePreFinalizerPlugin):
    '''
    Base Loader Pre Finalizer Plugin Class inherits from
    :class:`~ftrack_connect_pipeline.plugin.base.BasePreFinalizerPlugin`
    '''

    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_LOADER_PRE_FINALIZER_TYPE
    '''Type of the plugin'''
    _required_output = {}
    '''Required return exporters'''

    def __init__(self, session):
        super(LoaderPreFinalizerPlugin, self).__init__(session)
