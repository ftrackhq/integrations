# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base


class PublisherValidatorPlugin(base.BaseValidatorPlugin):
    '''
    Base Publisher Validator Plugin Class inherits from
    :class:`~ftrack_connect_pipeline.plugin.base.BaseValidatorPlugin`
    '''
    return_type = bool
    '''Required return type'''
    plugin_type = constants.PLUGIN_PUBLISHER_VALIDATOR_TYPE
    '''Type of the plugin'''
    _required_output = False
    '''Required return output'''

    def __init__(self, session):
        super(PublisherValidatorPlugin, self).__init__(session)
