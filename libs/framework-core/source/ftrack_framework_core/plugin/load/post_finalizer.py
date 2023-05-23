# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_framework_core import constants
from ftrack_framework_core.plugin import base


class LoaderPostFinalizerPlugin(base.BasePostFinalizerPlugin):
    '''
    Base Loader Post Finalizer Plugin Class inherits from
    :class:`~ftrack_framework_core.plugin.base.BasePostFinalizerPlugin`
    '''

    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_LOADER_POST_FINALIZER_TYPE
    '''Type of the plugin'''
    _required_output = {}
    '''Required return exporters'''

    def __init__(self, session):
        super(LoaderPostFinalizerPlugin, self).__init__(session)
