
class PluginValidation(object):

    def __init__(self, plugin_name, input_options, output_options, return_type, return_value):
        super(PluginValidation, self).__init__()
        self.plugin_name = plugin_name
        self.input_options = input_options
        self.output_options = output_options
        self.return_type = return_type
        self.return_value = return_value

    def validate_input_options(self, settings):
        '''This function checks that the plugin settings contains all the expected input_options
            defined for the specific plugin type'''
        validator_result = (True, "")
        if settings.get('options'):
            for input_option in self.input_options:
                if input_option not in settings['options']:
                    message = '{} require {} input option'.format(
                        self.plugin_name, input_option
                    )
                    validator_result = (False, message)

        return validator_result


    def validate_result_options(self, result):
        '''This function checks that the plugin result contains all the expected output_options
        defined for the specific plugin type'''
        validator_result = (True, "")

        for output_option in self.output_options:

            if output_option not in result:
                message = '{} require {} result option'.format(
                    self.plugin_name, output_option
                )
                validator_result = (False, message)

        return validator_result

    def validate_result_type(self, result):
        '''This function checks that the plugin result is instance
        of the defined return_type for the specific plugin type'''
        validator_result = (True, "")

        if self.return_type is not None:
            if not isinstance(result, self.return_type):
                message = 'Return value of {} is of type {}, should {} type'.format(
                    self.plugin_name, type(result), self.return_type
                )
                validator_result = (False, message)

        return validator_result


    def validate_result_value(self, result):
        '''This function checks if plugin result is equal as the expected
        defined return_value for the specific plugin type'''
        validator_result = (True, "")

        if self.return_value is not None:

            if result != self.return_value:
                message = 'Return value of {} is not {}'.format(
                    self.__class__.__name__, self.return_value
                )
                validator_result = (False, message)

        return validator_result


