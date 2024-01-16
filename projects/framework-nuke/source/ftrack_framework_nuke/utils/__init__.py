# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

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
