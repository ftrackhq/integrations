# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import logging
import time
import sys

from Qt import QtWidgets

import ftrack_api

from ._version import __version__
from ftrack_constants import framework as constants
from ftrack_framework_core.host import Host
from ftrack_framework_core.event import EventManager
from ftrack_framework_core.client import Client
from ftrack_framework_core.registry import Registry
from ftrack_framework_photoshop.rpc_cep import (
    PhotoshopRPC,
)

from ftrack_framework_core.configure_logging import configure_logging

import ftrack_qt.utils
from . import process_util

photoshop_pid = None

configure_logging(
    'ftrack_framework_photoshop',
    extra_modules=["ftrack_qt"],
    propagate=False,
)

logger = logging.getLogger('ftrack_framework_photoshop')

rpc_connection = None

# Create Qt application
app = QtWidgets.QApplication.instance()

if not app:
    app = QtWidgets.QApplication(sys.argv)

remote_session = None


def bootstrap_integration(panel_launchers, extension_packages):
    '''Initialise Photoshop Framework Python standalone part,
    with panels defined in *panel_launchers*'''

    integration_session_id = os.environ['FTRACK_INTEGRATION_SESSION_ID']

    global rpc_connection

    session = ftrack_api.Session(auto_connect_event_hub=False)

    global remote_session
    remote_session = ftrack_api.Session(auto_connect_event_hub=True)

    event_manager = EventManager(
        session=session,
        mode=constants.event.LOCAL_EVENT_MODE
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

    # TODO: Update to pass in RPC interface and allow the plugins
    # to access Photoshop in this case.
    Host(event_manager, host_registry)

    client = Client(event_manager, client_registry)

    def on_run_dialog_callback(dialog_name):
        ftrack_qt.utils.invoke_in_qt_thread(
            client.run_dialog, dialog_name
        )

    photoshop_version = os.environ.get('FTRACK_PHOTOSHOP_VERSION')
    assert (
        photoshop_version
    ), 'Photoshop integration requires FTRACK_PHOTOSHOP_VERSION passed as environment variable!'

    rpc_connection = PhotoshopRPC(
        remote_session.event_hub,
        panel_launchers,
        integration_session_id,
        on_run_dialog_callback
    )

    global monitor_process
    monitor_process = process_util.MonitorProcess(int(photoshop_version))

    for _ in range(60 * 2):
        time.sleep(0.5)

        if monitor_process.check_running():
            break

    else:
        raise RuntimeError("Photoshop process never started. Shutting down.")

    logger.info("Photoshop plugin initialized and ready to run.")


def run_integration():
    '''Run Photoshop Framework Python standalone part as long as Photoshop is alive.'''

    global remote_session

    # Run until it's closed, or CTRL+C
    active_time = 0
    while True:
        app.processEvents()
        remote_session.event_hub.wait(0.01)
        active_time += 10
        if active_time % 10000 == 0:
            logger.info(
                "Integration alive has been for {}s, connected: {}".format(
                    active_time / 1000, rpc_connection.connected
                )
            )
        # Failsafe check if PS is still alive
        if active_time % (60 * 1000) == 0:
            if not rpc_connection.connected:
                # Check if Photoshop still is running
                if not monitor_process.check_running():
                    logger.warning(
                        'Photoshop never connected and process gone, shutting down!'
                    )
                    process_util.terminate_current_process()
            else:
                # Check if Photoshop panel is alive
                if not rpc_connection.check_responding():
                    if not monitor_process.check_running():
                        logger.warning(
                            'Photoshop is not responding and process gone, shutting down!'
                        )
                        process_util.terminate_current_process()
                    else:
                        logger.warning(
                            'Photoshop is not responding but process ({}) is still there, panel temporarily closed?'.format(
                                monitor_process.photoshop_pid
                            )
                        )
