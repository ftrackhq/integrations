# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin, BasePluginValidation


class FinaliserPluginValidation(BasePluginValidation):
    '''Finaliser Plugin Validation class'''

    def __init__(self, plugin_name, required_output, return_type, return_value):
        '''Initialise FinaliserPluginValidation with *plugin_name*, *required_output*,
        *return_type*, *return_value*.

        *plugin_name* current plugin name stored at the plugin base class

        *required_output* required output of the current plugin stored at
        _required_output of the plugin base class

        *return_type* return type of the current plugin stored at the plugin
        base class

        *return_value* return value of the current plugin stored at the
        plugin base class
        '''
        super(FinaliserPluginValidation, self).__init__(plugin_name,
                                                        required_output,
                                                        return_type,
                                                        return_value)

class FinaliserPlugin(BasePlugin):
    ''' Class representing a Finaliser Plugin

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''
    return_type = dict
    plugin_type = constants.PLUGIN_FINALISER_TYPE
    _required_output = {'context_id': None, 'asset_name': None,
                        'asset_type': None, 'comment': None, 'status_id': None}

    def __init__(self, session):
        '''Initialise FinaliserPlugin with *session*

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(FinaliserPlugin, self).__init__(session)
        self.validator = FinaliserPluginValidation(self.plugin_name,
                                                  self._required_output,
                                                  self.return_type,
                                                  self.return_value)

    def run(self, context=None, data=None, options=None):
        '''Run the current plugin with , *context* , *data* and *options*.

        *context* provides a mapping with the asset_name, context_id, asset_type,
        comment and status_id of the asset that we are working on.

        *data* a list of data coming from outputs.

        *options* a dictionary of options passed from outside.

        Returns self.output a Dictionary with ontext_id, asset_name, asset_type,
        comment, status_id.

        .. note::

            Use always self.output as a base to return the values,
            don't override self.output as it contains the _required_output
        '''

        raise NotImplementedError('Missing run method.')