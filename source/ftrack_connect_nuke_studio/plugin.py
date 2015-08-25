# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import functools

from PySide import QtGui
import hiero.ui
import hiero.core

from ftrack_connect_nuke_studio.ui.create_project import ProjectTreeDialog
from ftrack_connect_nuke_studio.ui.tag_drop_handler import TagDropHandler
from ftrack_connect_nuke_studio.ui.tag_manager import TagManager

import ftrack

# Run setup to discover any Location or Event plugins for ftrack.
ftrack.setup()


def open_export_dialog(*args, **kwargs):
    '''Open export project from timeline context menu.'''
    parent = hiero.ui.mainWindow()
    ftags = []
    trackItems = args[0]

    sequence = None
    for item in trackItems:
        if not isinstance(item, hiero.core.TrackItem):
            continue
        tags = item.tags()
        tags = [tag for tag in tags if tag.metadata().hasKey('ftrack.type')]
        ftags.append((item, tags))
        sequence = item.sequence()

    dialog = ProjectTreeDialog(
        data=ftags, parent=parent, sequence=sequence
    )
    dialog.exec_()


def on_context_menu_event(event):
    menu = event.menu.addMenu(
        QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'), 'ftrack'
    )

    action_callback = functools.partial(
        open_export_dialog, event.sender.selection()
    )

    action = QtGui.QAction(
        'Export project', menu,
        triggered=action_callback
    )

    # Disable the Export option if no track items are selected.
    action.setDisabled(
        len(event.sender.selection()) == 0
    )

    menu.addAction(action)

hiero.core.events.registerInterest(
    (
        hiero.core.events.EventType.kShowContextMenu,
        hiero.core.events.EventType.kTimeline
    ), on_context_menu_event
)

tag_handler = TagDropHandler()

hiero.core.events.registerInterest(
    'kStartup', TagManager
)

hiero.ui.setWorkspace('dev')