# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

class LogItem(object):
    '''Represents a Logging Item Base Class'''

    def __init__(self, log_result):
        '''
        Initialise LogItem with *log_result*

        *log_result*: Dicctionary with log information.
        '''

        self.status = log_result.get('status')
        self.widget_ref = log_result.get('widget_ref')
        self.host_id = log_result.get('host_id')
        self.execution_time = log_result.get('execution_time')
        self.plugin_name = log_result.get('plugin_name')
        self.result = log_result.get('result')
        self.message = log_result.get('message')
        self.plugin_type = log_result.get('plugin_type')

    @property
    def execution_time(self):
        '''Return the duration of the log entry.'''
        return round(self._execution_time, 4)

    @execution_time.setter
    def execution_time(self, value):
        '''Set the duration of the log entry.'''
        self._execution_time = value