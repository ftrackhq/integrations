# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

try:
    from PySide6 import QtCore  # noqa: F401
    from PySide6 import QtWidgets  # noqa: F401
    from shiboken6 import wrapInstance  # noqa: F401
except ImportError:
    from PySide2 import QtCore  # noqa: F401
    from PySide2 import QtWidgets  # noqa: F401
    from shiboken2 import wrapInstance  # noqa: F401

import maya.OpenMayaUI as omui


def get_maya_main_window():
    """Return Maya's main window as a QWidget."""
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


def format_bytes(n):
    """Format *n* bytes as a human-readable string."""
    if n < 1024:
        return f"{n} B"
    for unit in ("KB", "MB", "GB", "TB"):
        n /= 1024.0
        if n < 1024:
            return f"{n:.1f} {unit}"
    return f"{n:.1f} PB"
