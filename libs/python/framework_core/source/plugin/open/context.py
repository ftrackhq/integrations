# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from framework_core import constants
from framework_core.plugin import base


class OpenerContextPlugin(base.BaseContextPlugin):
    '''
    Base Opener Context Plugin Class inherits from
    :class:`~framework_core.plugin.base.BaseContextPlugin`
    '''

    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_OPENER_CONTEXT_TYPE
    '''Type of the plugin'''
    _required_output = {
        'context_id': None,
        'asset_name': None,
        'comment': None,
        'status_id': None,
    }
    '''Required return exporters'''

    def __init__(self, session):
        super(OpenerContextPlugin, self).__init__(session)
