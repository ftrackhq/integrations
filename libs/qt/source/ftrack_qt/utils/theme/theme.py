# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import sys

from Qt import QtCore, QtWidgets, QtGui


from ftrack_constants.qt import DEFAULT_THEME

def apply_font(font=':/ftrack/font/main'):
    '''Add application *font*.'''
    QtGui.QFontDatabase.addApplicationFont(font)


def apply_theme(widget, theme=None):
    '''Apply *theme* to *widget* - load stylesheet from resource file and apply'''
    apply_font()
    if theme is None:
        theme = DEFAULT_THEME
    theme_path = ':/ftrack/style/{0}'.format(theme)
    fileObject = QtCore.QFile(theme_path)
    if fileObject.exists():
        fileObject.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
        stream = QtCore.QTextStream(fileObject)
        styleSheetContent = stream.readAll()

        widget.setStyleSheet(styleSheetContent)
    else:
        sys.stderr.write(
            'ftrack theme "{}" could not be found! Make sure to import resource.py from ftrack_style library.\n'.format(
                theme_path
            )
        )
