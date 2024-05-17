# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import logging
import os
import time
import traceback
import platform
import sys
from functools import partial

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

import ftrack_api

from ftrack_framework_core.host import Host
from ftrack_framework_core.event import EventManager
from ftrack_framework_core.client import Client
from ftrack_framework_core.registry import Registry
from ftrack_framework_core.configure_logging import configure_logging

from ftrack_constants import framework as constants

from ftrack_utils.extensions.environment import (
    get_extensions_path_from_environment,
)

from ftrack_utils.usage import set_usage_tracker, UsageTracker

from ftrack_framework_harmony.utils import TCPRPCClient


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
    'ftrack_framework_harmony',
    extra_modules=['ftrack_qt'],
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug('v{}'.format(__version__))

harmony_tcp_connection = None
process_monitor = None

# Create Qt application
app = QtWidgets.QApplication.instance()

if not app:
    app = QtWidgets.QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_PluginApplication)


def on_run_dialog_callback(client_instance, dialog_name, tool_config_names):
    client_instance.run_dialog(
        dialog_name,
        dialog_options={'tool_config_names': tool_config_names},
    )


def handle_event_callback(event):
    pass


def rpc_process_events_callback():
    '''Have Qt process events while waiting for RPC reply'''
    app.processEvents()


def on_connect_callback():
    pass


def on_connection_failure_callback():
    logger.error(f'Could not establish connection to Harmony, exiting.')
    sys.exit(-1)


def bootstrap_integration(framework_extensions_path):
    '''
    Initialise Harmony Framework integration
    '''

    global harmony_tcp_connection, process_monitor

    logger.debug(
        'Harmony standalone integration initialising, extensions path:'
        f' {framework_extensions_path}'
    )
    # Create ftrack session and instantiate event manager
    session = ftrack_api.Session(auto_connect_event_hub=False)
    event_manager = EventManager(
        session=session, mode=constants.event.LOCAL_EVENT_MODE
    )

    logger.debug(f"framework_extensions_path:{framework_extensions_path}")

    # Instantiate registry
    registry_instance = Registry()
    registry_instance.scan_extensions(paths=framework_extensions_path)

    registry_info_dict = {
        'tool_configs': [
            item['name'] for item in registry_instance.tool_configs
        ]
        if registry_instance.tool_configs
        else [],
        'plugins': [item['name'] for item in registry_instance.plugins]
        if registry_instance.plugins
        else [],
        'engines': [item['name'] for item in registry_instance.engines]
        if registry_instance.engines
        else [],
        'widgets': [item['name'] for item in registry_instance.widgets]
        if registry_instance.widgets
        else [],
        'dialogs': [item['name'] for item in registry_instance.dialogs]
        if registry_instance.dialogs
        else [],
        'launch_configs': [
            item['name'] for item in registry_instance.launch_configs
        ]
        if registry_instance.launch_configs
        else [],
        'dcc_configs': [item['name'] for item in registry_instance.dcc_configs]
        if registry_instance.dcc_configs
        else [],
    }

    # Instantiate Host and Client
    Host(event_manager, registry=registry_instance)
    client_instance = Client(event_manager, registry=registry_instance)

    # Init tools
    dcc_config = registry_instance.get_one(
        name='framework-harmony', extension_type='dcc_config'
    )['extension']

    logger.debug(f'Read DCC config: {dcc_config}')

    # Connect to DCC

    port = int(os.environ.get('FTRACK_INTEGRATION_LISTEN_PORT'))
    assert port, 'FTRACK_INTEGRATION_LISTEN_PORT environment variable not set'

    harmony_tcp_connection = TCPRPCClient(
        "harmony",
        "localhost",
        port,
        client_instance,
        dcc_config['tools'],
        partial(on_run_dialog_callback, client_instance),
        rpc_process_events_callback,
    )

    time.sleep(2)  # Give DCC time to launch

    harmony_tcp_connection.connect_dcc(
        on_connect_callback, on_connection_failure_callback
    )

    # Set mix panel event
    set_usage_tracker(
        UsageTracker(
            session=session,
            default_data=dict(
                app="Harmony",
                registry=registry_info_dict,
                version=__version__,
                app_version=harmony_tcp_connection.dcc_version,
                os=platform.platform(),
            ),
        )
    )

    return client_instance


# Find and read DCC config
try:
    bootstrap_integration(get_extensions_path_from_environment())
except:
    # Make sure any exception that happens are logged as there is most likely no console
    logger.error(traceback.format_exc())
    raise

# Run the application
app.exec_()
