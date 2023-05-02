# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.plugin import BasePlugin, BasePluginValidation
from ftrack_connect_pipeline.constants import plugin


class BaseValidatorPluginValidation(BasePluginValidation):
    '''
    Validator Plugin Validation class inherits from
    :class:`~ftrack_connect_pipeline.plugin.BasePluginValidation`
    '''

    def __init__(
        self, plugin_name, required_output, return_type, return_value
    ):
        super(BaseValidatorPluginValidation, self).__init__(
            plugin_name, required_output, return_type, return_value
        )

    def validate_required_output(self, result):
        '''
        Ensures that *result* contains all the expected :obj:`required_output`
        values defined for the current plugin.

        *result* : exporters value of the plugin execution.

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
        '''Ensures that *result* is True.

        *result* : exporters value of the plugin execution.

        Return tuple (bool,str)
        '''
        validator_result = (True, "")

        if result is not True:
            message = 'Return value of {} is not {}'.format(
                self.plugin_name, self.return_value
            )
            validator_result = (False, message)

        return validator_result


class BaseValidatorPlugin(BasePlugin):
    '''
    Base Validator Plugin Class inherits from
    :class:`~ftrack_connect_pipeline.plugin.BasePlugin`
    '''

    return_type = bool
    '''Required return type'''
    plugin_type = plugin._PLUGIN_VALIDATOR_TYPE
    '''Type of the plugin'''
    _required_output = False
    '''Required return exporters'''
    return_value = True
    '''Required return Value'''

    def __init__(self, session):
        super(BaseValidatorPlugin, self).__init__(session)
        self.validator = BaseValidatorPluginValidation(
            self.plugin_name,
            self._required_output,
            self.return_type,
            self.return_value,
        )

    def run(self, context_data=None, data=None, options=None):
        raise NotImplementedError('Missing run method.')
