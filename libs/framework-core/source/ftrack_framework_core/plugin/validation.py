# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

# TODO: rename this to PluginResultValidation
class BasePluginValidation(object):
    '''Plugin Validation base class'''

    def __init__(
        self, plugin_name, required_output, return_type, return_value
    ):
        '''
        Initialise PluginValidation with *plugin_name*, *required_output*,
        *return_type*, *return_value*.

        *plugin_name* : current plugin name.

        *required_output* : required exporters of the current plugin.

        *return_type* : required return type of the current plugin.

        *return_value* : Expected return value of the current plugin.
        '''
        super(BasePluginValidation, self).__init__()
        self.plugin_name = plugin_name
        self.required_output = required_output
        self.return_type = return_type
        self.return_value = return_value

    def validate_required_output(self, result):
        '''
        Ensures that *result* contains all the expected :obj:`required_output`
        keys defined for the current plugin.

        *result* : exporters value of the plugin execution.

        Return tuple (bool,str)
        '''
        validator_result = (True, "")

        for output_key in list(self.required_output.keys()):
            if output_key not in list(result.keys()):
                message = '{} require {} result option'.format(
                    self.plugin_name, output_key
                )
                validator_result = (False, message)

        return validator_result

    def validate_result_type(self, result):
        '''
        Ensures that *result* is instance of the defined :obj:`return_type` of
        the current plugin.

        *result* : exporters value of the plugin execution.

        Return tuple (bool,str)
        '''
        validator_result = (True, "")

        if self.return_type is not None:
            if not isinstance(result, self.return_type):
                message = (
                    'Return value of {} is of type {}, should be {} '
                    'type'.format(
                        self.plugin_name, type(result), self.return_type
                    )
                )

                validator_result = (False, message)

        return validator_result

    def validate_result_value(self, result):
        '''Ensures that *result* is equal as the defined :obj:`return_value` of
        the current plugin.

        *result* : exporters value of the plugin execution.

        Return tuple (bool,str)
        '''
        validator_result = (True, "")

        return validator_result

    def validate_user_data(self, user_data):
        '''
        Ensures that *user_data* is instance of :obj:`dict`. And validates that
        contains message and data keys.

        Return tuple (bool,str)
        '''
        validator_result = (True, "")

        if user_data is not None:
            if not isinstance(user_data, dict):
                message = (
                    'user_data value should be of type {} and it\'s '
                    'type of {}'.format(type(dict), type(user_data))
                )
                validator_result = (False, message)
            else:
                if not 'message' in list(user_data.keys()):
                    user_data['message'] = ''
                if not 'data' in list(user_data.keys()):
                    user_data['data'] = {}
                for key in list(user_data.keys()):
                    if not key in ['message', 'data']:
                        validator_result = (
                            False,
                            'user_data can only contain they keys "message" '
                            'and/or "data"',
                        )
                        break
        return validator_result