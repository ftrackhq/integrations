# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import functools

from PySide import QtGui
import hiero.ui
import hiero.core
import nuke

import ftrack_connect.ui.theme
import ftrack_connect.event_hub_thread
import ftrack

from ftrack_connect_nuke_studio.ui.create_project import ProjectTreeDialog
from ftrack_connect_nuke_studio.ui.tag_drop_handler import TagDropHandler
from ftrack_connect_nuke_studio.ui.tag_manager import TagManager

import ftrack_connect_nuke_studio.ui.widget.info_view

# Run setup to discover any Location or Event plugins for ftrack.
ftrack.setup()

# Start thread to handle events from ftrack.
eventHubThread = ftrack_connect.event_hub_thread.EventHubThread()
eventHubThread.start()

# Import crew hub to instantiate a global crew hub.
import ftrack_connect_nuke_studio.crew_hub

ftrack_connect.ui.theme.applyFont()


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
    'kStartup', TagManager
)

# Trigger population of the ftrack menu.
populate_ftrack()

hiero.ui.setWorkspace('dev')

