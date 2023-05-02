# :copyright: Copyright (c) 2014-2020 ftrack

from framework_core import constants
from framework_core.plugin import base


class OpenerPreFinalizerPlugin(base.BasePreFinalizerPlugin):
    '''
    Base Opener Pre Finalizer Plugin Class inherits from
    :class:`~framework_core.plugin.base.BasePreFinalizerPlugin`
    '''

    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_OPENER_PRE_FINALIZER_TYPE
    '''Type of the plugin'''
    _required_output = {}
    '''Required return exporters'''

    def __init__(self, session):
        super(OpenerPreFinalizerPlugin, self).__init__(session)
