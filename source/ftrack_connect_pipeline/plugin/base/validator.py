# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.plugin import BasePlugin, BasePluginValidation
from ftrack_connect_pipeline.constants import plugin


class ValidatorPluginValidation(BasePluginValidation):
    ''' Validator Plugin Validation class'''

    def __init__(self, plugin_name, required_output, return_type, return_value):
        '''Initialise ValidatorPluginValidation with *plugin_name*,
        *required_output*, *return_type*, *return_value*.

        *plugin_name* current plugin name stored at the plugin base class

        *required_output* required output of the current plugin stored at
        _required_output of the plugin base class

        *return_type* return type of the current plugin stored at the plugin
        base class

        *return_value* return value of the current plugin stored at the
        plugin base class
        '''
        super(ValidatorPluginValidation, self).__init__(
            plugin_name, required_output, return_type, return_value
        )

    def validate_required_output(self, result):
        '''Ensures that *result* contains the expected required_output
        defined for the current plugin.

        *result* output value of the plugin execution

        Return tuple (bool,str)
        '''
        validator_result = (True, "")
        if type(result) != type(self.required_output):
            message = '{} require {} result option type'.format(
                self.plugin_name, type(self.required_output)
            )
            validator_result = (False, message)

        return validator_result

    def validate_result_value(self, result):
        '''Ensures that *result* is equal as the defined return_value of
        the current plugin.

        *result* output value of the plugin execution

        Return tuple (bool,str)
        '''
        validator_result = (True, "")

        if result is not True:
            message = 'Return value of {} is not {}'.format(
                self.__class__.__name__, self.return_value
            )
            validator_result = (False, message)

        return validator_result


class BaseValidatorPlugin(BasePlugin):
    ''' Class representing a Validator Plugin

    .. note::

        _required_output a Boolean
    '''
    return_type = bool
    plugin_type = plugin._PLUGIN_VALIDATOR_TYPE
    _required_output = False

    def __init__(self, session):
        '''Initialise ValidatorPlugin with *session*

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(BaseValidatorPlugin, self).__init__(session)
        self.validator = ValidatorPluginValidation(
            self.plugin_name, self._required_output,
            self.return_type, self.return_value
        )

    def run(self, context=None, data=None, options=None):
        '''Run the current plugin with , *context* , *data* and *options*.

        *context* provides a mapping with the asset_name, context_id,
        asset_type, comment and status_id of the asset that we are working on.

        *data* a list of data coming from previous collector or empty list

        *options* a dictionary of options passed from outside.

        Returns self.output Boolean value

        .. note::

            Use always self.output as a base to return the values.
        '''

        raise NotImplementedError('Missing run method.')