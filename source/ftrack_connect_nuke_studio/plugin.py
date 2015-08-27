# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import functools

from PySide import QtGui
import hiero.ui
import hiero.core
import nuke
from nukescripts import panels

from ftrack_connect_nuke_studio.ui.create_project import ProjectTreeDialog
from ftrack_connect_nuke_studio.ui.tag_drop_handler import TagDropHandler
from ftrack_connect_nuke_studio.ui.tag_manager import TagManager

import ftrack_connect_nuke_studio.ui.widget.info_view

import ftrack

# Run setup to discover any Location or Event plugins for ftrack.
ftrack.setup()

def populate_ftrack():
    '''Populate the ftrack menu with items.

    .. note ::

        This method is using the nuke module which will not work if the
        plugin run in Hiero.

    '''
    # Inline to not break if plugin run in Hiero.
    import nuke

    mainMenu = nuke.menu('Nuke')
    ftrackMenu = mainMenu.addMenu('&ftrack')

    panels.registerWidgetAsPanel(
        'ftrack_connect_nuke_studio.ui.widget.info_view.InfoView',
        ftrack_connect_nuke_studio.ui.widget.info_view.InfoView.get_display_name(),
        ftrack_connect_nuke_studio.ui.widget.info_view.InfoView.get_identifier()
    )
    ftrackMenu.addCommand(
        ftrack_connect_nuke_studio.ui.widget.info_view.InfoView.get_display_name(),
        'import ftrack_connect_nuke_studio;'
        'pane = nuke.getPaneFor("Properties.1");'
        'panel = nukescripts.restorePanel("{0}");'
        'panel.addToPane(pane)'.format(
            ftrack_connect_nuke_studio.ui.widget.info_view.InfoView.get_identifier()
        )
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