# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack


class LogItem(object):
    '''Represents a Logging Item Base Class'''

    def __init__(self, log_result):
        '''
        Initialise LogItem with *log_result*

        *log_result*: Dictionary with log information.
        '''
        self.date = log_result.get('date')
        self.host_id = log_result.get('host_id')

        self.name = log_result.get('name')
        self.reference = log_result.get('reference')
        self.boolean_status = log_result.get('boolean_status')
        self.status = log_result.get('status')
        self.message = log_result.get('message')
        self.execution_time = log_result.get('execution_time')
        self.options = log_result.get('options')
        # Revisit this if store goes to big
        self.store = log_result.get('store')

    # TODO: remove this properties if not needed.
    @property
    def execution_time(self):
        '''Return the duration of the log entry.'''
        return round(self._execution_time, 4)

    @execution_time.setter
    def execution_time(self, value):
        '''Set the duration of the log entry.'''
        self._execution_time = value
