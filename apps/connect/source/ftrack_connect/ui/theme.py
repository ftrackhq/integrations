# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui


def applyFont():
    """Add application font."""
    fonts = [
        ":/ftrack/connect/font/regular",
        ":/ftrack/connect/font/medium",
    ]
    for font in fonts:
        if QtCore.QFile(font).exists():
            QtGui.QFontDatabase.addApplicationFont(font)


def applyTheme(widget, theme="light", baseTheme=None):
    """Apply *theme* to *widget*."""
    # Set base style.
    if baseTheme and QtWidgets.QApplication.style().objectName() != baseTheme:
        QtWidgets.QApplication.setStyle(baseTheme)

    # Load stylesheet from resource file and apply.
    candidate_paths = [
        ":/ftrack/connect/style/{0}".format(theme),
        ":/ftrack/style/{0}".format(theme),
    ]

    for theme_path in candidate_paths:
        fileObject = QtCore.QFile(theme_path)
        if not fileObject.exists():
            continue

        fileObject.open(
            QtCore.QFile.OpenModeFlag.ReadOnly | QtCore.QFile.OpenModeFlag.Text
        )
        stream = QtCore.QTextStream(fileObject)
        styleSheetContent = stream.readAll()
        widget.setStyleSheet(styleSheetContent)
        break
