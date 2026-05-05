# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Tests for M2: ScriptJob callbacks and dialog shells.

Verifies menu items, opt-in toggle behaviour, dialog
opening via callbacks, and the singleton pattern.

Save uses a SceneSaved scriptJob (post-save).
Open uses MSceneMessage.kBeforeOpenCheck (pre-open, modal).
"""

import time


def _ensure_bootstrap(dcc_client):
    """Force the deferred bootstrap to complete."""
    dcc_client.execute(
        "import ftrack_framework_maya_deadline\n"
        "ftrack_framework_maya_deadline.bootstrap()\n"
    )


class TestMenuItems:
    """Verify Deadline Cloud submenu has all expected items."""

    def test_action_items(self, dcc_client):
        """Publish and Scene Status menu items exist."""
        _ensure_bootstrap(dcc_client)
        result = dcc_client.execute(
            "import maya.cmds as cmds\n"
            "children = cmds.menu("
            "'Deadline_Cloud', q=True, itemArray=True"
            ") or []\n"
            "labels = []\n"
            "for i in children:\n"
            "    labels.append("
            "cmds.menuItem(i, q=True, label=True))\n"
            "__result__ = labels\n"
        )
        assert "Publish to Deadline..." in result
        assert "Scene Status..." in result

    def test_toggle_items(self, dcc_client):
        """Sync on Save and Sync on Open toggles exist."""
        result = dcc_client.execute(
            "import maya.cmds as cmds\n"
            "children = cmds.menu("
            "'Deadline_Cloud', q=True, itemArray=True"
            ") or []\n"
            "labels = []\n"
            "for i in children:\n"
            "    labels.append("
            "cmds.menuItem(i, q=True, label=True))\n"
            "__result__ = labels\n"
        )
        assert "Sync on Save" in result
        assert "Sync on Open" in result


class TestSyncToggle:
    """Verify the opt-in toggle registers/unregisters callbacks."""

    def test_save_toggle_on(self, dcc_client):
        """Enabling Sync on Save registers a SceneSaved scriptJob."""
        _ensure_bootstrap(dcc_client)
        dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "callbacks.toggle_save(True)\n"
        )
        result = dcc_client.execute(
            "import maya.cmds as cmds\n"
            "jobs = cmds.scriptJob(listJobs=True)\n"
            "found = False\n"
            "for j in jobs:\n"
            "    if 'SceneSaved' in j"
            " and '_on_scene_saved' in j:\n"
            "        found = True\n"
            "        break\n"
            "__result__ = found\n"
        )
        assert result is True

    def test_save_toggle_off(self, dcc_client):
        """Disabling Sync on Save removes the scriptJob."""
        dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "callbacks.toggle_save(True)\n"
            "callbacks.toggle_save(False)\n"
        )
        result = dcc_client.execute(
            "import maya.cmds as cmds\n"
            "jobs = cmds.scriptJob(listJobs=True)\n"
            "found = False\n"
            "for j in jobs:\n"
            "    if 'SceneSaved' in j"
            " and '_on_scene_saved' in j:\n"
            "        found = True\n"
            "        break\n"
            "__result__ = found\n"
        )
        assert result is False

    def test_open_toggle_on(self, dcc_client):
        """Enabling Sync on Open registers a kBeforeOpenCheck callback."""
        _ensure_bootstrap(dcc_client)
        dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "callbacks.toggle_open(True)\n"
        )
        result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "__result__ = callbacks._open_cb_id is not None\n"
        )
        assert result is True

    def test_open_toggle_off(self, dcc_client):
        """Disabling Sync on Open removes the callback."""
        dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "callbacks.toggle_open(True)\n"
            "callbacks.toggle_open(False)\n"
        )
        result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "__result__ = callbacks._open_cb_id is None\n"
        )
        assert result is True


class TestDialogs:
    """Verify dialogs open from menu items and scriptJobs."""

    def test_manual_publish_dialog(self, dcc_client):
        """Clicking 'Publish to Deadline...' opens the dialog."""
        _ensure_bootstrap(dcc_client)
        dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "callbacks.show_save_dialog()\n"
        )
        time.sleep(1)
        result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "dlg = callbacks._save_dialog\n"
            "__result__ = dlg is not None"
            " and dlg.isVisible()\n"
        )
        assert result is True
        # Clean up
        dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "if callbacks._save_dialog:\n"
            "    callbacks._save_dialog.close()\n"
        )

    def test_manual_status_dialog(self, dcc_client):
        """Clicking 'Scene Status...' opens the dialog non-blocking."""
        dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "callbacks.show_open_dialog()\n"
        )
        time.sleep(1)
        result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "dlg = callbacks._open_dialog\n"
            "__result__ = dlg is not None"
            " and dlg.isVisible()\n"
        )
        assert result is True
        # Clean up
        dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "if callbacks._open_dialog:\n"
            "    callbacks._open_dialog.close()\n"
        )

    def test_save_triggers_dialog(self, dcc_client):
        """Saving with sync enabled opens the publish dialog."""
        _ensure_bootstrap(dcc_client)
        dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "callbacks.toggle_save(True)\n"
        )
        dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "if callbacks._save_dialog:\n"
            "    callbacks._save_dialog.close()\n"
            "callbacks._save_dialog = None\n"
        )
        dcc_client.execute(
            "import maya.cmds as cmds\n"
            "import tempfile, os\n"
            "p = os.path.join(tempfile.gettempdir(),"
            " 'dl_test_scene.ma')\n"
            "cmds.file(rename=p)\n"
            "cmds.file(save=True, type='mayaAscii')\n"
        )
        time.sleep(2)
        result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "dlg = callbacks._save_dialog\n"
            "__result__ = dlg is not None"
            " and dlg.isVisible()\n"
        )
        assert result is True
        # Clean up
        dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "callbacks.toggle_save(False)\n"
            "if callbacks._save_dialog:\n"
            "    callbacks._save_dialog.close()\n"
            "callbacks._save_dialog = None\n"
        )

    def test_dialog_singleton(self, dcc_client):
        """Opening the save dialog twice reuses the same instance."""
        dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "callbacks.show_save_dialog()\n"
        )
        time.sleep(0.5)
        first_id = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "__result__ = id(callbacks._save_dialog)\n"
        )
        dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "callbacks.show_save_dialog()\n"
        )
        time.sleep(0.5)
        second_id = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "__result__ = id(callbacks._save_dialog)\n"
        )
        assert first_id == second_id
        # Clean up
        dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            " import callbacks\n"
            "if callbacks._save_dialog:\n"
            "    callbacks._save_dialog.close()\n"
        )
