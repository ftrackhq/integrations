# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.plugin import BasePlugin, BasePluginValidation
from ftrack_connect_pipeline.constants import plugin


class ActionPluginValidation(BasePluginValidation):
    '''
    Action Plugin Validation class inherits from
    :class:`~ftrack_connect_pipeline.plugin.BasePluginValidation`
    '''

    def __init__(self, plugin_name, required_output, return_type, return_value):
        super(ActionPluginValidation, self).__init__(
            plugin_name, required_output, return_type, return_value)

    def validate_required_output(self, result):
        '''
        Ensures that *result* contains all the expected :obj:`required_output`
        values defined for the current plugin.

        *result* : output value of the plugin execution.

        Return tuple (bool,str)
        '''
        validator_result = (True, "")

        for output_value in self.required_output:
            if output_value not in result:
                message = '{} require {} result option'.format(
                    self.plugin_name, output_value
                )
                validator_result = (False, message)

        return validator_result


class BaseActionPlugin(BasePlugin):
    '''
    Base Action Plugin Class inherits from
    :class:`~ftrack_connect_pipeline.plugin.BasePlugin`
    '''
    return_type = list
    '''Required return type'''
    plugin_type = plugin._PLUGIN_ACTION_TYPE
    '''Type of the plugin'''
    _required_output = []
    '''Required return output'''

    def __init__(self, session):
        super(BaseActionPlugin, self).__init__(session)
        self.validator = ActionPluginValidation(
            self.plugin_name, self._required_output, self.return_type,
            self.return_value)

    def run(self, context_data=None, data=None, options=None):
        raise NotImplementedError('Missing run method.')
