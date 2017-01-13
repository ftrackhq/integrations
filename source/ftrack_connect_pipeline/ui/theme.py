# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from QtExt import QtGui, QtCore, QtWidgets


def applyFont(font=':/ftrack/font/main'):
    '''Add application font.'''
    QtGui.QFontDatabase.addApplicationFont(font)


def applyTheme(widget, theme='light', baseTheme=None):
    '''Apply *theme* to *widget*.'''
    # Set base style.

    if baseTheme and QtWidgets.QApplication.style().objectName() != baseTheme:
        QtWidgets.QApplication.setStyle(baseTheme)

    # Load stylesheet from resource file and apply.
    fileObject = QtCore.QFile(':/ftrack/style/{0}'.format(theme))
    fileObject.open(
        QtCore.QFile.ReadOnly | QtCore.QFile.Text
    )
    stream = QtCore.QTextStream(fileObject)
    styleSheetContent = stream.readAll()

    widget.setStyleSheet(styleSheetContent)
