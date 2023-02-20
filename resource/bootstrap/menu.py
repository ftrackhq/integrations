# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import functools
import logging
import sys
import traceback

import nuke
import nukescripts

from Qt import QtWidgets

import ftrack_api

import ftrack_connect_pipeline_nuke
from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.configure_logging import configure_logging

from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.asset_manager.model import AssetListModel

from ftrack_connect_pipeline_nuke.client import (
    open,
    load,
    asset_manager,
    publish,
    change_context,
    log_viewer,
)
from ftrack_connect_pipeline_qt.client import documentation

from ftrack_connect_pipeline_nuke.menu import build_menu_widgets
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils
from ftrack_connect_pipeline_nuke import host as nuke_host

configure_logging(
    'ftrack_connect_pipeline_nuke',
    extra_modules=['ftrack_connect_pipeline', 'ftrack_connect_pipeline_qt'],
)

logger = logging.getLogger('ftrack_connect_pipeline_nuke')


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
        self._host.launch_client(widget_name)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    nuke.tprint(
        "[ERROR] Uncaught Nuke exception: {}".format(
            '\n'.join(
                traceback.format_exception(exc_type, exc_value, exc_traceback)
            )
        )
    )


sys.excepthook = handle_exception

created_widgets = dict()


def _open_widget(event_manager, asset_list_model, widgets, event):
    '''Open Nuke widget based on widget name in *event*, and create if not already
    exists'''
    widget_name = None
    widget_class = None
    for item in widgets:
        if isinstance(item, tuple):
            (_widget_name, _widget_class, unused_label, unused_image) = item
            if _widget_name == event['data']['pipeline']['name']:
                widget_name = _widget_name
                widget_class = _widget_class
                break
    if widget_name:
        widget = None
        if widget_name in created_widgets:
            widget = created_widgets[widget_name]
            # Is it still visible?
            is_valid_and_visible = False
            try:
                if widget is not None and widget.isVisible():
                    is_valid_and_visible = True
            except:
                pass
            finally:
                if not is_valid_and_visible:
                    del created_widgets[widget_name]  # Not active any more
                    if widget:
                        try:
                            widget.deleteLater()  # Make sure it is deleted
                        except:
                            pass
                        widget = None
        if widget is None:
            # Need to create
            if widget_name in [
                core_constants.ASSET_MANAGER,
                core_constants.PUBLISHER,
            ]:
                # Restore panel
                pane = nuke.getPaneFor("Properties.1")
                panel = nukescripts.restorePanel(widget_name)
                panel.addToPane(pane)
            else:
                ftrack_client = widget_class
                if widget_name in [
                    qt_constants.ASSEMBLER_WIDGET,
                    core_constants.ASSET_MANAGER,
                ]:
                    widget = ftrack_client(event_manager, asset_list_model)
                else:
                    widget = ftrack_client(event_manager)
                widget.show()
                created_widgets[widget_name] = widget
    else:
        raise Exception(
            'Unknown widget {}!'.format(event['data']['pipeline']['name'])
        )


def initialise():

    logger.debug('Setting up the menu')
    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = event.QEventManager(
        session=session, mode=core_constants.LOCAL_EVENT_MODE
    )
    host = nuke_host.NukeHost(event_manager)

    asset_list_model = AssetListModel(event_manager)

    widgets = list()
    widgets.append(
        (
            core_constants.OPENER,
            open.NukeQtOpenerClientWidget,
            'Open',
            'fileOpen',
        )
    )
    widgets.append(
        (
            qt_constants.ASSEMBLER_WIDGET,
            load.NukeQtAssemblerClientWidget,
            'Assembler',
            '',
        )
    )
    widgets.append(
        (
            core_constants.ASSET_MANAGER,
            asset_manager.NukeQtAssetManagerClientWidget,
            'Asset Manager',
            '',
        )
    )
    widgets.append(
        (
            core_constants.PUBLISHER,
            publish.NukeQtPublisherClientWidget,
            'Publisher',
            '',
        )
    )
    widgets.append('separator')
    widgets.append(
        (
            qt_constants.CHANGE_CONTEXT_WIDGET,
            change_context.NukeQtChangeContextClientWidget,
            'Change context',
            '',
        )
    )
    widgets.append('separator')
    widgets.append(
        (
            core_constants.LOG_VIEWER,
            log_viewer.NukeQtLogViewerClientWidget,
            'Log Viewer',
            '',
        )
    )
    widgets.append(
        (
            qt_constants.DOCUMENTATION_WIDGET,
            documentation.QtDocumentationClientWidget,
            'Documentation',
            '',
        )
    )

    ftrack_menu = get_ftrack_menu(submenu_name=None)
    widget_launcher = WidgetLauncher(host)

    build_menu_widgets(
        ftrack_menu,
        widget_launcher,
        widgets,
        event_manager,
        asset_list_model,
        created_widgets,
    )

    # Listen to client launch events
    session.event_hub.subscribe(
        'topic={} and data.pipeline.host_id={}'.format(
            core_constants.PIPELINE_CLIENT_LAUNCH, host.host_id
        ),
        functools.partial(
            _open_widget, event_manager, asset_list_model, widgets
        ),
    )

    def on_nuke_exit():
        logger.info('Shutting down ftrack integration.')
        if session.event_hub.connected:
            session.event_hub.disconnect()

    app = QtWidgets.QApplication.instance()
    app.aboutToQuit.connect(on_nuke_exit)

    nuke_utils.init_nuke()

    # Deactivating this until is available on maya.
    # Make opener automatically open when nuke is launched.
    # host.launch_client(core_constants.OPENER)


initialise()
