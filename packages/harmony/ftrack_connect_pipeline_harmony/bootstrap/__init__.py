# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import time
import os
import sys
import logging
import functools
import atexit
import uuid
import json
from functools import partial

from Qt import QtWidgets, QtCore, QtGui, QtNetwork

import ftrack_api

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.configure_logging import configure_logging

from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.asset_manager.model import AssetListModel

from ftrack_connect_pipeline_harmony import constants as harmony_constants
from ftrack_connect_pipeline_harmony import host as harmony_host
from ftrack_connect_pipeline_harmony.client import (
    menu,
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


logger = logging.getLogger('ftrack_connect_pipeline_harmony.bootstrap')

logger.info('Initializing Harmony Framework POC')

with open('/tmp/debug.txt', 'w') as f:
    f.write('\n'.join(['{}={}'.format(k, os.environ[k]) for k in list(os.environ.keys())]))

class HarmonyStandaloneApplication(QtWidgets.QApplication):

    openClient = QtCore.Signal(object)

    created_widgets = dict()

    @property
    def session_id(self):
        return self._session_id

    def __init__(self, *args, **kwargs):
        super(HarmonyStandaloneApplication, self).__init__(*args, **kwargs)
        self.openClient.connect(self._open_widget)
        self.client = None

    # def process_remote_event(host, event):
    #     logger.info('process_remote_event({})'.format(event))
    #     print('remote_launch_client_converter({})'.format(event))
    #     name = event['data']['pipeline']['name']
    #     source = event['data']['pipeline']['source']
    #     host.launch_client(name, source)
    #
    # def spawn_remote_event_listener(host, remote_event_manager, harmony_session_id):
    #
    #     logger.info('Registering remote event listener (session id: {})'.format(harmony_session_id))
    #
    #     remote_event_manager.subscribe(
    #         'ftrack.pipeline.client.launch and data.pipeline.integration_session_id={}'.format(
    #             harmony_session_id
    #         ),
    #         partial(process_remote_event, host),
    #     )

    def handle_event(self, topic, event_data, id):
        logger.info('Processing incoming event: {} ({}), data: {}'.format(topic, id, event_data))

        if topic == harmony_utils.TCPEventHubClient.TOPIC_PING:
            logger.info('Ping received')
            return
        elif topic == harmony_utils.TCPEventHubClient.TOPIC_CLIENT_LAUNCH:
            self.openClient.emit(event_data)
        elif topic == harmony_utils.TCPEventHubClient.TOPIC_SHUTDOWN:
            logger.warning('Harmony is shutting down, so will we')
            sys.exit(0)


    def send_event(self, topic, data, synchronous=False):
        return self.client.send(topic, data, synchronous=synchronous)

    def initialise(self, harmony_session_id):

        self._session_id = harmony_session_id

        logger.debug('Setting up harmony standalone integration (session id: {})...'.format(self.session_id))

        self.session = ftrack_api.Session(auto_connect_event_hub=False)

        self.event_manager = event.QEventManager(
            session=self.session, mode=core_constants.LOCAL_EVENT_MODE
        )

        self.host = harmony_host.HarmonyHost(self.event_manager)

        # Shared asset manager model
        self.asset_list_model = AssetListModel(self.event_manager)

        self.widgets = list()
        self.widgets.append(
            (
                harmony_constants.MENU_WIDGET,
                menu.HarmonyQtMenuClientWidget,
                'Menu',
                False
            )
        )
        # self.widgets.append(
        #     (
        #         core_constants.OPENER,
        #         ftrack_open.HarmonyQtOpenerClientWidget,
        #         'Open',
        #     )
        # )
        # self.widgets.append(
        #     (
        #         qt_constants.ASSEMBLER_WIDGET,
        #         load.HarmonyQtAssemblerClientWidget,
        #         'Assembler',
        #     )
        # )
        # self.widgets.append(
        #     (
        #         core_constants.ASSET_MANAGER,
        #         asset_manager.HarmonyQtAssetManagerClientWidget,
        #         'Asset Manager',
        #     )
        # )
        self.widgets.append(
            (
                core_constants.PUBLISHER,
                publish.HarmonyQtPublisherClientWidget,
                'Publisher',
                True
            )
        )
        self.widgets.append(
            (
                qt_constants.CHANGE_CONTEXT_WIDGET,
                change_context.HarmonyQtChangeContextClientWidget,
                'Change context',
                True
            )
        )
        self.widgets.append(
            (
                core_constants.LOG_VIEWER,
                log_viewer.HarmonyQtLogViewerClientWidget,
                'Log Viewer',
                True
            )
        )
        self.widgets.append(
            (
                qt_constants.DOCUMENTATION_WIDGET,
                documentation.HarmonyQtDocumentationClientWidget,
                'Documentation',
                True
            )
        )

        # Listen to widget launch events
        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                core_constants.PIPELINE_CLIENT_LAUNCH, self.host.host_id
            ),
            self._open_widget_async
        )

        #remote_event_manager = harmony_utils.init_harmony(harmony_session_id)
        #spawn_remote_event_listener(host, remote_event_manager, harmony_session_id)

        # Connect to Harmony event hub
        self.client = harmony_utils.TCPEventHubClient(
            "localhost",
            int(os.environ.get('FTRACK_INTEGRATION_LISTEN_PORT') or 56031),
            app,
            self.handle_event)

        self.client.connect()

        harmony_utils.store_client(self.client)

        # Send a ping event to Harmony to let it know we are ready
        self.send_event(harmony_utils.TCPEventHubClient.TOPIC_PING, {})

        def on_exit():
            logger.info('Harmony pipeline exit')
            self.client.close()

        atexit.register(on_exit)

    def _open_widget(self, event_data):
        '''Open Harmony widget based on widget name in *event*, and create if not already
        exists'''

        widget_name = None
        widget_class = None
        for (_widget_name, _widget_class, unused_label, unused_visible_in_menu) in self.widgets:
            if _widget_name == event_data['pipeline']['name']:
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
                    harmony_constants.MENU_WIDGET,
                ]:
                    widget = ftrack_client(self.widgets, self, event_data['pipeline'])
                elif widget_name in [
                    qt_constants.ASSEMBLER_WIDGET,
                    core_constants.ASSET_MANAGER,
                ]:
                    # Create with asset model
                    widget = ftrack_client(self.event_manager, self.asset_list_model)
                else:
                    # Create without asset model
                    widget = ftrack_client(self.event_manager)
                self.created_widgets[widget_name] = widget
            widget.show()
            widget.raise_()
            widget.activateWindow()
        else:
            raise Exception(
                'Unknown widget {}!'.format(event_data['pipeline']['name'])
            )

    def _open_widget_async(self, event):
        self.openClient.emit(event['data'])

    def checkAlive(self):
        '''Check if the client is alive'''
        if not self.client:
            logger.warning("TCP client not initialised yet")
            return
        if self.client.connection.state() in (
                QtNetwork.QAbstractSocket.SocketState.UnconnectedState,
        ):
            logger.warning("My Harmony is gone, shutting down")
            sys.exit(0)
        else:
            logger.info("Harmony is alive")

# Init QApplication
app = HarmonyStandaloneApplication()

harmony_session_id = os.environ['FTRACK_INTEGRATION_SESSION_ID']

assert (harmony_session_id), ('Harmony integration requires a FTRACK_INTEGRATION_SESSION_ID set!')
try:
    app.initialise(harmony_session_id)
except:
    import traceback
    logger.warning(traceback.format_exc())

# Enable CTRL+C
#timer = QtCore.QTimer()
#timer.timeout.connect(lambda: None)
#timer.start(100)

# Run until it's closed, or CTRL+C
active_time = 0

while True:
    app.processEvents()
    time.sleep(0.01)
    active_time += 10
    if active_time % 5000 == 0:
        app.checkAlive()

sys.exit(0)