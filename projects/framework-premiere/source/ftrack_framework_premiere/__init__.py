# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import logging
import time
import sys
import os
import traceback
import platform
import subprocess
import zipfile
from functools import partial

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

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

from ftrack_utils.session import create_api_session


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
    "ftrack_framework_premiere",
    extra_modules=["ftrack_qt"],
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug("v{}".format(__version__))

client_instance = None
premiere_rpc_connection = None
startup_tools = []
session = None
process_monitor = None
process_watchdog_timer = None
integration_alive_seconds = 0
last_panel_healthcheck_timestamp = 0.0
launcher_expected_premiere_pid = None
launcher_expected_application_path = None
launcher_expected_pid_fallback_logged = False
launcher_expected_path_fallback_logged = False

PROCESS_WATCHDOG_INTERVAL_SECONDS = 5
PANEL_HEALTHCHECK_INTERVAL_SECONDS = 20
PANEL_HEALTHCHECK_TIMEOUT_MS = 2000


# Create Qt application
if hasattr(QtCore.Qt, "AA_PluginApplication"):
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_PluginApplication)

app = QtWidgets.QApplication.instance()

if not app:
    app = QtWidgets.QApplication(sys.argv)


def _get_application_icon():
    """Return icon for Premiere standalone helper app, if available."""
    package_root = os.path.abspath(os.path.dirname(__file__))
    package_candidates = [
        os.path.join(package_root, "resources", "ftrack-logo-96.png"),
        os.path.join(package_root, "resources", "ftrack-logo-48.png"),
    ]

    for candidate in package_candidates:
        if os.path.isfile(candidate):
            icon = QtGui.QIcon(candidate)
            if icon.isNull():
                logger.debug(
                    "Packaged helper icon exists but failed to load: %s",
                    candidate,
                )
                continue
            logger.info(
                "Using packaged helper icon: %s",
                candidate,
            )
            return icon

    integration_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )

    ccx_files = sorted(
        [
            filename
            for filename in os.listdir(integration_root)
            if filename.lower().endswith(".ccx")
        ]
    )

    for ccx_filename in reversed(ccx_files):
        ccx_path = os.path.join(integration_root, ccx_filename)
        try:
            with zipfile.ZipFile(ccx_path, "r") as archive:
                for ccx_icon_path in [
                    "icons/ftrack-logo-96.png",
                    "icons/ftrack-logo-48.png",
                ]:
                    try:
                        icon_data = archive.read(ccx_icon_path)
                    except KeyError:
                        continue

                    pixmap = QtGui.QPixmap()
                    if not pixmap.loadFromData(icon_data):
                        logger.debug(
                            "Failed loading helper icon bytes from CCX asset:"
                            " %s in %s",
                            ccx_icon_path,
                            ccx_path,
                        )
                        continue

                    icon = QtGui.QIcon(pixmap)
                    if icon.isNull():
                        continue

                    logger.info(
                        "Using helper icon loaded from CCX asset: %s in %s",
                        ccx_icon_path,
                        ccx_path,
                    )
                    return icon
        except Exception:
            logger.debug(
                "Failed reading icon assets from CCX: %s",
                ccx_path,
                exc_info=True,
            )

    return None


def _configure_application_identity():
    """Set standalone process app icon metadata."""

    icon = _get_application_icon()
    if icon and not icon.isNull():
        app.setWindowIcon(icon)
        logger.info("Applied helper app icon.")
    else:
        logger.warning(
            "No helper icon asset found, using default Python icon."
        )


_configure_application_identity()


@invoke_in_qt_main_thread
def on_run_tool_callback(tool_name, dialog_name=None, options=None):
    client_instance.run_tool(
        tool_name,
        dialog_name,
        options,
    )


@invoke_in_qt_main_thread
def on_connected_callback(event):
    """Premiere has connected, run bootstrap tools"""
    for tool in startup_tools:
        on_run_tool_callback(*tool)


def rpc_process_events_callback():
    """Have Qt process events while waiting for RPC reploy"""
    app.processEvents()


