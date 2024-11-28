# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import threading
from functools import wraps

from typing import Callable

from PySide6.QtWidgets import QDockWidget, QSizePolicy
from PySide6.QtCore import Qt, QObject, Signal, Slot
from PySide6.QtGui import QGuiApplication

import qtmax


# Dock widget in Max
def dock_max_right(widget):
    '''Dock *widget* to the right side of Max.'''
    # Use the current widget's parent as the parent for the dockable
    # widget
    widget.show()

    # TODO: Check for existing publisher widget and delete if exists
    # TODO: To provide docking functionality, uncomment the code below
    # dock_widget = QDockWidget()
    # dock_widget.setWindowTitle(widget.windowTitle())
    # dock_widget.setObjectName(widget.windowTitle())
    # dock_widget.setWidget(widget)
    # qtmax.GetQMaxMainWindow().addDockWidget(
    #     Qt.RightDockWidgetArea,
    #     dock_widget,
    #     Qt.Horizontal
    # )
    # dock_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    # dock_widget.setAttribute(Qt.WA_DeleteOnClose)
    # dock_widget.setFloating(False)
    # dock_widget.show()
