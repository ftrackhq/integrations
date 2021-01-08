# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import hiero.core
from Qt import QtWidgets, QtCore, QtGui


from ftrack_connect_nuke_studio import config
config.configure_logging('ftrack_connect_nuke_studio', level='WARNING')

from ftrack_connect_nuke_studio.actions.build_track import FtrackBuildTrack
from ftrack_connect_nuke_studio.tags.tag_drop_handler import TagDropHandler
from ftrack_connect_nuke_studio.tags.tag_manager import TagManager
from ftrack_connect_nuke_studio.overrides.version_scanner import register_versioning_overrides
from ftrack_connect_nuke_studio.processors import register_processors
import ftrack_connect_nuke_studio.resource


def populate_ftrack(event):
    '''Populate the ftrack menu with items.'''
    import hiero.ui
    from Qt import QtWidgets, QtCore, QtGui

    menu_bar = hiero.ui.menuBar()
    ftrack_menu = menu_bar.addMenu(
        QtGui.QPixmap(':ftrack/image/default/ftrackLogoLight'), 'ftrack'
    )


if (not hiero.core.isHieroPlayer()) and isinstance(QtCore.QCoreApplication.instance(), QtWidgets.QApplication):

    hiero.core.events.registerInterest(
        'kStartup', TagManager
    )

    hiero.core.events.registerInterest(
        'kStartup', populate_ftrack
    )

    ftrackBuildExternalMediaTrackAction = FtrackBuildTrack()
    tag_handler = TagDropHandler()

    register_processors()
    register_versioning_overrides()

