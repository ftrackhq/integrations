# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import logging
import os
import subprocess
import time
import traceback
import platform
import sys

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

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
from ftrack_utils.session import create_api_session
from ftrack_utils.process import MonitorProcess, terminate_current_process
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread

from ftrack_framework_harmony.utils import TCPRPCClient

# How often (seconds) to check that Harmony is still running.
PROCESS_WATCHDOG_INTERVAL_SECONDS = 5


# Evaluate version and log package version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    __version__ = "0.0.0"

configure_logging(
    "ftrack_framework_harmony",
    extra_modules=["ftrack_qt"],
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug("v{}".format(__version__))

client_instance = None
harmony_tcp_connection = None
startup_tools = []
process_monitor = None
process_watchdog_timer = None

# Create Qt application
app = QtWidgets.QApplication.instance()

if not app:
    app = QtWidgets.QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_PluginApplication)

# This is a persistent standalone process that outlives individual
# dialogs: without this, closing the last dialog (e.g. the publisher)
# quits the QApplication, the process exits and its TCP connection to
# Harmony drops - so the ftrack menu would only ever open a dialog once.
# The process is instead shut down when Harmony disconnects
# (see TCPRPCClient._on_disconnected).
app.setQuitOnLastWindowClosed(False)


def on_run_tool_callback(tool_name, dialog_name=None, options=None):
    client_instance.run_tool(tool_name, dialog_name, options)


def rpc_process_events_callback():
    """Have Qt process events while waiting for RPC reply"""
    app.processEvents()


def on_connected_callback():
    """Harmony has connected, run bootstrap tools"""
    for tool in startup_tools:
        on_run_tool_callback(*tool)


def on_connection_failure_callback():
    logger.error("Could not establish connection to Harmony, exiting.")
    sys.exit(-1)


def probe_harmony_pid():
    """Return the PID of the Harmony process to monitor, or None.

    Prefers ``FTRACK_APPLICATION_PID`` (Connect sets it to the launched
    DCC's PID for the standalone helper); falls back to probing by
    process name.
    """
    expected = os.environ.get("FTRACK_APPLICATION_PID")
    if expected:
        try:
            pid = int(expected)
            os.kill(pid, 0)  # Raises OSError if the process is gone.
            return pid
        except (ValueError, OSError):
            pass

    if sys.platform in ("darwin", "linux"):
        try:
            output = subprocess.check_output(
                ["pgrep", "-f", "[Hh]armony (Premium|Advanced|Essentials)"],
                text=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
        for token in output.split():
            try:
                return int(token)
            except ValueError:
                continue
    elif sys.platform == "win32":
        try:
            output = subprocess.check_output(
                [
                    "tasklist",
                    "/FI",
                    "IMAGENAME eq Harmony*",
                    "/FO",
                    "CSV",
                    "/NH",
                ],
                text=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
        import csv
        import io

        for row in csv.reader(io.StringIO(output)):
            if len(row) >= 2:
                try:
                    return int(row[1])
                except ValueError:
                    continue
    return None


def process_watchdog_callback():
    """Terminate the standalone process when Harmony is no longer running.

    Safety net for cases where the TCP disconnect signal
    (``TCPRPCClient._on_disconnected``) does not fire - e.g. a
    half-open socket after an abrupt Harmony exit.
    """
    if process_monitor and not process_monitor.check_running():
        logger.warning("Harmony process is gone, shutting down.")
        terminate_current_process()


def bootstrap_integration(framework_extensions_path):
    """
    Initialise Harmony Framework integration
    """

    global \
        client_instance, \
        harmony_tcp_connection, \
        startup_tools, \
        process_monitor, \
        process_watchdog_timer

    logger.debug(
        "Harmony standalone integration initialising, extensions path:"
        f" {framework_extensions_path}"
    )
    # Create ftrack session and instantiate event manager
    session = create_api_session(auto_connect_event_hub=True)
    event_manager = EventManager(
        session=session, mode=constants.event.LOCAL_EVENT_MODE
    )

    logger.debug(f"framework_extensions_path:{framework_extensions_path}")

    # Instantiate registry
    registry_instance = Registry()
    registry_instance.scan_extensions(paths=framework_extensions_path)

    registry_info_dict = {
        "tool_configs": [
            item["name"] for item in registry_instance.tool_configs
        ]
        if registry_instance.tool_configs
        else [],
        "plugins": [item["name"] for item in registry_instance.plugins]
        if registry_instance.plugins
        else [],
        "engines": [item["name"] for item in registry_instance.engines]
        if registry_instance.engines
        else [],
        "widgets": [item["name"] for item in registry_instance.widgets]
        if registry_instance.widgets
        else [],
        "dialogs": [item["name"] for item in registry_instance.dialogs]
        if registry_instance.dialogs
        else [],
        "launch_configs": [
            item["name"] for item in registry_instance.launch_configs
        ]
        if registry_instance.launch_configs
        else [],
        "dcc_configs": [item["name"] for item in registry_instance.dcc_configs]
        if registry_instance.dcc_configs
        else [],
    }

    # Instantiate Host and Client
    Host(
        event_manager,
        registry=registry_instance,
        run_in_main_thread_wrapper=invoke_in_qt_main_thread,
    )
    client_instance = Client(
        event_manager,
        registry=registry_instance,
        run_in_main_thread_wrapper=invoke_in_qt_main_thread,
    )

    # Init tools
    dcc_config = registry_instance.get_one(
        name="framework-harmony", extension_type="dcc_config"
    )["extension"]

    logger.debug(f"Read DCC config: {dcc_config}")

    # Filter tools, extract the ones that are marked as startup tools
    launchers = []
    for tool in dcc_config["tools"]:
        name = tool["name"]
        run_on = tool.get("run_on")
        on_menu = tool.get("menu", True)
        dialog_name = tool.get("dialog_name")
        options = tool.get("options")

        if on_menu:
            launchers.append(tool)
        else:
            if run_on == "startup":
                startup_tools.append(
                    [
                        name,
                        dialog_name,
                        options,
                    ]
                )
            else:
                logger.error(
                    f"Unsupported run_on value: {run_on} tool section of the "
                    f"tool {tool.get('name')} on the tool config file: "
                    f"{dcc_config['name']}. \n Currently supported values:"
                    f" [startup]"
                )

    # Connect to DCC
    port = os.environ.get("FTRACK_INTEGRATION_LISTEN_PORT")
    assert port, "FTRACK_INTEGRATION_LISTEN_PORT environment variable not set"
    port = int(port)

    harmony_tcp_connection = TCPRPCClient(
        "harmony",
        "localhost",
        port,
        client_instance,
        launchers,
        on_connected_callback,
        on_run_tool_callback,
        rpc_process_events_callback,
    )

    time.sleep(2)  # Give DCC time to launch

    harmony_tcp_connection.connect_dcc(on_connection_failure_callback)

    # Monitor the Harmony process and shut down when it exits. This is
    # the reliable cleanup path - the TCP disconnect handler is the fast
    # path, this watchdog is the safety net for abrupt exits.
    process_monitor = MonitorProcess(probe_harmony_pid)
    process_monitor.check_running()  # Prime PID detection.
    process_watchdog_timer = QtCore.QTimer()
    process_watchdog_timer.timeout.connect(process_watchdog_callback)
    process_watchdog_timer.start(PROCESS_WATCHDOG_INTERVAL_SECONDS * 1000)
    logger.info(
        "Harmony process watchdog started (%ss interval).",
        PROCESS_WATCHDOG_INTERVAL_SECONDS,
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
if hasattr(app, "exec"):
    app.exec()
else:
    # PySide2 fallback
    app.exec_()
