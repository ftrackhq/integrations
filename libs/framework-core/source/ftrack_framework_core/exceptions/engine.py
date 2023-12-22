# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack


class EngineExecutionError(Exception):
    """
    Exception raised when there is an error during engine execution.
    """

    def __init__(self, message):
        super(EngineExecutionError, self).__init__(message)
