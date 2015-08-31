# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from __future__ import absolute_import

import functools

from PySide import QtGui
import hiero.ui
import hiero.core
import nuke

from ftrack_connect_nuke_studio.ui.create_project import ProjectTreeDialog
from ftrack_connect_nuke_studio.ui.tag_drop_handler import TagDropHandler
import ftrack_connect_nuke_studio.ui.tag_manager
import ftrack_connect_nuke_studio.ui.widget.info_view

# Setup logging for ftrack.
# TODO: Check with The Foundry if there is any better way to customise logging.
from . import logging as _logging

import ftrack

# Run setup to discover any Location or Event plugins for ftrack.
ftrack.setup()

# Setup logging.
_logging.setup()

def populate_ftrack():
    '''Populate the ftrack menu with items.'''
    mainMenu = nuke.menu('Nuke')
    ftrackMenu = mainMenu.addMenu('&ftrack')

    information_view = ftrack_connect_nuke_studio.ui.widget.info_view.InfoView()
    window_manager = hiero.ui.windowManager()
    window_manager.addWindow(information_view)

    ftrackMenu.addCommand(
        ftrack_connect_nuke_studio.ui.widget.info_view.InfoView.get_display_name(),
        functools.partial(window_manager.showWindow, information_view)
    )


def open_export_dialog(*args, **kwargs):
    '''Open export project from timeline context menu.'''
    parent = hiero.ui.mainWindow()
    ftags = []
    trackItems = args[0]

    sequence = None
    for item in trackItems:
        if not isinstance(item, hiero.core.TrackItem):
            continue

        ftrack_connect_nuke_studio.ui.tag_manager.update_tag_value_from_name(
            item
        )

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


# Register for Context menu events in the Timeline.
hiero.core.events.registerInterest(
    (
        hiero.core.events.EventType.kShowContextMenu,
        hiero.core.events.EventType.kTimeline
    ), on_context_menu_event
)

# Setup the TagManager and TagDropHandler.
tag_handler = TagDropHandler()
hiero.core.events.registerInterest(
    'kStartup', ftrack_connect_nuke_studio.ui.tag_manager.TagManager
)

# Trigger population of the ftrack menu.
populate_ftrack()

hiero.ui.setWorkspace('dev')