# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from __future__ import absolute_import

import functools
import logging

from QtExt import QtGui, QtWidgets, is_webwidget_supported
import hiero.ui
import hiero.core

import ftrack_connect.ui.theme
import ftrack_connect.event_hub_thread


# Setup logging for ftrack.
# TODO: Check with The Foundry if there is any better way to customise logging.
from . import logging as _logging
_logging.setup()
logger = logging.getLogger(__name__)


import ftrack
ftrack.setup()

import ftrack_connect_nuke_studio.ui.widget.info_view
from ftrack_connect_nuke_studio.fn_processors import register_processors


ftrack_connect.ui.theme.applyFont()


def populate_ftrack(event):
    '''Populate the ftrack menu with items.'''
    parent = hiero.ui.mainWindow()
    menu_bar = hiero.ui.menuBar()

    ftrack_menu = menu_bar.addMenu(
        QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'), 'ftrack'
    )

    window_manager = hiero.ui.windowManager()

    if is_webwidget_supported():
        information_view = ftrack_connect_nuke_studio.ui.widget.info_view.InfoView(
            parent=parent
        )
        window_manager.addWindow(information_view)

        information_view_action = QtWidgets.QAction(
            ftrack_connect_nuke_studio.ui.widget.info_view.InfoView.get_display_name(),
            ftrack_menu
        )

        information_view_action.triggered.connect(
            functools.partial(window_manager.showWindow, information_view)
        )

        ftrack_menu.addAction(information_view_action)


# Trigger population of the ftrack menu.
logger.debug('Populate the ftrack menu')
hiero.core.events.registerInterest(
    'kStartup', populate_ftrack
)

register_processors()