# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

#: Unknown status of plugin execution.
UNKNOWN_STATUS = 'UNKNOWN_STATUS'
#: Succed status of plugin execution.
SUCCESS_STATUS = 'SUCCESS_STATUS'
#: Warning status of plugin execution.
WARNING_STATUS = 'WARNING_STATUS'
#: Error status of plugin execution.
ERROR_STATUS = 'ERROR_STATUS'
#: Exception status of plugin execution.
EXCEPTION_STATUS = 'EXCEPTION_STATUS'
#: Running status of plugin execution.
RUNNING_STATUS = 'RUNNING_STATUS'
#: Default status of plugin execution.
DEFAULT_STATUS = 'PAUSE_STATUS'

#: Mapping of the run plugins status. Valid or non-valid result.
status_bool_mapping = {
    UNKNOWN_STATUS: False,
    SUCCESS_STATUS: True,
    WARNING_STATUS: False,
    ERROR_STATUS: False,
    EXCEPTION_STATUS: False,
    RUNNING_STATUS: False,
    DEFAULT_STATUS: False,
}
