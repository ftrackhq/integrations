# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack
import sys

from Qt import QtCore, QtWidgets, QtGui


def applyFont(font=':/ftrack/font/main'):
    '''Add application font.'''
    QtGui.QFontDatabase.addApplicationFont(font)


def applyTheme(widget, theme='dark', baseTheme=None):
    '''Apply *theme* to *widget*.'''
    # Set base style.
    # if baseTheme and QtWidgets.QApplication.style().objectName() != baseTheme:
    #    QtWidgets.QApplication.setStyle(baseTheme)

    # if not QtCore.QFile(':/ftrack/font/main').exists():
    #    raise Exception('TEST ! Font does not exist!')

    # Load stylesheet from resource file and apply.
    theme_path = ':/ftrack/style/{0}'.format(theme)
    fileObject = QtCore.QFile(theme_path)
    if fileObject.exists():
        fileObject.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
        stream = QtCore.QTextStream(fileObject)
        styleSheetContent = stream.readAll()

        widget.setStyleSheet(styleSheetContent)
    else:
        sys.stderr.write(
            'ftrack theme "{}" could not be found! Make sure to import ui/resource.py.\n'.format(theme_path)
        )
