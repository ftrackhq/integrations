# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import functools
import json
import logging
import os
import time
import uuid

import ftrack_api
import platformdirs

from ftrack_utils.version import get_connect_plugin_version

# The name of the integration, should match name in launcher.
NAME = "framework-premiere"


logger = logging.getLogger(__name__)

cwd = os.path.dirname(__file__)
connect_plugin_path = os.path.abspath(os.path.join(cwd, ".."))

# Read version number from __version__.py
__version__ = get_connect_plugin_version(connect_plugin_path)

python_dependencies = os.path.join(connect_plugin_path, "dependencies")
UXP_BOOTSTRAP_LATEST_FILENAME = "bootstrap-latest.json"


def _get_connect_user_data_dir():
    """Return ftrack Connect user data directory."""
    return platformdirs.user_data_dir("ftrack-connect", "ftrack")


def _get_uxp_bootstrap_path():
    return os.path.join(
        _get_connect_user_data_dir(),
        NAME,
        "uxp-bootstrap",
        UXP_BOOTSTRAP_LATEST_FILENAME,
    )


def _write_uxp_bootstrap_data(remote_integration_session_id, premiere_version):
    bootstrap_path = _get_uxp_bootstrap_path()
    bootstrap_folder = os.path.dirname(bootstrap_path)
    os.makedirs(bootstrap_folder, exist_ok=True)

    data = {
        "remote_integration_session_id": remote_integration_session_id,
        "premiere_version": str(premiere_version),
        "created_at": int(time.time()),
    }

    temp_bootstrap_path = f"{bootstrap_path}.tmp"

    with open(temp_bootstrap_path, "w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=True)

    os.replace(temp_bootstrap_path, bootstrap_path)

    try:
        os.chmod(bootstrap_path, 0o600)
    except OSError:
        logger.debug(
            "Could not set strict permissions on UXP bootstrap file: %s",
            bootstrap_path,
            exc_info=True,
        )

    return bootstrap_path


def on_discover_integration(session, event):
    data = {
        "integration": {
            "name": NAME,
            "version": __version__,
        }
    }

    return data


def on_launch_integration(session, event):
    """Handle application launch and add environment to *event*."""

    launch_data = {"integration": event["data"]["integration"]}

    discover_data = on_discover_integration(session, event)
    for key in discover_data["integration"]:
        launch_data["integration"][key] = discover_data["integration"][key]

    application_version = event["data"]["application"]["version"]
    if hasattr(application_version, "version"):
        integration_version = application_version.version[0]
    else:
        integration_version = int(str(application_version).split(".")[0])

    logger.info(
        f"Launching integration v{integration_version} assuming UXP plugin has "
        "been properly installed prior to launch."
    )

    if not launch_data["integration"].get("env"):
        launch_data["integration"]["env"] = {}

    launch_data["integration"]["env"]["PYTHONPATH.prepend"] = (
        os.path.pathsep.join([python_dependencies])
    )
    remote_integration_session_id = str(uuid.uuid4())
    launch_data["integration"]["env"][
        "FTRACK_REMOTE_INTEGRATION_SESSION_ID"
    ] = remote_integration_session_id

    launch_data["integration"]["env"]["FTRACK_PREMIERE_VERSION"] = str(
        integration_version
    )

    bootstrap_path = _write_uxp_bootstrap_data(
        remote_integration_session_id,
        integration_version,
    )
    launch_data["integration"]["env"]["FTRACK_PREMIERE_UXP_BOOTSTRAP_PATH"] = (
        bootstrap_path
    )
    launch_data["integration"]["env"]["FTRACK_PREMIERE_UXP_BOOTSTRAP_DIR"] = (
        os.path.dirname(bootstrap_path)
    )
    launch_data["integration"]["env"][
        "FTRACK_PREMIERE_UXP_BOOTSTRAP_LATEST_PATH"
    ] = bootstrap_path

    selection = event["data"].get("context", {}).get("selection", [])

    if selection:
        task = session.get("Context", selection[0]["entityId"])
        launch_data["integration"]["env"]["FTRACK_CONTEXTID.set"] = task["id"]

    return launch_data


def register(session):
    """Subscribe to application launch events on *registry*."""
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_integration, session
    )

    session.event_hub.subscribe(
        "topic=ftrack.connect.application.discover and "
        "data.application.identifier=premiere*"
        " and data.application.version >= 15",
        handle_discovery_event,
        priority=40,
    )

    handle_launch_event = functools.partial(on_launch_integration, session)

    session.event_hub.subscribe(
        "topic=ftrack.connect.application.launch and "
        "data.application.identifier=premiere*"
        " and data.application.version >= 15",
        handle_launch_event,
        priority=40,
    )

    logger.info(
        "Registered {} integration v{} discovery and launch.".format(
            NAME, __version__
        )
    )
