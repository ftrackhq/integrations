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
from ftrack_utils.extensions.environment import (
    get_extensions_path_from_environment,
)
from ftrack_utils.framework.remote import get_remote_integration_session_id
from ftrack_framework_core.host import Host
from ftrack_framework_core.event import EventManager
from ftrack_framework_core.client import Client
from ftrack_framework_core import registry

from ftrack_framework_core.configure_logging import configure_logging

from ftrack_qt.utils.threading import invoke_in_qt_thread

from .rpc_cep import PhotoshopRPC
from . import process_util

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
    extra_modules=['ftrack_qt'],
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug('v{}'.format(__version__))

photoshop_connection = None

# Create Qt application
app = QtWidgets.QApplication.instance()

if not app:
    app = QtWidgets.QApplication(sys.argv)

remote_session = None

process_monitor = None


def bootstrap_integration(framework_extensions_path):
    '''Initialise Photoshop Framework Python standalone part,
    with panels defined in *panel_launchers*'''

    global photoshop_connection, remote_session, process_monitor

    logger.debug(
        'Photoshop standalone integration initialising, extensions path:'
        f' {framework_extensions_path}'
    )

    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = EventManager(
        session=session, mode=constants.event.LOCAL_EVENT_MODE
    )

    registry_instance = registry.Registry()
    registry_instance.scan_extensions(paths=framework_extensions_path)

    Host(event_manager, registry=registry_instance)

    client = Client(event_manager, registry=registry_instance)

    # Init tools
    dcc_config = registry_instance.get_one(
        name='framework-photoshop', extension_type='dcc_config'
    )

    def on_run_dialog_callback(dialog_name):
        invoke_in_qt_thread(client.run_dialog, dialog_name)

    # Init Photoshop connection
    remote_session = ftrack_api.Session(auto_connect_event_hub=True)

    photoshop_connection = PhotoshopRPC(
        remote_session.event_hub, dcc_config['tools'], on_run_dialog_callback
    )

    # Init process monitor
    process_monitor = process_util.MonitorProcess(
        photoshop_connection.photoshop_version
    )

    for _ in range(60 * 2):
        time.sleep(0.5)

        if process_monitor.check_running():
            break

    else:
        raise RuntimeError(
            f'Photoshop {photoshop_connection.photoshop_version} '
            f'({photoshop_connection.session_id}) '
            f'process never started. Shutting down.'
        )

    logger.info(
        f'Photoshop {photoshop_connection.photoshop_version} standalone '
        f'integration initialized and ready to '
        'accept incoming connect.'
    )


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
                'Integration alive has been for {}s, connected: {}'.format(
                    active_time / 1000, photoshop_connection.connected
                )
            )
        # Failsafe check if PS is still alive
        if active_time % (60 * 1000) == 0:
            if not photoshop_connection.connected:
                # Check if Photoshop still is running
                if not process_monitor.check_running():
                    logger.warning(
                        'Photoshop never connected and process gone, shutting '
                        'down!'
                    )
                    process_util.terminate_current_process()
            else:
                # Check if Photoshop panel is alive
                if not photoshop_connection.check_responding():
                    if not process_monitor.check_running():
                        logger.warning(
                            'Photoshop is not responding and process gone, '
                            'shutting down!'
                        )
                        process_util.terminate_current_process()
                    else:
                        logger.warning(
                            'Photoshop is not responding but process ({}) is still '
                            'there, panel temporarily closed?'.format(
                                process_monitor.photoshop_pid
                            )
                        )


# Find and read DCC config
bootstrap_integration(get_extensions_path_from_environment())
run_integration()