def process_watchdog_callback():
    """Check Premiere process + panel responsiveness periodically."""
    global integration_alive_seconds
    global last_panel_healthcheck_timestamp

    integration_alive_seconds += PROCESS_WATCHDOG_INTERVAL_SECONDS
    if integration_alive_seconds % 40 == 0:
        logger.info(
            f"Integration alive has been for {integration_alive_seconds}s, "
            f"connected: {premiere_rpc_connection.connected}"
        )

    # Check if Premiere still is running
    if not process_monitor.check_running():
        logger.warning("Premiere process gone, shutting down!")
        terminate_current_process()
        return

    now = time.monotonic()
    if (
        now - last_panel_healthcheck_timestamp
        < PANEL_HEALTHCHECK_INTERVAL_SECONDS
    ):
        return

    last_panel_healthcheck_timestamp = now

    # Check if Premiere panel is alive
    check_start = time.perf_counter()
    respond_result = premiere_rpc_connection.check_responding(
        timeout_ms=PANEL_HEALTHCHECK_TIMEOUT_MS,
    )
    check_elapsed_ms = int((time.perf_counter() - check_start) * 1000)
    logger.debug(
        "Premiere panel healthcheck result=%s elapsed=%sms timeout=%sms",
        respond_result,
        check_elapsed_ms,
        PANEL_HEALTHCHECK_TIMEOUT_MS,
    )
    if not respond_result and premiere_rpc_connection.connected:
        premiere_rpc_connection.connected = False
        logger.info(
            f"Premiere is not responding but process ({process_monitor.process_pid}) "
            "is still there, panel temporarily closed?"
        )
    elif respond_result and not premiere_rpc_connection.connected:
        premiere_rpc_connection.connected = True
        logger.info("Premiere is responding again, panel alive.")


def _extract_launcher_expected_pid():
    """Return launcher provided PID hint, if available and valid."""
    raw_pid = os.environ.get("FTRACK_APPLICATION_PID")
    if not raw_pid:
        return None

    try:
        pid = int(raw_pid)
    except (TypeError, ValueError):
        logger.warning("Invalid FTRACK_APPLICATION_PID value: %s", raw_pid)
        return None

    if pid <= 0:
        logger.warning(
            "Ignoring non-positive FTRACK_APPLICATION_PID value: %s", raw_pid
        )
        return None

    return pid


def _extract_launcher_expected_application_path():
    """Return launcher provided application path hint, if available."""
    raw_path = os.environ.get("FTRACK_APPLICATION_PATH")
    if not raw_path:
        return None

    normalized_path = os.path.normpath(os.path.abspath(str(raw_path)))
    if not normalized_path:
        return None

    return normalized_path


def _is_matching_macos_application_path(command, expected_application_path):
    """Return True when macOS process command resolves under app bundle path."""
    if not expected_application_path:
        return False

    app_bundle_marker = ".app"
    expected_bundle_path = expected_application_path
    expected_marker_index = expected_bundle_path.lower().find(
        app_bundle_marker
    )
    if expected_marker_index > -1:
        expected_bundle_path = expected_bundle_path[
            : expected_marker_index + len(app_bundle_marker)
        ]

    normalized_expected_bundle_path = os.path.normcase(
        os.path.normpath(expected_bundle_path)
    )

    normalized_command = command.strip().replace("\\ ", " ")
    if not normalized_command:
        return False

    return normalized_expected_bundle_path in os.path.normcase(
        normalized_command
    )


def _is_matching_premiere_pid(pid, premiere_version):
    """Return True if *pid* appears to be the expected Premiere process."""
    try:
        if sys.platform == "darwin":
            command = (
                subprocess.check_output(
                    ["ps", "-p", str(pid), "-o", "command="],
                )
                .decode("utf-8", errors="ignore")
                .strip()
            )

            expected_command_fragment = (
                f"MacOS/Adobe Premiere Pro {str(premiere_version)}"
            )
            if expected_command_fragment in command:
                return True

            return "MacOS/Adobe Premiere Pro" in command

        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            output = subprocess.check_output(
                ["TASKLIST", "/FI", f"PID eq {pid}"],
                startupinfo=startupinfo,
            ).decode("cp850", errors="ignore")

            return (
                "Adobe Premiere Pro.exe" in output
                or "Premiere Pro.exe" in output
                or "Premiere.exe" in output
            )

    except Exception:
        return False

    return False


