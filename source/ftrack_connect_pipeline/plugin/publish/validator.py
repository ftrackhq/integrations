# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base

class PublisherValidatorPlugin(base.BaseValidatorPlugin):
    ''' Class representing a Validator Plugin

    .. note::

        _required_output a Boolean '''
    return_type = bool
    plugin_type = constants.PLUGIN_PUBLISHER_VALIDATOR_TYPE
    _required_output = False

    def __init__(self, session):
        '''Initialise ValidatorPlugin with *session*

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(PublisherValidatorPlugin, self).__init__(session)
