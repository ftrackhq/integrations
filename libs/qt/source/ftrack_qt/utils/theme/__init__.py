# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import sys

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

import ftrack_constants.qt as qt_constants


def apply_font(font=':/ftrack/font/main'):
    '''Add application *font*.'''
    QtGui.QFontDatabase.addApplicationFont(font)


def apply_theme(widget, theme=None):
    '''Apply *theme* to *widget* - load stylesheet from resource file and apply'''
    apply_font()
    if theme is None:
        theme = qt_constants.theme.DEFAULT_THEME
    theme_path = ':/ftrack/style/{0}'.format(theme)
    fileObject = QtCore.QFile(theme_path)
    if fileObject.exists():
        fileObject.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
        stream = QtCore.QTextStream(fileObject)
        styleSheetContent = stream.readAll()

        widget.setStyleSheet(styleSheetContent)
    else:
        sys.stderr.write(
            'ftrack theme "{}" could not be found! Make sure to import '
            'resource.py from ftrack_qt_style library.\n'.format(theme_path)
        )
