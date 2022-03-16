# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import functools
import logging
import atexit

import nuke
import nukescripts

from Qt import QtWidgets

import ftrack_connect_pipeline_nuke
from ftrack_connect_pipeline_nuke import host as nuke_host
from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline import constants

from ftrack_connect_pipeline_qt import constants as qt_constants

from ftrack_connect_pipeline_nuke.client import open
from ftrack_connect_pipeline_nuke.client import assembler
from ftrack_connect_pipeline_nuke.client import save
from ftrack_connect_pipeline_nuke.client import asset_manager
from ftrack_connect_pipeline_nuke.client import publish
from ftrack_connect_pipeline_nuke.client import log_viewer
from ftrack_connect_pipeline_qt import client

from ftrack_connect_pipeline_nuke.menu import build_menu_widgets

from ftrack_connect_pipeline_qt.ui.asset_manager.base import AssetListModel

import ftrack_api

from ftrack_connect_pipeline.configure_logging import configure_logging

configure_logging(
    'ftrack_connect_pipeline_nuke',
    extra_modules=['ftrack_connect_pipeline', 'ftrack_connect_pipeline_qt'],
)

logger = logging.getLogger('ftrack_connect_pipeline_nuke')

created_dialogs = dict()


def get_ftrack_menu(menu_name='ftrack', submenu_name='pipeline'):
    '''Get the current ftrack menu, create it if does not exists.'''

    nuke_menu = nuke.menu("Nuke")
    ftrack_menu = nuke_menu.findItem(menu_name)
    if not ftrack_menu:
        ftrack_menu = nuke_menu.addMenu(menu_name)
    if submenu_name is not None:
        ftrack_sub_menu = ftrack_menu.findItem(submenu_name)
        if not ftrack_sub_menu:
            ftrack_sub_menu = ftrack_menu.addMenu(submenu_name)

        return ftrack_sub_menu
    else:
        return ftrack_menu


class WidgetLauncher(object):
    def __init__(self, host):
        self._host = host

    def launch(self, widget_name):
        self._host.launch_widget(widget_name)


created_widgets = dict()


def _open_widget(event_manager, asset_list_model, widgets, event):
    '''Open Nuke widget based on widget name in *event*, and create if not already
    exists'''
    widget_name = None
    widget_class = None
    for (_widget_name, _widget_class, unused_label, unused_image) in widgets:
        if _widget_name == event['data']['pipeline']['widget_name']:
            widget_name = _widget_name
            widget_class = _widget_class
            break
    if widget_name:
        if widget_name in [
            qt_constants.ASSET_MANAGER_WIDGET,
            qt_constants.PUBLISHER_WIDGET,
        ]:
            # Restore panel
            pane = nuke.getPaneFor("Properties.1")
            panel = nukescripts.restorePanel(widget_name)
            panel.addToPane(pane)
        else:
            if widget_name not in created_widgets:
                ftrack_client = widget_class
                created_widgets[widget_name] = ftrack_client(
                    event_manager, asset_list_model
                )
            created_widgets[widget_name].show()
    else:
        raise Exception(
            'Unknown widget {}!'.format(
                event['data']['pipeline']['widget_name']
            )
        )


def initialise():
    # TODO : later we need to bring back here all the nuke initialiations
    #  from ftrack-connect-nuke such as frame start / end etc....

    logger.debug('Setting up the menu')
    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = event.QEventManager(
        session=session, mode=constants.LOCAL_EVENT_MODE
    )
    host = nuke_host.NukeHost(event_manager)

    asset_list_model = AssetListModel(event_manager)

    created_widgets = dict()

    widgets = list()
    widgets.append(
        (qt_constants.OPEN_WIDGET, open.NukeOpenDialog, 'Open', 'fileOpen')
    )
    widgets.append(
        (
            qt_constants.ASSEMBLER_WIDGET,
            assembler.NukeAssemblerDialog,
            'Assembler',
            '',
        )
    )
    widgets.append(
        (
            qt_constants.ASSET_MANAGER_WIDGET,
            asset_manager.NukeAssetManagerClient,
            'Asset Manager',
            '',
        )
    )
    widgets.append(
        (
            qt_constants.SAVE_WIDGET,
            save.QtSaveClient,
            'Save Snapshot',
            '',
        )
    )
    widgets.append(
        (
            qt_constants.PUBLISHER_WIDGET,
            publish.NukePublisherClient,
            'Publisher',
            '',
        )
    )
    widgets.append(
        (
            qt_constants.LOG_VIEWER_WIDGET,
            log_viewer.NukeLogViewerDialog,
            'Log Viewer',
            '',
        )
    )
    widgets.append(
        (
            qt_constants.DOC_WIDGET,
            client.QtDocumentationClient,
            'Documentation',
            '',
        )
    )

    ftrack_menu = get_ftrack_menu(submenu_name=None)
    widget_launcher = WidgetLauncher(host)

    build_menu_widgets(
        ftrack_menu, widget_launcher, widgets, event_manager, asset_list_model
    )

    # Listen to client launch events
    session.event_hub.subscribe(
        'topic={} and data.pipeline.host_id={}'.format(
            constants.PIPELINE_WIDGET_LAUNCH, host.host_id
        ),
        functools.partial(
            _open_widget, event_manager, asset_list_model, widgets
        ),
    )

    def on_nuke_exit():
        logger.info('Shutting down ftrack integration.')
        session.event_hub.disconnect()

    app = QtWidgets.QApplication.instance()
    app.aboutToQuit.connect(on_nuke_exit)


initialise()
