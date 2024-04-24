# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import sys
import traceback
from io import StringIO
import logging

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore


class UncaughtError(QtWidgets.QMessageBox):
    '''Widget that handles uncaught errors and presents a message box.'''

    onError = QtCore.Signal(object, object, object)

    def __init__(self, parent=None):
        '''Initialise and setup widget.'''
        super(UncaughtError, self).__init__(
            QtWidgets.QMessageBox.Icon.Critical, '', ''
        )
        self.setParent(parent)
        self.onError.connect(self.exceptHook)

        # Listen to all unhandled exceptions.
        sys.excepthook = self.onError.emit

    def getTraceback(self, exceptionTraceback):
        '''Return message from *exceptionTraceback*.'''
        tracebackInfoStream = StringIO()
        traceback.print_tb(exceptionTraceback, None, tracebackInfoStream)
        tracebackInfoStream.seek(0)
        return tracebackInfoStream.read()

    def exceptHook(self, exceptionType, exceptionValue, exceptionTraceback):
        '''Show message box with error details.'''

        logging.error(
            'Logging an uncaught exception',
            exc_info=(exceptionType, exceptionValue, exceptionTraceback),
        )

        # Show exception to user.
        tracebackInfo = self.getTraceback(exceptionTraceback)
        self.setDetailedText(tracebackInfo)

        # Make sure text is at least a certain length to force message box size.
        # Otherwise buttons will not fit.
        self.setText(str(exceptionValue).ljust(50, ' '))
        self.exec_()
