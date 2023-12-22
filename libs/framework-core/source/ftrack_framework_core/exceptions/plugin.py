# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

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
    *on_fix_click* method callback is accepted.
    """

    def __init__(self, message, on_fix_click):
        super(PluginValidationError, self).__init__(message)
        self.on_fix_click = on_fix_click

    def attempt_fix(self):
        """
        Attempt to fix the validation error.
        """
        if callable(self.on_fix_click):
            try:
                self.on_fix_click()
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
