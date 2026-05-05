# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

import os
import ftrack_api
import logging
import functools

from ftrack_utils.version import get_connect_plugin_version

# The name of the integration, should match name in launcher.
NAME = "framework-maya-deadline"


logger = logging.getLogger(__name__)

cwd = os.path.dirname(__file__)
connect_plugin_path = os.path.abspath(os.path.join(cwd, ".."))

# Read version number from __version__.py
__version__ = get_connect_plugin_version(connect_plugin_path)

python_dependencies = os.path.join(connect_plugin_path, "dependencies")


def on_discover_integration(session, event):
    data = {
        "integration": {
            "name": NAME,
            "version": __version__,
        }
    }

    return data


def on_launch_integration(session, event):
    """Inject framework-maya-deadline into the Maya launch environment.

    Rather than going through Connect's integrations mechanism
    (which requires being listed in a launch config and is
    subject to first_level_merge ordering issues), we modify
    the subprocess environment dict directly.  This dict is
    available at event["data"]["options"]["env"] and is the
    same object that Connect passes to subprocess.Popen.
    """

    bootstrap_path = os.path.join(connect_plugin_path, "resource", "bootstrap")

    env = event["data"].get("options", {}).get("env")
    if env is None:
        logger.warning(
            "No environment dict found in launch event, " "cannot inject %s",
            NAME,
        )
        return

    # -- PYTHONPATH: prepend dependencies + bootstrap --
    prepend = os.pathsep.join([python_dependencies, bootstrap_path])
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        prepend + os.pathsep + existing_pp if existing_pp else prepend
    )

    # -- MAYA_SCRIPT_PATH: append bootstrap --
    existing_msp = env.get("MAYA_SCRIPT_PATH", "")
    env["MAYA_SCRIPT_PATH"] = (
        existing_msp + os.pathsep + bootstrap_path
        if existing_msp
        else bootstrap_path
    )

    logger.info(
        "Injected %s v%s into Maya launch environment",
        NAME,
        __version__,
    )


def register(session):
    """Subscribe to application launch events on *registry*."""
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_integration, session
    )

    session.event_hub.subscribe(
        "topic=ftrack.connect.application.discover and "
        "data.application.identifier=maya*"
        " and data.application.version >= 2021",
        handle_discovery_event,
        priority=50,
    )

    handle_launch_event = functools.partial(on_launch_integration, session)

    session.event_hub.subscribe(
        "topic=ftrack.connect.application.launch and "
        "data.application.identifier=maya*"
        " and data.application.version >= 2021",
        handle_launch_event,
        priority=50,
    )

    logger.info(
        "Registered {} integration v{} discovery and launch.".format(
            NAME, __version__
        )
    )
