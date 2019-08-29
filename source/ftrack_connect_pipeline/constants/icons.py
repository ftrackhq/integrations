# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from qtpy import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline.constants.status import (
    UNKNOWN_STATUS, DEFAULT_STATUS, ERROR_STATUS, WARNING_STATUS, EXCEPTION_STATUS, RUNNING_STATUS, SUCCESS_STATUS
)

# UNKNOWN
_unknown_icon = QtWidgets.QApplication.style().standardIcon(
    QtWidgets.QStyle.SP_TitleBarContextHelpButton
).pixmap(QtCore.QSize(16, 16))

# RUNNING
_running_icon = QtWidgets.QApplication.style().standardIcon(
    QtWidgets.QStyle.SP_BrowserReload
).pixmap(QtCore.QSize(16, 16))

# SUCCESS
_success_icon = QtWidgets.QApplication.style().standardIcon(
    QtWidgets.QStyle.SP_DialogApplyButton
).pixmap(QtCore.QSize(16, 16))

# ERROR
_error_icon = QtWidgets.QApplication.style().standardIcon(
    QtWidgets.QStyle.SP_BrowserStop
).pixmap(QtCore.QSize(16, 16))

# EXCEPTION
_exception_icon = QtWidgets.QApplication.style().standardIcon(
    QtWidgets.QStyle.SP_MessageBoxCritical
).pixmap(QtCore.QSize(16, 16))

# WARNING
_warning_icon = QtWidgets.QApplication.style().standardIcon(
    QtWidgets.QStyle.SP_MessageBoxWarning
).pixmap(QtCore.QSize(16, 16))

# DEFAULT
_default_icon = QtWidgets.QApplication.style().standardIcon(
    QtWidgets.QStyle.SP_MediaPause
).pixmap(QtCore.QSize(16, 16))

status_icons = {
    UNKNOWN_STATUS: _unknown_icon,
    DEFAULT_STATUS: _default_icon,
    ERROR_STATUS: _error_icon,
    WARNING_STATUS: _warning_icon,
    EXCEPTION_STATUS: _exception_icon,
    RUNNING_STATUS: _running_icon,
    SUCCESS_STATUS: _success_icon,
}
