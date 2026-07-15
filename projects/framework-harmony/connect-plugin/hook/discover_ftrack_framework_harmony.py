# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import ftrack_api
import logging
import functools
import sys
import re
import shutil
import random
import socket
import tempfile
import uuid

from ftrack_utils.version import get_connect_plugin_version


# The name of the integration, should match name in launcher.
NAME = "framework-harmony"


logger = logging.getLogger(__name__)

cwd = os.path.dirname(__file__)
connect_plugin_path = os.path.abspath(os.path.join(cwd, ".."))

# Read version number from __version__.py
try:
    __version__ = get_connect_plugin_version(connect_plugin_path)
except FileNotFoundError:
    # __version__.py is generated at build time; fall back when the hook
    # is imported from the source tree (e.g. by the tests).
    __version__ = "0.0.0"

python_dependencies = os.path.join(connect_plugin_path, "dependencies")


def on_discover_integration(session, event):
    data = {
        "integration": {
            "name": NAME,
            "version": __version__,
        }
    }

    return data


def check_port(port, host="localhost"):
    """
    Check if a port is free to use or not.

    :param port: The port to check.
    :param host: The host to check the port on.
    :return: True if the port is in use, False if it is free.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)  # Timeout in case the socket server does not respond

    try:
        sock.connect((host, port))
        sock.close()
        return False
    except (socket.timeout, ConnectionRefusedError, OSError):
        return True


# Name of the bundled blank scene folder (and its .xstage basename), staged
# per launch so Harmony boots straight into it. See stage_bootstrap_scene.
BOOTSTRAP_SCENE_NAME = "ftrack_bootstrap"


def launch_into_scene_enabled(launch_env=None):
    """Whether to launch Harmony straight into the bundled bootstrap scene.

    Enabled by default: the ftrack tools (menu/toolbar/opener) are otherwise
    unavailable at Harmony's welcome screen, where the ftrack package never
    initializes (Harmony does not run package scripts until a scene UI
    loads).

    Configure it in the launch config's ``environment_variables`` block
    (see ``extensions/launch/harmony-launch-*.yaml``)::

        environment_variables:
          FTRACK_HARMONY_LAUNCH_INTO_SCENE: "0"

    *launch_env* is that block from the launch event
    (``event["data"]["application"]["environment_variables"]``); the Connect
    process environment is used as a fallback. Set the value to
    ``0``/``false``/``no``/``off`` to keep the normal welcome/staging screen.
    """
    value = None
    if launch_env:
        value = launch_env.get("FTRACK_HARMONY_LAUNCH_INTO_SCENE")
    if value is None:
        value = os.environ.get("FTRACK_HARMONY_LAUNCH_INTO_SCENE", "1")
    return str(value).strip().lower() not in ("0", "false", "no", "off", "")


def stage_bootstrap_scene():
    """Stage a per-launch copy of the bundled blank bootstrap scene.

    A Harmony scene is a folder; hand the artist a throwaway copy rather than
    the shared bundled original. Returns ``(xstage_path, stage_root)`` where
    *xstage_path* is the ``.xstage`` to pass to the launch command and
    *stage_root* is the temp directory to remove on shutdown, or
    ``(None, None)`` if the bundled scene is missing.
    """
    source = os.path.join(
        connect_plugin_path,
        "resource",
        "bootstrap",
        "scene",
        BOOTSTRAP_SCENE_NAME,
    )
    if not os.path.isdir(source):
        logger.warning(
            "Bootstrap scene not found at {}; launching without a "
            "scene.".format(source)
        )
        return None, None

    stage_root = tempfile.mkdtemp(prefix="ftrack_harmony_bootstrap_")
    dest = os.path.join(stage_root, BOOTSTRAP_SCENE_NAME)
    shutil.copytree(source, dest)
    xstage_path = os.path.join(dest, BOOTSTRAP_SCENE_NAME + ".xstage")
    return xstage_path, stage_root


def sync_js_plugin(app_path, framework_extensions_paths, bootstrap_path=None):
    """
    Sync the JS plugin to the user's Harmony scripts folder, removing any existing files.

    :param app_path: The full path to DCC executable.
    :param framework_extensions_paths: List of paths to scan for extensions.
        Currently unused, kept for backwards compatibility (JS extensions
        support has been removed).
    :param bootstrap_path: Path to the bootstrap resource folder to deploy,
        defaults to the resource/bootstrap folder within the built Connect
        plugin. The tests pass this explicitly when run against the source
        tree.
    :return:
    """
    version_nr = None
    variant = None
    for part in app_path.split(os.sep):
        if part.lower().startswith("toon boom"):
            for s in re.findall(r"\d+", part):
                version_nr = s
                variant = part.split(" ")[-1]
                break
            if variant:
                break
    logger.info(
        f"Deploying scripts, variant: {variant}, version: {version_nr}, app_path: {app_path}"
    )

    assert (
        variant
    ), f"Could not determine Harmony variant from executable path: {app_path}"
    assert (
        version_nr
    ), f"Could not determine Harmony version from executable path: {app_path}"

    path_scripts = None
    if sys.platform == "win32":
        path_scripts = os.path.expandvars("%APPDATA%")
    elif sys.platform == "linux":
        path_scripts = os.path.expandvars("$HOME")
    elif sys.platform == "darwin":
        path_scripts = os.path.expandvars("$HOME/Library/Preferences")

    if not path_scripts:
        raise Exception("Could not determine user prefs folder!")

    path_scripts = os.path.realpath(path_scripts)

    path_scripts = os.path.join(
        path_scripts,
        "Toon Boom Animation",
        "Toon Boom Harmony {}".format(variant),
    )

    if not path_scripts:
        raise Exception("Could not determine Harmony prefs folder!")

    path_scripts = os.path.join(
        path_scripts, "{}00-scripts".format(version_nr), "packages", "ftrack"
    )

    if not os.path.exists(path_scripts):
        logger.warning("Creating: {}".format(path_scripts))
        os.makedirs(path_scripts)
    else:
        # Clean up the folder
        logger.debug("Removing files at: {}".format(path_scripts))
        for fn in os.listdir(path_scripts):
            file_path = os.path.join(path_scripts, fn)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                logger.debug(f"Removed: {fn}")
            except Exception as e:
                logger.error(f"Failed to delete {file_path}. Reason: {e}")

    bootstrap_folder = bootstrap_path or os.path.join(
        connect_plugin_path, "resource", "bootstrap"
    )

    # Copy the library and bootstrap
    for fn in ["utils.js", "configure.js", "harmony_commands.js"]:
        src = os.path.join(bootstrap_folder, "js", fn)
        dst = os.path.join(path_scripts, fn)
        shutil.copy(src, dst)
        logger.debug(f"Copied: {fn}")

    # Copy icons folder
    src = os.path.join(bootstrap_folder, "icons")
    dst = os.path.join(path_scripts, "icons")
    shutil.copytree(src, dst)
    logger.debug("Copied: icons")

    # Deploy the scene-event hooks to the user scripts root (one level
    # above packages/): Harmony rebuilds the menu bar whenever a scene is
    # opened or created and drops script-added items, so these hooks
    # re-register the ftrack menu entries. Each hook chains Harmony's
    # default callback of the same name (never clobbers it). Never
    # overwrite a studio's own hook (ours carry an "[ftrack]" marker).
    scripts_root = os.path.dirname(os.path.dirname(path_scripts))
    for hook_name in ["TB_sceneOpened.js", "TB_sceneCreated.js"]:
        src = os.path.join(bootstrap_folder, "js", hook_name)
        dst = os.path.join(scripts_root, hook_name)
        if os.path.isfile(dst):
            with open(dst, "r", errors="replace") as existing:
                if "[ftrack]" not in existing.read():
                    logger.warning(
                        f"Not deploying {hook_name} - a non-ftrack "
                        f"script already exists at {dst}. ftrack menu "
                        f"entries will disappear after a scene switch; "
                        f"add a call to the ftrack re-registration there."
                    )
                    continue
        shutil.copy(src, dst)
        logger.debug(f"Copied: {hook_name}")

    # Return the deployed package folder (the one holding configure.js) so
    # the launcher can expose it to the JS side. The TB_scene* hooks need
    # this absolute path to re-include configure.js and reconnect the
    # integration to the standalone RPC server after Harmony tears down
    # the script engine on a scene switch (Harmony does not re-invoke the
    # package configure()).
    return path_scripts


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
    logger.info("Launching integration v{}".format(integration_version))

    if not launch_data["integration"].get("env"):
        launch_data["integration"]["env"] = {}

    bootstrap_path = os.path.join(connect_plugin_path, "resource", "bootstrap")
    logger.info("Adding {} to PYTHONPATH".format(bootstrap_path))

    launch_data["integration"]["env"]["PYTHONPATH.prepend"] = (
        os.path.pathsep.join([python_dependencies, bootstrap_path])
    )

    while True:
        # Use a random port for the integration server
        port = random.randint(50000, 65000)
        if check_port(port):
            break
        else:
            logger.warning(
                f"Port {port} is already in use, trying another one."
            )

    # Re-create the Harmony plugin taking extension into account
    package_ftrack_path = sync_js_plugin(
        event["data"]["application"]["path"],
        event["data"]["application"]["environment_variables"][
            "FTRACK_FRAMEWORK_EXTENSIONS_PATH"
        ].split(os.pathsep),
    )

    # Expose the package root (parent of the "ftrack" folder, i.e. the
    # Harmony "packages" dir) so the TB_scene* hooks can re-include
    # configure.js and reconnect the integration to the standalone RPC
    # server after a scene switch.
    launch_data["integration"]["env"]["FTRACK_HARMONY_PACKAGE_PATH.set"] = (
        os.path.dirname(package_ftrack_path)
    )

    launch_data["integration"]["env"]["FTRACK_INTEGRATION_LISTEN_PORT.set"] = (
        str(port)
    )
    launch_data["integration"]["env"][
        "FTRACK_REMOTE_INTEGRATION_SESSION_ID"
    ] = str(uuid.uuid4())
    launch_data["integration"]["env"]["FTRACK_HARMONY_VERSION"] = str(
        integration_version
    )

    selection = event["data"].get("context", {}).get("selection", [])

    if selection:
        task = session.get("Context", selection[0]["entityId"])
        launch_data["integration"]["env"]["FTRACK_CONTEXTID.set"] = task["id"]

    # Launch Harmony straight into a bundled blank "bootstrap" scene so the
    # ftrack tools (menu/toolbar/opener) are available immediately. Without
    # this the artist lands on Harmony's welcome screen, where the ftrack
    # package never initializes. Connect appends integration launch_arguments
    # to the launch command and, on macOS, rewrites `open <app>` to
    # `open -n -a <app> <scene>`; Windows/Linux receive the scene as a
    # positional argument. Configure via the launch config's
    # environment_variables block; disable with
    # FTRACK_HARMONY_LAUNCH_INTO_SCENE=0.
    launch_env = event["data"]["application"].get("environment_variables", {})
    if launch_into_scene_enabled(launch_env):
        xstage_path, stage_root = stage_bootstrap_scene()
        if xstage_path:
            logger.info(
                "Launching Harmony into bootstrap scene: {}".format(
                    xstage_path
                )
            )
            launch_data["integration"].setdefault("launch_arguments", [])
            launch_data["integration"]["launch_arguments"].append(xstage_path)
            # Hand the staged copy's root to the standalone helper so it can
            # remove it when Harmony exits (see the shutdown watchdog).
            launch_data["integration"]["env"][
                "FTRACK_HARMONY_BOOTSTRAP_SCENE.set"
            ] = stage_root

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
        "data.application.identifier=harmony*"
        " and data.application.version >= 22",
        handle_discovery_event,
        priority=40,
    )

    handle_launch_event = functools.partial(on_launch_integration, session)

    session.event_hub.subscribe(
        "topic=ftrack.connect.application.launch and "
        "data.application.identifier=harmony*"
        " and data.application.version >= 22",
        handle_launch_event,
        priority=40,
    )

    logger.info(
        "Registered {} integration v{} discovery and launch.".format(
            NAME, __version__
        )
    )
