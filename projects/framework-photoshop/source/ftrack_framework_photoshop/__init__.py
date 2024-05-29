# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import logging
import time
import sys
import os
import traceback
import platform
import subprocess
import re
from functools import partial

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

import ftrack_api

from ftrack_constants import framework as constants

from ftrack_utils.extensions.environment import (
    get_extensions_path_from_environment,
)
from ftrack_utils.rpc import JavascriptRPC
from ftrack_utils.process import MonitorProcess, terminate_current_process
from ftrack_utils.usage import set_usage_tracker, UsageTracker
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread


from ftrack_framework_core.host import Host
from ftrack_framework_core.event import EventManager
from ftrack_framework_core.client import Client
from ftrack_framework_core.configure_logging import configure_logging
from ftrack_framework_core import registry


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

client_instance = None
photoshop_rpc_connection = None
startup_tools = []
remote_session = None
process_monitor = None

# Create Qt application
app = QtWidgets.QApplication.instance()

if not app:
    app = QtWidgets.QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_PluginApplication)


@invoke_in_qt_main_thread
def on_run_tool_callback(tool_name, dialog_name=None, options=dict):
    client_instance.run_tool(tool_name, dialog_name, options)


@invoke_in_qt_main_thread
def on_connected_callback(event):
    '''Photoshop has connected, run bootstrap tools'''
    for tool in startup_tools:
        on_run_tool_callback(*tool)


def rpc_process_events_callback():
    '''Have Qt process events while waiting for RPC reploy'''
    app.processEvents()


def probe_photoshop_pid(photoshop_version):
    '''
    Probe the Photoshop PID based on the version for the process monitor.

    :param photoshop_version: The version of Photoshop to probe, e.g. '2024' and so on
    :return: The detected PID or None if not found
    '''
    if sys.platform == 'darwin':
        PS_EXECUTABLE = f'Adobe Photoshop {str(photoshop_version)}'
        logger.info(f'Probing Mac PID (executable: {PS_EXECUTABLE})')

        for line in (
            subprocess.check_output(['ps', '-ef']).decode('utf-8').split('\n')
        ):
            if line.find(f'MacOS/{PS_EXECUTABLE}') > -1:
                # Expect:
                #   501 21270     1   0  3:05PM ??         0:36.85 /Applications/Adobe Photoshop 2022/Adobe Photoshop 2022.app/Contents/MacOS/Adobe Photoshop 2022
                pid = int(re.split(' +', line)[2])
                logger.info(f'Found pid: {pid}.')
                return pid

    elif sys.platform == 'win32':
        PS_EXECUTABLE = 'Photoshop.exe'
        logger.info(f'Probing Windows PID (executable: {PS_EXECUTABLE}).')

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        for line in (
            subprocess.check_output(['TASKLIST'], startupinfo=startupinfo)
            .decode('cp850')
            .split('\n')
        ):
            if line.find(PS_EXECUTABLE) > -1:
                # Expect:
                #   Photoshop.exe                15364 Console                    1  2 156 928 K
                pid = int(re.split(' +', line)[1])
                logger.info(f'Found pid: {pid}.')
                return pid

    logger.warning('Photoshop not found running!')
    return None


def bootstrap_integration(framework_extensions_path):
    '''Initialise Photoshop Framework Python standalone part,
    with extensions defined @ *framework_extensions_path*'''

    global client_instance, photoshop_rpc_connection, startup_tools, remote_session, process_monitor

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

    client_instance = Client(event_manager, registry=registry_instance)

    # Init tools
    dcc_config = registry_instance.get_one(
        name='framework-photoshop', extension_type='dcc_config'
    )['extension']

    logger.debug(f'Read DCC config: {dcc_config}')

    # Init Photoshop connection
    remote_session = ftrack_api.Session(auto_connect_event_hub=True)

    # Filter tools, extract the ones that are marked as startup tools
    panel_launchers = []
    for tool in dcc_config['tools']:
        name = tool['name']
        on_menu = tool.get("menu", True)
        dialog_name = tool.get('dialog_name')
        options = tool.get('options')

        if on_menu:
            panel_launchers.append(tool)
        else:
            startup_tools.append(
                [
                    name,
                    dialog_name,
                    options,
                ]
            )
    photoshop_rpc_connection = JavascriptRPC(
        'photoshop',
        remote_session,
        client_instance,
        panel_launchers,
        on_connected_callback,
        on_run_tool_callback,
        rpc_process_events_callback,
    )

    # TODO: clean up this dictionary creation or move it as a query function of
    #  the registry.
    # Create a registry dictionary with all extension names to pass to the mix panel event
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

    # Set mix panel event
    set_usage_tracker(
        UsageTracker(
            session=session,
            default_data=dict(
                app="Photoshop",
                registry=registry_info_dict,
                version=__version__,
                app_version=photoshop_rpc_connection.dcc_version,
                os=platform.platform(),
            ),
        )
    )

    # Init process monitor
    process_monitor = MonitorProcess(
        partial(probe_photoshop_pid, photoshop_rpc_connection.dcc_version)
    )

    for _ in range(30 * 2):  # Wait 30s for Photoshop to connect
        time.sleep(0.5)

        if process_monitor.check_running():
            break

        logger.debug("Still waiting for Photoshop to launch")

    else:
        raise RuntimeError(
            'Photoshop {photoshop_rpc_connection.photoshop_version} '
            f'({photoshop_rpc_connection.remote_integration_session_id}) '
            'process never started. Shutting down.'
        )

    logger.warning(
        f'Photoshop {photoshop_rpc_connection.dcc_version} standalone '
        'integration initialized and ready and awaiting connection from'
        ' Photoshop.'
    )


def run_integration():
    '''Run Framework Python standalone as long as Photoshop is alive.'''

    global remote_session

    # Run until it's closed, or CTRL+C
    active_time = 0
    while True:
        app.processEvents()
        remote_session.event_hub.wait(0.01)
        active_time += 10
        if active_time % 10000 == 0:
            logger.info(
                f'Integration alive has been for {active_time / 1000}s, '
                f'connected: {photoshop_rpc_connection.connected}'
            )
        # Failsafe check if PS is still alive every 5s
        if active_time % (5 * 1000) == 0:
            # Check if Photoshop still is running
            if not process_monitor.check_running():
                logger.warning('Photoshop process gone, shutting ' 'down!')
                terminate_current_process()
            else:
                # Check if Photoshop panel is alive
                respond_result = photoshop_rpc_connection.check_responding()
                if not respond_result and photoshop_rpc_connection.connected:
                    photoshop_rpc_connection.connected = False
                    logger.info(
                        f'Photoshop is not responding but process ({process_monitor.process_pid}) '
                        f'is still there, panel temporarily closed?'
                    )
                elif respond_result and not photoshop_rpc_connection.connected:
                    photoshop_rpc_connection.connected = True
                    logger.info('Photoshop is responding again, panel alive.')


# Find and read DCC config
try:
    bootstrap_integration(get_extensions_path_from_environment())
    run_integration()
except:
    # Make sure any exception that happens are logged as there is most likely no console
    logger.error(traceback.format_exc())
    raise
