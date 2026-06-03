# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
from functools import wraps
import threading

try:
    from PySide6 import QtWidgets
except ImportError:
    from PySide2 import QtWidgets

import nuke
import nukescripts  # noqa: F401 — imported for side-effects
from nukescripts import panels  # noqa: F401 — imported for side-effects


def dock_nuke_right(widget):
    """Dock *widget*, to the right of the properties panel in Nuke"""
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
    """Find the nodegraph viewers by title"""
    stack = QtWidgets.QApplication.topLevelWidgets()
    viewers = []
    while stack:
        widget = stack.pop()
        if widget.windowTitle().lower().startswith("node graph"):
            viewers.append(widget)
        stack.extend(
            c
            for c in widget.children()
            if hasattr(c, "isWidgetType") and c.isWidgetType()
        )
    if len(viewers) <= 1:
        raise Exception(
            "Could not find node graph viewer to export image from"
        )
    widget = viewers[1]
    if activate:
        activate_nodegraph_viewer(widget)
    return widget


def activate_nodegraph_viewer(widget):
    """Activate the nodegraph viewer"""
    stacked_widget = widget.parent()
    idx = stacked_widget.indexOf(widget)
    if stacked_widget.currentIndex() != idx:
        stacked_widget.setCurrentIndex(idx)


def run_in_main_thread(f):
    """Make sure a function runs in the main Maya thread."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != "MainThread":
            return nuke.executeInMainThreadWithResult(
                f, args=args, kwargs=kwargs
            )
        else:
            return f(*args, **kwargs)

    return decorated


def get_nodes_with_ftrack_tab():
    """Return all Nuke nodes that carry the ``ftracktab`` Tab knob — the
    marker the asset manager uses to discover loaded assets."""
    from ftrack_framework_nuke.asset import constants as asset_const

    return [
        n
        for n in nuke.allNodes(recurseGroups=True)
        if n.knob(asset_const.FTRACK_PLUGIN_TYPE)
    ]


def clean_selection():
    """Deselect every node in the script."""
    for n in nuke.allNodes(recurseGroups=True):
        sel = n.knob("selected")
        if sel is not None:
            sel.setValue(False)


def sync_asset_link_on_rename():
    """addKnobChanged callback. When a content node's ``name`` knob
    changes, rewrite the ``asset_link`` knob on every ftrack-tagged
    Backdrop that contains the renamed node so it reflects the current
    names.

    TODO(asset_link): stopgap. Replace with a live nuke.Link_Knob
    cross-reference if a workable solution to Link_Knob's visibility
    quirks turns up (see comment in
    ``NukeDccObject.connect_objects``)."""
    from ftrack_framework_nuke.asset import constants as asset_const

    knob = nuke.thisKnob()
    if knob is None or knob.name() != "name":
        return
    renamed_node = nuke.thisNode()
    if renamed_node is None:
        return

    for backdrop in nuke.allNodes("BackdropNode"):
        if not backdrop.knob(asset_const.FTRACK_PLUGIN_TYPE):
            continue
        contained = backdrop.getNodes()
        if renamed_node not in contained:
            continue
        link_knob = backdrop.knob(asset_const.ASSET_LINK)
        if link_knob is None:
            continue
        names = [n.name() for n in contained if n is not backdrop]
        link_knob.setValue(";".join(names))


def register_asset_link_sync():
    """Register :func:`sync_asset_link_on_rename` for the content node
    classes the loader importer creates. Called once from
    ``bootstrap_integration``."""
    for node_class in ("Read", "ReadGeo2", "AudioRead", "Camera2"):
        nuke.addKnobChanged(sync_asset_link_on_rename, nodeClass=node_class)
