# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging

logger = logging.getLogger('ftrack_framework_core.exceptions.plugin')


class PluginExecutionError(Exception):
    """
    Exception raised when there is an error during plugin execution.
    """

    def __init__(self, message):
        super(PluginExecutionError, self).__init__(message)


class PluginValidationError(Exception):
    """
    Exception raised when there is a validation error in the plugin.
    *on_fix_callback* method callback is accepted.
    """

    def __init__(self, message, on_fix_callback=None, fix_kwargs={}):
        super(PluginValidationError, self).__init__(message)
        self.on_fix_callback = on_fix_callback
        self.fix_kwargs = fix_kwargs

    def attempt_fix(self, store):
        """
        Attempt to fix the validation error.
        """
        if callable(self.on_fix_callback):
            try:
                self.on_fix_callback(store, **self.fix_kwargs)
                logger.debug("Fix applied successfully.")
            except Exception as e:
                raise Exception(
                    f"An error occurred while applying the fix: {e}"
                )
        else:
            raise Exception("No fix available.")


class PluginUIHookExecutionError(Exception):
    """
    Exception raised when there is an error during plugin UI hook execution.
    """

    def __init__(self, message):
        super(PluginUIHookExecutionError, self).__init__(message)
