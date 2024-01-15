# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import nuke, nukescripts
from nukescripts import panels

from ftrack_utils.paths import get_temp_path


def dock_nuke_right(name, label, widget):
    '''Dock *widget*, with *name* and *label* to the right of the properties panel in Nuke'''
    class_name = f'ftrack{name.title()}Class'

    if class_name not in globals():
        globals()[class_name] = lambda *args, **kwargs: widget

        # Register docked panel
        panels.registerWidgetAsPanel(
            f'{__name__}.{class_name}',
            f'ftrack {label}',
            name,
        )

    # Restore panel
    pane = nuke.getPaneFor("Properties.1")
    panel = nukescripts.restorePanel(name)
    panel.addToPane(pane)


def save_temp():
    '''Save script locally in temp folder.'''

    save_path = get_temp_path(filename_extension='.nk')

    nuke.scriptSaveAs(save_path, overwrite=1)

    return save_path
