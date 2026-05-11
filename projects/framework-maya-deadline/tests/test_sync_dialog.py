# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Live Maya tests for DeadlineSyncDialog.

Run via dcc-test-harness::

    uv run python -m pytest tests/test_sync_dialog.py -v \\
        --dcc-connect-plugin .../framework-maya/dist/ftrack-framework-maya-X \\
        --dcc-connect-plugin .
"""


def test_dialog_opens_with_correct_title(dcc_client):
    """Dialog should open with the expected window title."""
    result = dcc_client.execute("""
import maya.cmds as cmds
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.utils import get_maya_main_window

dialog = DeadlineSyncDialog(parent=get_maya_main_window())
title = dialog.windowTitle()
dialog.close()
dialog.deleteLater()
title
""")
    assert result == "Deadline Cloud - Sync"


def test_dialog_has_compare_button(dcc_client):
    """Dialog should contain a Compare button."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.utils import get_maya_main_window

dialog = DeadlineSyncDialog(parent=get_maya_main_window())
btn = dialog._compare_btn
exists = btn is not None
text = btn.text()
dialog.close()
dialog.deleteLater()
(exists, text)
""")
    assert result == (True, "Compare")


def test_dialog_has_sync_button_disabled(dcc_client):
    """Sync button should exist but be disabled (M5)."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.utils import get_maya_main_window

dialog = DeadlineSyncDialog(parent=get_maya_main_window())
btn = dialog._sync_btn
exists = btn is not None
enabled = btn.isEnabled()
dialog.close()
dialog.deleteLater()
(exists, enabled)
""")
    assert result == (True, False)


def test_modal_dialog_has_continue_cancel(dcc_client):
    """Modal mode should show Continue/Cancel instead of Sync/Close."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.utils import get_maya_main_window, QtWidgets

dialog = DeadlineSyncDialog(
    scene_path="/tmp/test.ma", modal=True,
    parent=get_maya_main_window(),
)

# Find buttons by text
buttons = dialog.findChildren(QtWidgets.QPushButton)
labels = sorted([b.text() for b in buttons])

dialog.close()
dialog.deleteLater()
labels
""")
    assert "Cancel Open" in result
    assert "Continue" in result
    assert "Sync" in result


def test_dialog_has_farm_queue_selector(dcc_client):
    """Dialog should contain FarmQueueSelector widget."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.dialogs.widgets.farm_queue_selector import (
    FarmQueueSelector,
)
from ftrack_framework_maya_deadline.utils import get_maya_main_window

dialog = DeadlineSyncDialog(parent=get_maya_main_window())
is_instance = isinstance(dialog._farm_queue, FarmQueueSelector)
dialog.close()
dialog.deleteLater()
is_instance
""")
    assert result is True


def test_dialog_has_sync_status_widget(dcc_client):
    """Dialog should contain SyncStatusWidget."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.dialogs.widgets.sync_status_widget import (
    SyncStatusWidget,
)
from ftrack_framework_maya_deadline.utils import get_maya_main_window

dialog = DeadlineSyncDialog(parent=get_maya_main_window())
is_instance = isinstance(dialog._results, SyncStatusWidget)
dialog.close()
dialog.deleteLater()
is_instance
""")
    assert result is True


def test_dialog_shows_scene_path(dcc_client):
    """Scene label should reflect the current scene (or unsaved)."""
    result = dcc_client.execute("""
import maya.cmds as cmds
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.utils import get_maya_main_window

cmds.file(new=True, force=True)

dialog = DeadlineSyncDialog(parent=get_maya_main_window())
text = dialog._scene_label.text()
dialog.close()
dialog.deleteLater()
text
""")
    assert result == "(unsaved)"


def test_modal_dialog_shows_explicit_scene_path(dcc_client):
    """Modal dialog should show the provided scene path."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.utils import get_maya_main_window

dialog = DeadlineSyncDialog(
    scene_path="/projects/shot01/scene.ma",
    modal=True,
    parent=get_maya_main_window(),
)
text = dialog._scene_label.text()
dialog.close()
dialog.deleteLater()
text
""")
    assert result == "/projects/shot01/scene.ma"


def test_sync_status_widget_set_results(dcc_client):
    """SyncStatusWidget should accept and display result dicts."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.widgets.sync_status_widget import (
    SyncStatusWidget,
)

