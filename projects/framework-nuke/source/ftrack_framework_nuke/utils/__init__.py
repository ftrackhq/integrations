# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
from functools import wraps
import threading

try:
    from PySide6 import QtWidgets
except ImportError:
    from PySide2 import QtWidgets

import nuke, nukescripts
from nukescripts import panels


def dock_nuke_right(widget):
    '''Dock *widget*, to the right of the properties panel in Nuke'''
    widget.show()
    # TODO: To provide docking functionality, comment line above and uncomment code below
    # class_name = widget.__class__.__name__
    #
    # if class_name not in globals():
    #     globals()[class_name] = lambda *args, **kwargs: widget
    #
    #     # Register docked panel
    #     panels.registerWidgetAsPanel(
    #         f'{__name__}.{class_name}', widget.windowTitle(), class_name
    #     )
    #
    # # Restore panel
    # pane = nuke.getPaneFor("Properties.1")
    #
    # panel = nukescripts.restorePanel(class_name)
    # panel.addToPane(pane)


def find_nodegraph_viewer(activate=False):
    '''Find the nodegraph viewers by title'''
    stack = QtWidgets.QApplication.topLevelWidgets()
    viewers = []
    while stack:
        widget = stack.pop()
        if widget.windowTitle().lower().startswith('node graph'):
            viewers.append(widget)
        stack.extend(
            c
            for c in widget.children()
            if hasattr(c, 'isWidgetType') and c.isWidgetType()
        )
    if len(viewers) <= 1:
        raise Exception(
            'Could not find node graph viewer to export image from'
        )
    widget = viewers[1]
    if activate:
        activate_nodegraph_viewer(widget)
    return widget


def activate_nodegraph_viewer(widget):
    '''Activate the nodegraph viewer'''
    stacked_widget = widget.parent()
    idx = stacked_widget.indexOf(widget)
    if stacked_widget.currentIndex() != idx:
        stacked_widget.setCurrentIndex(idx)


def run_in_main_thread(f):
    '''Make sure a function runs in the main Maya thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            return nuke.executeInMainThreadWithResult(
                f, args=args, kwargs=kwargs
            )
        else:
            return f(*args, **kwargs)

    return decorated
