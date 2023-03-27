# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import sys
import logging
import functools
import atexit
from functools import partial

from Qt import QtWidgets, QtCore

import ftrack_api

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.configure_logging import configure_logging

from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.asset_manager.model import AssetListModel

from ftrack_connect_pipeline_harmony import host as harmony_host
from ftrack_connect_pipeline_harmony.client import (
    open as ftrack_open,
    load,
    asset_manager,
    publish,
    change_context,
    log_viewer,
    documentation,
)

from ftrack_connect_pipeline_harmony import utils as harmony_utils

configure_logging(
    'ftrack_connect_pipeline_harmony',
    extra_modules=['ftrack_connect_pipeline', 'ftrack_connect_pipeline_qt'],
    propagate=False,
)


logger = logging.getLogger('ftrack_connect_pipeline_harmony')

logger.info('Initializing Harmony Framework POC')

class StandaloneApplication(QtWidgets.QApplication):

    openClient = QtCore.Signal(object, object, object, object)

    created_widgets = dict()

    def __init__(self, *args, **kwargs):
        super(StandaloneApplication, self).__init__(*args, **kwargs)
        self.openClient.connect(self._open_widget)


    def _open_widget(self, event_manager, asset_list_model, widgets, event):
        '''Open Harmony widget based on widget name in *event*, and create if not already
        exists'''

        widget_name = None
        widget_class = None
        for (_widget_name, _widget_class, unused_label) in widgets:
            if _widget_name == event['data']['pipeline']['name']:
                widget_name = _widget_name
                widget_class = _widget_class
                break
        if widget_name:
            ftrack_client = widget_class
            widget = None
            if widget_name in self.created_widgets:
                widget = self.created_widgets[widget_name]
                # Is it still visible?
                is_valid_and_visible = False
                try:
                    if widget is not None and widget.isVisible():
                        is_valid_and_visible = True
                except:
                    pass
                finally:
                    if not is_valid_and_visible:
                        del self.created_widgets[widget_name]  # Not active any more
                        if widget:
                            try:
                                widget.deleteLater()  # Make sure it is deleted
                            except:
                                pass
                            widget = None
            if widget is None:
                # Need to create
                if widget_name in [
                    qt_constants.ASSEMBLER_WIDGET,
                    core_constants.ASSET_MANAGER,
                ]:
                    # Create with asset model
                    widget = ftrack_client(event_manager, asset_list_model)
                else:
                    # Create without asset model
                    widget = ftrack_client(event_manager)
                self.created_widgets[widget_name] = widget
            widget.show()
            widget.raise_()
            widget.activateWindow()
        else:
            raise Exception(
                'Unknown widget {}!'.format(event['data']['pipeline']['name'])
            )


# Init QApplication
app = StandaloneApplication()


def get_ftrack_menu(menu_name='ftrack', submenu_name=None):
    '''Get the current ftrack menu, create it if does not exists.'''
    # TODO: We will send and event to photoshop to return the ftrack menu
    # gMainWindow = mm.eval('$temp1=$gMainWindow')
    #
    # if cmds.menu(menu_name, exists=True, parent=gMainWindow, label=menu_name):
    #     menu = menu_name
    #
    # else:
    #     menu = cmds.menu(
    #         menu_name, parent=gMainWindow, tearOff=True, label=menu_name
    #     )

    # if submenu_name:
        # if cmds.menuItem(
        #     submenu_name, exists=True, parent=menu, label=submenu_name
        # ):
        #     submenu = submenu_name
        # else:
        #     submenu = cmds.menuItem(
        #         submenu_name, subMenu=True, label=submenu_name, parent=menu
        #     )
    #     return submenu
    # else:
    #     return menu
    pass


def _open_widget_async(event_manager, asset_list_model, widgets, event):
    app.openClient.emit(event_manager, asset_list_model, widgets, event)

def process_remove_event(host, event):
    logger.info('remote_launch_client_converter({})'.format(event))
    print('remote_launch_client_converter({})'.format(event))
    name = event['data']['pipeline']['name']
    source = event['data']['pipeline']['source']
    host.launch_client(name, source)

def spawn_remote_event_listener(host, remote_event_manager, harmony_session_id):

    logger.info('Registering remote event listener (session id: {})'.format(harmony_session_id))

    remote_event_manager.subscribe(
        'ftrack.pipeline.client.launch and data.pipeline.session_id={}'.format(
            harmony_session_id
        ),
        partial(process_remove_event, host),
    )




def initialise(harmony_session_id):

    logger.debug('Setting up the menu')
    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = event.QEventManager(
        session=session, mode=core_constants.LOCAL_EVENT_MODE
    )

    host = harmony_host.HarmonyHost(event_manager)

    # Shared asset manager model
    asset_list_model = AssetListModel(event_manager)

    widgets = list()
    widgets.append(
        (
            core_constants.OPENER,
            ftrack_open.HarmonyQtOpenerClientWidget,
            'Open',
        )
    )
    widgets.append(
        (
            qt_constants.ASSEMBLER_WIDGET,
            load.HarmonyQtAssemblerClientWidget,
            'Assembler',
        )
    )
    widgets.append(
        (
            core_constants.ASSET_MANAGER,
            asset_manager.HarmonyQtAssetManagerClientWidget,
            'Asset Manager',
        )
    )
    widgets.append(
        (
            core_constants.PUBLISHER,
            publish.HarmonyQtPublisherClientWidget,
            'Publisher',
        )
    )
    widgets.append(
        (
            qt_constants.CHANGE_CONTEXT_WIDGET,
            change_context.HarmonyQtChangeContextClientWidget,
            'Change context',
        )
    )
    widgets.append(
        (
            core_constants.LOG_VIEWER,
            log_viewer.HarmonyQtLogViewerClientWidget,
            'Log Viewer',
        )
    )
    widgets.append(
        (
            qt_constants.DOCUMENTATION_WIDGET,
            documentation.HarmonyQtDocumentationClientWidget,
            'Documentation',
        )
    )

    ftrack_menu = get_ftrack_menu()
    # Register and hook the dialog in ftrack menu
    # for item in widgets:
        # if item == 'divider':
        #     cmds.menuItem(divider=True)
        #     continue
        #
        # widget_name, unused_widget_class, label, image = item
        #
        # cmds.menuItem(
        #     parent=ftrack_menu,
        #     label=label,
        #     command=(functools.partial(host.launch_client, widget_name)),
        #     image=":/{}.png".format(image),
        # )

    # Listen to widget launch events
    session.event_hub.subscribe(
        'topic={} and data.pipeline.host_id={}'.format(
            core_constants.PIPELINE_CLIENT_LAUNCH, host.host_id
        ),
        functools.partial(
            _open_widget_async, event_manager, asset_list_model, widgets
        ),
    )

    remote_event_manager = harmony_utils.init_harmony(harmony_session_id)
    host.remote_events_listener(remote_event_manager, harmony_session_id)


def on_exit():
    logger.info('Harmony pipeline exit')

atexit.register(on_exit)

harmony_session_id = os.environ['FTRACK_INTEGRATION_SESSION_ID']

try:
    initialise(harmony_session_id)
except:
    import traceback
    logger.warning(traceback.format_exc())

# Run until it's closed
sys.exit(app.exec_())