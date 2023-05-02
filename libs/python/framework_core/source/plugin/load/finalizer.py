# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from framework_core import constants
from framework_core.plugin import base


class LoaderFinalizerPlugin(base.BaseFinalizerPlugin):
    '''
    Base Loader Finalizer Plugin Class inherits from
    :class:`~framework_core.plugin.base.BaseFinalizerPlugin`
    '''

    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_LOADER_FINALIZER_TYPE
    '''Type of the plugin'''
    _required_output = {}
    '''Required return exporters'''

    def __init__(self, session):
        super(LoaderFinalizerPlugin, self).__init__(session)
