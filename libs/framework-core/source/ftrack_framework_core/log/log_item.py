# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack


class LogItem(object):
    '''Represents a Logging Item Base Class'''

    def __init__(self, log_result):
        '''
        Initialise LogItem with *log_result*

        *log_result*: Dictionary with log information.
        '''
        self.date = log_result.get('date')

        #self.widget_ref = log_result.get('widget_ref')
        self.host_id = log_result.get('host_id')
        self.plugin_name = log_result.get('plugin_name')
        self.plugin_type = log_result.get('plugin_type')
        self.plugin_id = log_result.get('plugin_id')
        self.host_type = log_result.get('host_type')
        self.plugin_status = log_result.get('plugin_status')
        self.plugin_boolean_status = log_result.get('plugin_boolean_status')
        self.plugin_method_result = log_result.get('plugin_method_result')
        self.plugin_result_registry = log_result.get('plugin_result_registry')
        self.plugin_execution_time = log_result.get('plugin_execution_time')
        self.plugin_message = log_result.get('plugin_message')
        self.plugin_context_data = log_result.get('plugin_context_data')
        self.plugin_data = log_result.get('plugin_data')
        self.plugin_options = log_result.get('plugin_options')


    @property
    def execution_time(self):
        '''Return the duration of the log entry.'''
        return round(self._execution_time, 4)

    @execution_time.setter
    def execution_time(self, value):
        '''Set the duration of the log entry.'''
        self._execution_time = value
