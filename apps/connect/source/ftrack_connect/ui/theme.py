# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui


def applyFont():
    '''Add application font.'''
    fonts = [':/ftrack/font/regular', ':/ftrack/font/medium']
    for font in fonts:
        QtGui.QFontDatabase.addApplicationFont(font)


def applyTheme(widget, theme='light', baseTheme=None):
    '''Apply *theme* to *widget*.'''
    # Set base style.
    if baseTheme and QtWidgets.QApplication.style().objectName() != baseTheme:
        QtWidgets.QApplication.setStyle(baseTheme)

    # Load stylesheet from resource file and apply.
    fileObject = QtCore.QFile(':/ftrack/style/{0}'.format(theme))
    fileObject.open(
        QtCore.QFile.OpenModeFlag.ReadOnly | QtCore.QFile.OpenModeFlag.Text
    )
    stream = QtCore.QTextStream(fileObject)
    styleSheetContent = stream.readAll()

    widget.setStyleSheet(styleSheetContent)
