# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import logging
import time
import sys
import os

from Qt import QtWidgets, QtCore

import ftrack_api

from ftrack_constants import framework as constants
from ftrack_utils.framework.remote import get_integration_session_id
from ftrack_framework_core.host import Host
from ftrack_framework_core.event import EventManager
from ftrack_framework_core.client import Client
from ftrack_framework_core.registry import Registry

from ftrack_framework_core.configure_logging import configure_logging


# Evaluate version and log package version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    __version__ = '0.0.0'

configure_logging(
    'ftrack_framework_photoshop',
    extra_modules=["ftrack_qt"],
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug('v{}'.format(__version__))

photoshop_connection = None

# Create Qt application
app = QtWidgets.QApplication.instance()

if not app:
    app = QtWidgets.QApplication(sys.argv)


class Launcher(QtWidgets.QWidget):
    # Class for handling remote dialog and widget launch

    remote_integration_run_dialog = QtCore.Signal(
        object
    )  # Launch a tool(dialog)

    @property
    def client(self):
        return self._client

    @property
    def event_manager(self):
        return self.client.event_manager

    def __init__(self, client, parent=None):
        super(Launcher, self).__init__(parent=parent)

        self._client = client
        self.remote_integration_run_dialog.connect(
            self._remote_integration_run_dialog_callback
        )
        self.event_manager.subscribe.remote_integration_run_dialog(
            get_integration_session_id(),
            self._remote_integration_run_dialog_callback_async,
        )

    def _remote_integration_run_dialog_callback_async(self, event):
        '''Remote event callback, emit signal to run dialog in main Qt thread.'''
        self.remote_integration_run_dialog.emit(event)

    def _remote_integration_run_dialog_callback(self, event):
        '''Callback for remote integration run dialog event.'''
        self.client.run_dialog(event['data']['dialog_name'])


def bootstrap_integration(panel_launchers, extension_packages):
    '''Initialise Photoshop Framework Python standalone part,
    with panels defined in *panel_launchers*'''

    global photoshop_connection

    session = ftrack_api.Session(auto_connect_event_hub=False)

    remote_session = ftrack_api.Session(auto_connect_event_hub=True)

    event_manager = EventManager(
        session=session,
        mode=constants.event.LOCAL_EVENT_MODE,
        remote_session=remote_session,
    )

    host_registry = Registry()
    host_registry.scan_modules(
        extension_types=['plugin', 'engine', 'schema', 'tool_config'],
        package_names=extension_packages,
    )

    client_registry = Registry()
    client_registry.scan_modules(
        extension_types=['widget'], package_names=extension_packages
    )

    Host(event_manager, host_registry)

    client = Client(event_manager, client_registry)

    # Create launcher
    Launcher(client)

    # Create remote connection

    from ftrack_framework_photoshop.remote_connection.cep_connection import (
        CEPBasePhotoshopRemoteConnection,
    )

    photoshop_version = os.environ.get('FTRACK_PHOTOSHOP_VERSION')
    assert (
        photoshop_version
    ), 'Photoshop integration requires FTRACK_PHOTOSHOP_VERSION passed as environment variable!'

    photoshop_connection = CEPBasePhotoshopRemoteConnection(
        client, int(photoshop_version), panel_launchers
    )

    # Connect with Photoshop
    photoshop_connection.connect()

    # Wait for Photoshop to get ready to receive events
    time.sleep(0.5)

    # Probe and store Photoshop PID
    photoshop_connection.probe_photoshop_pid()


def run_integration():
    '''Run Photoshop Framework Python standalone part as long as Photoshop is alive.'''

    # Run until it's closed, or CTRL+C
    active_time = 0
    while True:
        app.processEvents()
        time.sleep(0.01)
        active_time += 10
        if active_time % 10000 == 0:
            logger.info(
                "Integration alive has been for {}s, connected: {}".format(
                    active_time / 1000, photoshop_connection.connected
                )
            )
        # Failsafe check if PS is still alive
        if active_time % (60 * 1000) == 0:
            if not photoshop_connection.connected:
                # Check if Photoshop still is running
                if not photoshop_connection.check_running():
                    logger.warning(
                        'Photoshop never connected and process gone, shutting down!'
                    )
                    photoshop_connection.terminate()
            else:
                # Check if Photoshop panel is alive
                if not photoshop_connection.check_responding():
                    if not photoshop_connection.check_running():
                        logger.warning(
                            'Photoshop is not responding and process gone, shutting down!'
                        )
                        photoshop_connection.terminate()
                    else:
                        logger.warning(
                            'Photoshop is not responding but process ({}) is still there, panel temporarily closed?'.format(
                                photoshop_connection.photoshop_pid
                            )
                        )
