# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_framework_core import constants
from ftrack_framework_core.plugin import base


# TODO: check required output is it used?
class PublisherContextPlugin(base.BaseContextPlugin):
    '''
    Base Publisher Context Plugin Class inherits from
    :class:`~ftrack_framework_core.plugin.base.BaseContextPlugin`
    '''

    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_PUBLISHER_CONTEXT_TYPE
    '''Type of the plugin'''
    _required_output = {
        'context_id': None,
        'asset_name': None,
        'comment': None,
        'status_id': None,
    }
    '''Required return exporters'''

    def __init__(self, session):
        super(PublisherContextPlugin, self).__init__(session)
