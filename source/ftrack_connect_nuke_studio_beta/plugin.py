# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

from __future__ import absolute_import

import logging
logger = logging.getLogger(__name__)

from QtExt import QtGui, QtWidgets, QtCore
import hiero.ui
import hiero.core

from ftrack_connect import config
config.configure_logging('ftrack_connect_nuke_studio_beta', level='WARNING')

import ftrack_connect.ui.theme
import ftrack_connect.event_hub_thread
from ftrack_connect_nuke_studio_beta.actions.build_track import FtrackBuildTrack
from ftrack_connect_nuke_studio_beta.tags.tag_drop_handler import TagDropHandler
from ftrack_connect_nuke_studio_beta.tags.tag_manager import TagManager
from ftrack_connect_nuke_studio_beta.overrides.version_scanner import register_versioning_overrides

register_versioning_overrides()

from ftrack_connect_nuke_studio_beta.processors import register_processors
ftrack_connect.ui.theme.applyFont()


def populate_ftrack(event):
    '''Populate the ftrack menu with items.'''
    menu_bar = hiero.ui.menuBar()
    ftrack_menu = menu_bar.addMenu(
        QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'), 'ftrack'
    )


if (not hiero.core.isHieroPlayer()) and isinstance(QtCore.QCoreApplication.instance(), QtWidgets.QApplication):

    hiero.core.events.registerInterest(
        'kStartup', TagManager
    )

    hiero.core.events.registerInterest(
        'kStartup', populate_ftrack
    )

    ftrackBuildExternalMediaTrackAction = FtrackBuildTrack()
    register_processors()
    tag_handler = TagDropHandler()
