# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import re
import getpass
import sys
import pprint
import logging

import functools
import ftrack_api

logger = logging.getLogger(__name__)

cwd = os.path.dirname(__file__)
connect_plugin_path = os.path.abspath(os.path.join(cwd, ".."))

# Read version number from __version__.py
__version__ = "0.0.0"
path_version_file = os.path.join(connect_plugin_path, "__version__.py")
if os.path.isfile(path_version_file):
    with open(path_version_file) as f:
        exec(f.read())
else:
    logger.warning(
        "Unable to read version from {0}. Using default version: {1}".format(
            path_version_file, __version__
        )
    )

sources = os.path.abspath(os.path.join(connect_plugin_path, "dependencies"))


def on_discover_ftrack_nuke_studio_integration(session, event):
    data = {
        "integration": {
            "name": "ftrack-nuke-studio",
            "version": __version__,
        }
    }

    return data


def on_launch_ftrack_nuke_studio_integration(session, event):
    ns_base_data = on_discover_ftrack_nuke_studio_integration(session, event)

    ftrack_nuke_studio_path = os.path.join(cwd, "..", "resource", "plugin")
    application_hooks_path = os.path.join(cwd, "..", "resource", "application_hook")

    entity = event["data"]["context"]["selection"][0]
    project = session.get("Project", entity["entityId"])

    ns_base_data["integration"]["env"] = {
        "PYTHONPATH.prepend": sources,
        "FTRACK_EVENT_PLUGIN_PATH.prepend": application_hooks_path,
        "HIERO_PLUGIN_PATH.prepend": ftrack_nuke_studio_path,
        "FTRACK_CONTEXTID.set": project["id"],
        "QT_PREFERRED_BINDING.set": os.pathsep.join(["PySide2", "PySide"]),
    }

    return ns_base_data


def register(session, **kw):
    """Register hooks for ftrack connect legacy plugins."""

    """Register plugin. Called when used as an plugin."""
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_ftrack_nuke_studio_integration, session
    )

    session.event_hub.subscribe(
        "topic=ftrack.connect.application.discover"
        " and (data.application.identifier=nuke-studio* or data.application.identifier=hiero*)"
        " and data.application.version >= 13",
        handle_discovery_event,
    )

    handle_launch_event = functools.partial(
        on_launch_ftrack_nuke_studio_integration, session
    )

    session.event_hub.subscribe(
        "topic=ftrack.connect.application.launch"
        " and (data.application.identifier=nuke-studio* or data.application.identifier=hiero*)"
        " and data.application.version >= 13",
        handle_launch_event,
    )
