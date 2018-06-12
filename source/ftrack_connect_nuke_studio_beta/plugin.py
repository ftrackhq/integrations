# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from __future__ import absolute_import

import logging

from QtExt import QtGui, QtWidgets
import hiero.ui
import hiero.core

import ftrack_connect.ui.theme
import ftrack_connect.event_hub_thread

logger = logging.getLogger(__name__)

from ftrack_connect_nuke_studio_beta.processors import register_processors

ftrack_connect.ui.theme.applyFont()


def populate_ftrack(event):
    '''Populate the ftrack menu with items.'''
    menu_bar = hiero.ui.menuBar()

    ftrack_menu = menu_bar.addMenu(
        QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'), 'ftrack'
    )


# Trigger population of the ftrack menu.
logger.debug('Populate the ftrack menu')
hiero.core.events.registerInterest(
    'kStartup', populate_ftrack
)

# TODO: move to events!
register_processors()