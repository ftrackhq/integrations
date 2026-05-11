# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Callback management for Deadline Cloud sync on save/open.

Save uses a SceneSaved scriptJob (post-save, non-blocking).
Open uses MSceneMessage.kBeforeOpenCheck (pre-open, blocking)
so assets can be synced before Maya tries to resolve references.

Both are opt-in via menu toggles, persisted in Maya optionVar.
"""

import logging

import maya.cmds as cmds
import maya.api.OpenMaya as om2

logger = logging.getLogger(__name__)

# optionVar keys
SAVE_OPTVAR = "ftrack_deadline_sync_on_save"
OPEN_OPTVAR = "ftrack_deadline_sync_on_open"

# Active callback IDs (None when not registered)
_save_job_id = None
_open_cb_id = None

# Dialog singleton (avoid stacking on rapid saves)
_sync_dialog = None


# -- optionVar helpers --


def is_save_enabled():
    """Return True if sync-on-save is enabled."""
    return bool(cmds.optionVar(q=SAVE_OPTVAR))


def is_open_enabled():
    """Return True if sync-on-open is enabled."""
    return bool(cmds.optionVar(q=OPEN_OPTVAR))


# -- Save callback (SceneSaved scriptJob, post-save) --


def register_save_callback():
    """Register SceneSaved scriptJob."""
    global _save_job_id
    if _save_job_id is not None:
        return
    _save_job_id = cmds.scriptJob(
        event=["SceneSaved", _on_scene_saved], protected=True
    )
    logger.info("Registered SceneSaved scriptJob (id=%s)", _save_job_id)


def unregister_save_callback():
    """Remove SceneSaved scriptJob."""
    global _save_job_id
    if _save_job_id is None:
        return
    if cmds.scriptJob(exists=_save_job_id):
        cmds.scriptJob(kill=_save_job_id, force=True)
    logger.info("Removed SceneSaved scriptJob (id=%s)", _save_job_id)
    _save_job_id = None


# -- Open callback (kBeforeOpenCheck, pre-open, blocking) --


def register_open_callback():
    """Register a kBeforeOpenCheck callback.

    Fires before Maya reads the scene file.  The callback
    shows a modal dialog so assets can be synced.  Returning
    True from the callback lets the open proceed; False
    cancels it.
    """
    global _open_cb_id
    if _open_cb_id is not None:
        return
    _open_cb_id = om2.MSceneMessage.addCheckFileCallback(
        om2.MSceneMessage.kBeforeOpenCheck,
        _on_before_open,
        None,  # clientData — ensures Maya passes all 3 args
    )
    logger.info(
        "Registered kBeforeOpenCheck callback (id=%s)",
        _open_cb_id,
    )


def unregister_open_callback():
    """Remove the kBeforeOpenCheck callback."""
    global _open_cb_id
    if _open_cb_id is None:
        return
    om2.MMessage.removeCallback(_open_cb_id)
    logger.info(
        "Removed kBeforeOpenCheck callback (id=%s)",
        _open_cb_id,
    )
    _open_cb_id = None


# -- Toggle helpers (called from menu checkBox commands) --


def toggle_save(enabled, *args):
    """Enable or disable sync-on-save."""
    if isinstance(enabled, str):
        enabled = enabled == "true" or enabled == "1"
    enabled = bool(enabled)
    cmds.optionVar(iv=(SAVE_OPTVAR, int(enabled)))
    if enabled:
        register_save_callback()
    else:
        unregister_save_callback()
    logger.info("Sync on Save: %s", "enabled" if enabled else "disabled")


def toggle_open(enabled, *args):
    """Enable or disable sync-on-open."""
    if isinstance(enabled, str):
        enabled = enabled == "true" or enabled == "1"
    enabled = bool(enabled)
    cmds.optionVar(iv=(OPEN_OPTVAR, int(enabled)))
    if enabled:
        register_open_callback()
    else:
        unregister_open_callback()
    logger.info("Sync on Open: %s", "enabled" if enabled else "disabled")


# -- Save scriptJob callback --


def _on_scene_saved():
    """Called by Maya on SceneSaved.  Defers dialog open."""
    cmds.evalDeferred(lambda: _show_sync_dialog(direction="upload"))


# -- Open check callback --


def _on_before_open(fileObject, clientData=None):
    """Called by Maya before opening a scene file.

    In Maya API 2.0, check callbacks receive ``(fileObject,
    clientData)`` and return True/False (no retCode parameter).

    Shows the sync dialog as a modal (blocking) dialog
    so that asset sync can complete before Maya reads the file.

    Args:
        fileObject: MFileObject with the path being opened.
        clientData: User data (unused).

    Returns:
        True to proceed with the open, False to cancel.
    """
    scene_path = fileObject.resolvedFullName()
    logger.info("kBeforeOpenCheck fired for: %s", scene_path)

    proceed = _show_sync_dialog_modal(scene_path)
    return proceed


# -- Dialog management --


def _show_sync_dialog(direction="both"):
    """Show the sync dialog (non-blocking singleton)."""
    global _sync_dialog
    from .dialogs.sync_dialog import DeadlineSyncDialog
    from .utils import get_maya_main_window

    if _sync_dialog is not None:
        try:
            if _sync_dialog.isVisible():
                _sync_dialog.raise_()
                _sync_dialog.activateWindow()
                return
        except RuntimeError:
            _sync_dialog = None

    _sync_dialog = DeadlineSyncDialog(
        direction=direction, parent=get_maya_main_window()
    )
    _sync_dialog.show()


def _show_sync_dialog_modal(scene_path=None):
    """Show the sync dialog as a modal dialog.

    Blocks until the user closes it.  Returns True to
    proceed with the open, False to cancel.
    """
    from .dialogs.sync_dialog import DeadlineSyncDialog
    from .utils import get_maya_main_window, QtWidgets

    dialog = DeadlineSyncDialog(
        scene_path=scene_path,
        modal=True,
        direction="download",
        parent=get_maya_main_window(),
    )
    result = dialog.exec()
    return result == QtWidgets.QDialog.Accepted


def show_sync_dialog(*args):
    """Menu callback: open sync dialog directly."""
    _show_sync_dialog()


# -- Startup restore --


def restore_from_prefs():
    """Re-register callbacks based on saved optionVar state."""
    if is_save_enabled():
        register_save_callback()
    if is_open_enabled():
        register_open_callback()
