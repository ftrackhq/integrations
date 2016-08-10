# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from PySide import QtGui, QtCore


def applyFont(font=':/ftrack/font/main'):
    '''Add application font.'''
    QtGui.QFontDatabase.addApplicationFont(font)


def applyTheme(widget, theme='light', baseTheme=None):
    '''Apply *theme* to *widget*.'''
    # Set base style.
    if baseTheme and QtGui.QApplication.style().objectName() != baseTheme:
        QtGui.QApplication.setStyle(baseTheme)

    # Load stylesheet from resource file and apply.
    fileObject = QtCore.QFile(':/ftrack/style/{0}'.format(theme))
    fileObject.open(
        QtCore.QFile.ReadOnly | QtCore.QFile.Text
    )
    stream = QtCore.QTextStream(fileObject)
    styleSheetContent = stream.readAll()

    print '!!!!!'
    print styleSheetContent

    widget.setStyleSheet(styleSheetContent)
