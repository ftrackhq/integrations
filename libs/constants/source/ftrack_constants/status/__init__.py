# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

#: Unknown status execution.
UNKNOWN_STATUS = 'UNKNOWN_STATUS'
#: Success status execution.
SUCCESS_STATUS = 'SUCCESS_STATUS'
#: Warning status - not critical
WARNING_STATUS = 'WARNING_STATUS'
#: Error status - user or systems error
ERROR_STATUS = 'ERROR_STATUS'
#: Exception status - internal code execution error or malfunction
EXCEPTION_STATUS = 'EXCEPTION_STATUS'
#: Running status
RUNNING_STATUS = 'RUNNING_STATUS'
#: Default status
DEFAULT_STATUS = 'PAUSE_STATUS'

STATUS_LIST = [
    UNKNOWN_STATUS,
    SUCCESS_STATUS,
    WARNING_STATUS,
    ERROR_STATUS,
    EXCEPTION_STATUS,
    RUNNING_STATUS,
    DEFAULT_STATUS,
]

#: Mapping of the run plugins status. Valid or non-valid result.
status_bool_mapping = {
    UNKNOWN_STATUS: False,
    SUCCESS_STATUS: True,
    WARNING_STATUS: False,
    ERROR_STATUS: False,
    EXCEPTION_STATUS: False,
    RUNNING_STATUS: True,
    DEFAULT_STATUS: False,
}

#: Mapping of the run plugins status. String representation.
STATUS_STRING_MAPPING = {
    UNKNOWN_STATUS: 'Not started',
    SUCCESS_STATUS: 'Success',
    WARNING_STATUS: 'Warning',
    ERROR_STATUS: 'ERROR',
    EXCEPTION_STATUS: 'EXCEPTION',
    RUNNING_STATUS: 'Running',
    DEFAULT_STATUS: 'Pause',
}