def _iter_mac_processes():
    """Yield ``(pid, command)`` tuples from macOS ``ps`` output."""

    output = subprocess.check_output(
        ["ps", "-axo", "pid=,command="],
    ).decode("utf-8", errors="ignore")

    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue

        pid_text, _, command = line.partition(" ")
        if not command:
            continue

        try:
            pid = int(pid_text)
        except ValueError:
            continue

        yield pid, command.strip()


def probe_premiere_pid(
    premiere_version,
    expected_pid=None,
    expected_application_path=None,
):
    """
    Probe the Premiere PID based on the version for the process monitor.

    :param premiere_version: The version of Premiere to probe, e.g. '2024' and so on
    :return: The detected PID or None if not found
    """
    global launcher_expected_pid_fallback_logged
    global launcher_expected_path_fallback_logged

    if expected_pid:
        if _is_matching_premiere_pid(expected_pid, premiere_version):
            logger.debug("Probe matched launcher PID hint: %s", expected_pid)
            return expected_pid

        if not launcher_expected_pid_fallback_logged:
            logger.warning(
                "Launcher provided PID hint (%s) did not match Premiere process. "
                "Falling back to executable probe.",
                expected_pid,
            )
            launcher_expected_pid_fallback_logged = True

    if sys.platform == "darwin" and expected_application_path:
        for pid, command in _iter_mac_processes():
            if _is_matching_macos_application_path(
                command,
                expected_application_path,
            ):
                logger.info(
                    "Matched Premiere process by application path hint: pid=%s path=%s",
                    pid,
                    expected_application_path,
                )
                return pid

        if not launcher_expected_path_fallback_logged:
            logger.warning(
                "Launcher provided application path hint (%s) did not match "
                "a running process. Falling back to executable probe.",
                expected_application_path,
            )
            launcher_expected_path_fallback_logged = True

    if sys.platform == "darwin":
        PS_EXECUTABLE = f"Adobe Premiere Pro {str(premiere_version)}"
        logger.info(f"Probing Mac PID (executable: {PS_EXECUTABLE})")

        expected_command_fragments = [
            f"MacOS/{PS_EXECUTABLE}",
            "MacOS/Adobe Premiere Pro",
        ]
        for pid, command in _iter_mac_processes():
            if any(
                fragment in command for fragment in expected_command_fragments
            ):
                logger.info(f"Found pid: {pid}.")
                return pid

    elif sys.platform == "win32":
        executable_names = [
            "Adobe Premiere Pro.exe",
            "Premiere Pro.exe",
            "Premiere.exe",
        ]
        logger.info(
            "Probing Windows PID (executables: {}).".format(
                ", ".join(executable_names)
            )
        )

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        for line in (
            subprocess.check_output(["TASKLIST"], startupinfo=startupinfo)
            .decode("cp850")
            .split("\n")
        ):
            if any(name in line for name in executable_names):
                tokens = line.split()
                if len(tokens) > 1:
                    try:
                        pid = int(tokens[1])
                    except ValueError:
                        continue
                    logger.info(f"Found pid: {pid}.")
                    return pid

    logger.warning("Premiere not found running!")
    return None


