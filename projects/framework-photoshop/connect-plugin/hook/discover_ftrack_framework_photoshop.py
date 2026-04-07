# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os
import json
import time
import ftrack_api
import logging
import functools
import uuid

from ftrack_utils.version import get_connect_plugin_version

# The name of the integration, should match name in launcher.
NAME = "framework-photoshop"


logger = logging.getLogger(__name__)

cwd = os.path.dirname(__file__)
connect_plugin_path = os.path.abspath(os.path.join(cwd, ".."))

# Read version number from __version__.py
__version__ = get_connect_plugin_version(connect_plugin_path)

python_dependencies = os.path.join(connect_plugin_path, "dependencies")

UXP_BOOTSTRAP_FOLDER = os.path.join(
    os.path.expanduser("~"),
    ".ftrack",
    "framework-photoshop",
    "uxp-bootstrap",
)
UXP_BOOTSTRAP_FILE_PREFIX = "bootstrap-"
UXP_BOOTSTRAP_LATEST_FILENAME = "bootstrap-latest.json"
UXP_BOOTSTRAP_MAX_AGE_SECONDS = 24 * 60 * 60


def _cleanup_stale_uxp_bootstrap_files():
    """Remove stale UXP bootstrap files."""
    if not os.path.isdir(UXP_BOOTSTRAP_FOLDER):
        return

    now = time.time()
    for filename in os.listdir(UXP_BOOTSTRAP_FOLDER):
        if not filename.startswith(UXP_BOOTSTRAP_FILE_PREFIX):
            continue
        if not filename.endswith(".json"):
            continue

        path = os.path.join(UXP_BOOTSTRAP_FOLDER, filename)
        try:
            age = now - os.path.getmtime(path)
            if age > UXP_BOOTSTRAP_MAX_AGE_SECONDS:
                os.remove(path)
        except OSError:
            logger.warning(
                "Failed removing stale UXP bootstrap file: %s", path
            )


def _write_uxp_bootstrap_data(session, launch_data, photoshop_version):
    """Write UXP bootstrap data to disk and return the bootstrap path."""
    _cleanup_stale_uxp_bootstrap_files()

    os.makedirs(UXP_BOOTSTRAP_FOLDER, exist_ok=True)

    remote_integration_session_id = launch_data["integration"]["env"][
        "FTRACK_REMOTE_INTEGRATION_SESSION_ID"
    ]

    bootstrap_data = {
        "server_url": getattr(session, "server_url", None)
        or os.environ.get("FTRACK_SERVER"),
        "api_user": getattr(session, "api_user", None)
        or os.environ.get("FTRACK_API_USER"),
        "api_key": getattr(session, "api_key", None)
        or os.environ.get("FTRACK_API_KEY"),
        "remote_integration_session_id": remote_integration_session_id,
        "photoshop_version": str(photoshop_version),
        "created_at": int(time.time()),
    }

    missing = [
        key
        for key in (
            "server_url",
            "api_user",
            "api_key",
            "remote_integration_session_id",
        )
        if not bootstrap_data.get(key)
    ]
    if missing:
        raise RuntimeError(
            "Missing values required for UXP bootstrap data: {}".format(
                ", ".join(missing)
            )
        )

    filename = (
        f"{UXP_BOOTSTRAP_FILE_PREFIX}{remote_integration_session_id}.json"
    )
    bootstrap_path = os.path.join(UXP_BOOTSTRAP_FOLDER, filename)
    latest_bootstrap_path = os.path.join(
        UXP_BOOTSTRAP_FOLDER, UXP_BOOTSTRAP_LATEST_FILENAME
    )

    with open(bootstrap_path, "w", encoding="utf-8") as handle:
        json.dump(bootstrap_data, handle)

    with open(latest_bootstrap_path, "w", encoding="utf-8") as handle:
        json.dump(bootstrap_data, handle)

    try:
        os.chmod(bootstrap_path, 0o600)
        os.chmod(latest_bootstrap_path, 0o600)
    except OSError:
        logger.warning(
            "Could not set strict permissions on UXP bootstrap files: %s and %s",
            bootstrap_path,
            latest_bootstrap_path,
        )

    logger.info(
        "Wrote Photoshop UXP bootstrap file for session %s: %s",
        remote_integration_session_id,
        bootstrap_path,
    )
    logger.info(
        "Updated Photoshop UXP latest bootstrap file: %s",
        latest_bootstrap_path,
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
        photoshop_version = application_version.version[0]
    else:
        photoshop_version = int(str(application_version).split(".")[0])

    logger.info(
        "Preparing Photoshop launch using the UXP integration bootstrap flow"
    )

    if not launch_data["integration"].get("env"):
        launch_data["integration"]["env"] = {}

    launch_data["integration"]["env"]["PYTHONPATH.prepend"] = (
        os.path.pathsep.join([python_dependencies])
    )
    launch_data["integration"]["env"][
        "FTRACK_REMOTE_INTEGRATION_SESSION_ID"
    ] = str(uuid.uuid4())
    launch_data["integration"]["env"]["FTRACK_PHOTOSHOP_VERSION"] = str(
        photoshop_version
    )

    bootstrap_path = _write_uxp_bootstrap_data(
        session, launch_data, photoshop_version
    )
    launch_data["integration"]["env"][
        "FTRACK_PHOTOSHOP_UXP_BOOTSTRAP_PATH"
    ] = bootstrap_path
    launch_data["integration"]["env"]["FTRACK_PHOTOSHOP_UXP_BOOTSTRAP_DIR"] = (
        UXP_BOOTSTRAP_FOLDER
    )
    launch_data["integration"]["env"][
        "FTRACK_PHOTOSHOP_UXP_BOOTSTRAP_LATEST_PATH"
    ] = os.path.join(UXP_BOOTSTRAP_FOLDER, UXP_BOOTSTRAP_LATEST_FILENAME)

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
        "data.application.identifier=photoshop*"
        " and data.application.version >= 2014",
        handle_discovery_event,
        priority=40,
    )

    handle_launch_event = functools.partial(on_launch_integration, session)

    session.event_hub.subscribe(
        "topic=ftrack.connect.application.launch and "
        "data.application.identifier=photoshop*"
        " and data.application.version >= 2014",
        handle_launch_event,
        priority=40,
    )

    logger.info(
        "Registered {} integration v{} discovery and launch.".format(
            NAME, __version__
        )
    )
