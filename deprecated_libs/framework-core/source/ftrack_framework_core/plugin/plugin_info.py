# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import ftrack_constants as constants


class PluginInfo:
    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        # Automatically update boolean status
        self.boolean_status = self.status_to_boolean(value)

    @staticmethod
    def status_to_boolean(status):
        # Implement the logic to convert status to a boolean value
        return constants.status.status_bool_mapping[status]

    def __init__(self, name, reference, options, store=None):
        '''
        Class to manage and store plugin execution information.

        This class handles the synchronization between the plugin's status
        and its boolean representation, and maintains other relevant information
        about the plugin's execution.

        *name*: Name of the plugin.
        *reference*: Reference identifier for the plugin.
        *options*: Options used for plugin execution.
        *store*: Optional store for plugin-related data.
        '''
        self.name = name
        self.reference = reference
        self.boolean_status = None
        self._status = None
        self.message = ''
        self.execution_time = 0
        self.options = options
        self.store = store
        # set default status
        self.status = constants.status.UNKNOWN_STATUS

    def to_dict(self):
        '''
        Returns a dictionary representation of the plugin information.
        Replaces the key '_plugin_status' with 'status'.
        '''
        return {
            'name': self.name,
            'reference': self.reference,
            'status': self._status,  # Use 'status' instead of '_status'
            'boolean_status': self.boolean_status,
            'message': self.message,
            'execution_time': self.execution_time,
            'options': self.options,
            'store': self.store,
        }