def bootstrap_integration(framework_extensions_path):
    """Initialise Premiere Framework Python standalone part,
    with panels defined in *panel_launchers*"""

    global \
        client_instance, \
        premiere_rpc_connection, \
        startup_tools, \
        session, \
        process_monitor, \
        process_watchdog_timer, \
        last_panel_healthcheck_timestamp, \
        launcher_expected_premiere_pid, \
        launcher_expected_application_path, \
        launcher_expected_pid_fallback_logged, \
        launcher_expected_path_fallback_logged

    logger.debug(
        "Premiere standalone integration initialising, extensions path:"
        f" {framework_extensions_path}"
    )

    session = create_api_session(auto_connect_event_hub=True)

    event_manager = EventManager(
        session=session, mode=constants.event.LOCAL_EVENT_MODE
    )

    registry_instance = registry.Registry()
    registry_instance.scan_extensions(paths=framework_extensions_path)

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
        name="framework-premiere", extension_type="dcc_config"
    )["extension"]

    logger.debug(f"Read DCC config: {dcc_config}")

    # Filter tools, extract the ones that are marked as startup tools
    panel_launchers = []
    for tool in dcc_config["tools"]:
        name = tool["name"]
        run_on = tool.get("run_on")
        on_menu = tool.get("menu", True)
        dialog_name = tool.get("dialog_name")
        options = tool.get("options")

        if on_menu:
            panel_launchers.append(tool)
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
    premiere_rpc_connection = JavascriptRPC(
        "premiere",
        session,
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

    # Set mix panel event
    set_usage_tracker(
        UsageTracker(
            session=session,
            default_data=dict(
                app="Premiere",
                registry=registry_info_dict,
                version=__version__,
                app_version=premiere_rpc_connection.dcc_version,
                os=platform.platform(),
            ),
        )
    )

    # Init process monitor
    launcher_expected_premiere_pid = _extract_launcher_expected_pid()
    launcher_expected_application_path = (
        _extract_launcher_expected_application_path()
    )
    last_panel_healthcheck_timestamp = 0.0
    launcher_expected_pid_fallback_logged = False
    launcher_expected_path_fallback_logged = False

    if launcher_expected_premiere_pid:
        logger.info(
            "Using launcher provided Premiere PID hint: %s",
            launcher_expected_premiere_pid,
        )

    if launcher_expected_application_path:
        logger.info(
            "Using launcher provided Premiere application path hint: %s",
            launcher_expected_application_path,
        )

    logger.info(
        "Premiere watchdog probe config: version=%s, expected_pid=%s, "
        "expected_application_path=%s, session_id=%s",
        premiere_rpc_connection.dcc_version,
        launcher_expected_premiere_pid,
        launcher_expected_application_path,
        premiere_rpc_connection.remote_integration_session_id,
    )

    process_monitor = MonitorProcess(
        partial(
            probe_premiere_pid,
            premiere_rpc_connection.dcc_version,
            launcher_expected_premiere_pid,
            launcher_expected_application_path,
        )
    )

    for _ in range(30 * 2):  # Wait 30s for Premiere to connect
        time.sleep(0.5)

        if process_monitor.check_running():
            break

        logger.debug("Still waiting for Premiere to launch")

    else:
        raise RuntimeError(
            f"Premiere {premiere_rpc_connection.remote_integration_session_id} "
            f"({premiere_rpc_connection.remote_integration_session_id}) "
            "process never started. Shutting down."
        )

    logger.warning(
        f"Premiere {premiere_rpc_connection.dcc_version} standalone "
        "integration initialized and ready and awaiting connection from"
        " Premiere."
    )

    process_watchdog_timer = QtCore.QTimer()
    process_watchdog_timer.timeout.connect(process_watchdog_callback)
    process_watchdog_timer.start(PROCESS_WATCHDOG_INTERVAL_SECONDS * 1000)
    logger.info(
        "Premiere process watchdog started with %ss interval.",
        PROCESS_WATCHDOG_INTERVAL_SECONDS,
    )


def run_integration():
    """Run Premiere Framework Python standalone as long as Premiere is alive."""

    global session

    # Run until it's closed, or CTRL+C
    while True:
        app.processEvents()
        session.event_hub.wait(0.01)


# Find and read DCC config
try:
    bootstrap_integration(get_extensions_path_from_environment())
    run_integration()
except:
    # Make sure any exception that happens are logged as there is most likely no console
    logger.error(traceback.format_exc())
    raise
