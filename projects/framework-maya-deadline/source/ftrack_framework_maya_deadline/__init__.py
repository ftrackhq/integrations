# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack
import logging
import os
import traceback

import maya.cmds as cmds

from ftrack_framework_core.configure_logging import configure_logging


# Evaluate version and log package version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    __version__ = "0.0.0"

extra_handlers = {
    "maya": {
        "class": "maya.utils.MayaGuiLogHandler",
        "level": "INFO",
        "formatter": "file",
    }
}

configure_logging(
    "ftrack_framework_maya_deadline",
    extra_modules=["ftrack_qt"],
    extra_handlers=extra_handlers,
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug("v{}".format(__version__))


def bootstrap():
    """Initialise framework-maya-deadline integration.

    Adds a "Deadline Cloud" submenu to the existing ftrack menu
    created by framework-maya, populates it with menu items, and
    restores scriptJob state from saved preferences.
    """
    from ftrack_framework_maya import get_ftrack_menu
    from ftrack_framework_maya_deadline import callbacks

    logger.debug("framework-maya-deadline bootstrap starting")

    # Create "Deadline Cloud" submenu under the ftrack menu.
    submenu = get_ftrack_menu(submenu_name="Deadline Cloud")

    # -- Action items --
    cmds.menuItem(
        "dl_sync",
        label="Sync...",
        command=callbacks.show_sync_dialog,
        parent=submenu,
    )

    cmds.menuItem(divider=True, parent=submenu)

    # -- Opt-in toggles --
    cmds.menuItem(
        "dl_sync_on_save",
        label="Sync on Save",
        checkBox=callbacks.is_save_enabled(),
        command=callbacks.toggle_save,
        parent=submenu,
    )
    cmds.menuItem(
        "dl_sync_on_open",
        label="Sync on Open",
        checkBox=callbacks.is_open_enabled(),
        command=callbacks.toggle_open,
        parent=submenu,
    )

    # Restore scriptJob state from previous session.
    callbacks.restore_from_prefs()

    logger.info(
        "framework-maya-deadline v{} bootstrap complete".format(__version__)
    )


try:
    cmds.evalDeferred(bootstrap, lp=True)
except:
    # Make sure any exception that happens are logged as there
    # is most likely no console
    logger.error(traceback.format_exc())
    raise