widget = SyncStatusWidget()
widget.set_results({
    "needs_upload": [
        {"path": "/tex/a.exr", "size": 1024, "hash": "abc"},
    ],
    "already_synced": [
        {"path": "/tex/b.exr", "size": 2048, "hash": "def"},
    ],
    "total_files": 2,
    "total_size_bytes": 3072,
    "upload_size_bytes": 1024,
})

top_count = widget._tree.topLevelItemCount()
summary = widget._summary_label.text()
widget.deleteLater()
(top_count, "need upload" in summary.lower())
""")
    assert result == (2, True)


def test_default_direction_is_both(dcc_client):
    """Non-modal dialog should default to 'both' direction."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.utils import get_maya_main_window

dialog = DeadlineSyncDialog(parent=get_maya_main_window())
direction = dialog.current_direction
dialog.close()
dialog.deleteLater()
direction
""")
    assert result == "both"


def test_modal_direction_defaults_to_download(dcc_client):
    """Modal dialog opened for pre-open should default to download."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.utils import get_maya_main_window

dialog = DeadlineSyncDialog(
    scene_path="/tmp/test.ma",
    modal=True,
    direction="download",
    parent=get_maya_main_window(),
)
direction = dialog.current_direction
dialog.close()
dialog.deleteLater()
direction
""")
    assert result == "download"


def test_upload_direction(dcc_client):
    """Dialog with direction='upload' should select upload radio."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.utils import get_maya_main_window

dialog = DeadlineSyncDialog(
    direction="upload",
    parent=get_maya_main_window(),
)
direction = dialog.current_direction
dialog.close()
dialog.deleteLater()
direction
""")
    assert result == "upload"


def test_sync_button_initially_disabled(dcc_client):
    """Sync button should be disabled until Compare finds uploads."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.utils import get_maya_main_window

dialog = DeadlineSyncDialog(parent=get_maya_main_window())
enabled = dialog._sync_btn.isEnabled()
text = dialog._sync_btn.text()
dialog.close()
dialog.deleteLater()
(enabled, text)
""")
    assert result == (False, "Sync")


def test_sync_button_has_click_handler(dcc_client):
    """Sync button should have a click handler connected."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.utils import get_maya_main_window

dialog = DeadlineSyncDialog(parent=get_maya_main_window())
# Check that the clicked signal has at least one receiver
has_receivers = dialog._sync_btn.receivers(
    dialog._sync_btn.clicked
) > 0
dialog.close()
dialog.deleteLater()
has_receivers
""")
    assert result is True


def test_progress_bar_hidden_by_default(dcc_client):
    """Progress bar should be hidden until upload starts."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.utils import get_maya_main_window

dialog = DeadlineSyncDialog(parent=get_maya_main_window())
visible = dialog._progress_bar.isVisible()
dialog.close()
dialog.deleteLater()
visible
""")
    assert result is False


def test_cancel_button_hidden_by_default(dcc_client):
    """Cancel button should be hidden until upload starts."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.utils import get_maya_main_window

dialog = DeadlineSyncDialog(parent=get_maya_main_window())
visible = dialog._cancel_btn.isVisible()
dialog.close()
dialog.deleteLater()
visible
""")
    assert result is False


def test_modal_dialog_has_expected_buttons(dcc_client):
    """Modal dialog should have Sync, Cancel Open, Continue."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.sync_dialog import (
    DeadlineSyncDialog,
)
from ftrack_framework_maya_deadline.utils import (
    get_maya_main_window, QtWidgets,
)

dialog = DeadlineSyncDialog(
    scene_path="/tmp/test.ma", modal=True,
    parent=get_maya_main_window(),
)

buttons = dialog.findChildren(QtWidgets.QPushButton)
labels = sorted([b.text() for b in buttons])
dialog.close()
dialog.deleteLater()
labels
""")
    assert "Cancel Open" in result
    assert "Continue" in result
    assert "Sync" in result
    assert "Compare" in result


def test_sync_status_widget_upload_complete(dcc_client):
    """SyncStatusWidget.set_upload_complete should update summary."""
    result = dcc_client.execute("""
from ftrack_framework_maya_deadline.dialogs.widgets.sync_status_widget import (
    SyncStatusWidget,
)

widget = SyncStatusWidget()
widget.set_upload_complete({
    "uploaded_files": 5,
    "uploaded_bytes": 10240,
    "skipped_files": 3,
    "total_time": 2.5,
    "transfer_rate": 4096.0,
})

summary = widget._summary_label.text()
widget.deleteLater()
("Upload complete" in summary, "5 file(s)" in summary)
""")
    assert result == (True, True)
