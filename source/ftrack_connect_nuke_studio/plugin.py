# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from __future__ import absolute_import

import functools
import logging

from PySide import QtGui
import hiero.ui
import hiero.core
import nuke

import ftrack_connect.ui.theme
import ftrack_connect.event_hub_thread

# Setup logging for ftrack.
# TODO: Check with The Foundry if there is any better way to customise logging.
from . import logging as _logging
_logging.setup()


import ftrack
ftrack.setup()


from ftrack_connect_nuke_studio.ui.create_project import ProjectTreeDialog
from ftrack_connect_nuke_studio.ui.tag_drop_handler import TagDropHandler
import ftrack_connect_nuke_studio.ui.tag_manager
import ftrack_connect_nuke_studio.ui.widget.info_view
import ftrack_connect_nuke_studio.ui.crew


# Start thread to handle events from ftrack.
eventHubThread = ftrack_connect.event_hub_thread.EventHubThread()
eventHubThread.start()

# Import crew hub to instantiate a global crew hub.
import ftrack_connect_nuke_studio.crew_hub

ftrack_connect.ui.theme.applyFont()

logger = logging.getLogger(__name__)


def populate_ftrack(event):
    '''Populate the ftrack menu with items.'''
    mainMenu = nuke.menu('Nuke')
    ftrackMenu = mainMenu.addMenu('&ftrack')

    window_manager = hiero.ui.windowManager()

    information_view = ftrack_connect_nuke_studio.ui.widget.info_view.InfoView()
    window_manager.addWindow(information_view)

    ftrackMenu.addCommand(
        ftrack_connect_nuke_studio.ui.widget.info_view.InfoView.get_display_name(),
        functools.partial(window_manager.showWindow, information_view)
    )

    crew = ftrack_connect_nuke_studio.ui.crew.NukeCrew()

    window_manager.addWindow(crew)

    ftrackMenu.addCommand(
        'Crew', functools.partial(window_manager.showWindow, crew)
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
logger.debug('Setup event listeners for timeline.')
hiero.core.events.registerInterest(
    (
        hiero.core.events.EventType.kShowContextMenu,
        hiero.core.events.EventType.kTimeline
    ), on_context_menu_event
)

# Setup the TagManager and TagDropHandler.
logger.debug('Setup tag manager and tag drop handler.')
tag_handler = TagDropHandler()
hiero.core.events.registerInterest(
    'kStartup', ftrack_connect_nuke_studio.ui.tag_manager.TagManager
)

# Trigger population of the ftrack menu.
logger.debug('Populate the ftrack menu')
hiero.core.events.registerInterest(
    'kStartup', populate_ftrack
)
