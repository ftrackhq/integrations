# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from PySide2 import QtWidgets

import nuke, nukescripts
from nukescripts import panels


def dock_nuke_right(label, widget):
    '''Dock *widget*, with *name* and *label* to the right of the properties panel in Nuke'''
    class_name = widget.__class__.__name__

    if class_name not in globals():
        globals()[class_name] = lambda *args, **kwargs: widget

        # Register docked panel
        panels.registerWidgetAsPanel(
            f'{__name__}.{class_name}', f'ftrack {label}', class_name
        )

    # Restore panel
    pane = nuke.getPaneFor("Properties.1")

    panel = nukescripts.restorePanel(class_name)
    panel.addToPane(pane)


def find_nodegraph_viewer(activate=False):
    '''Find the nodegraph viewers by title'''
    stack = QtWidgets.QApplication.topLevelWidgets()
    viewers = []
    while stack:
        widget = stack.pop()
        if widget.windowTitle().lower().startswith('node graph'):
            viewers.append(widget)
        stack.extend(c for c in widget.children() if c.isWidgetType())
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
