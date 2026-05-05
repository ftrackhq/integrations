# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Smoke tests for framework-maya-deadline.

Verify that the integration bootstraps correctly alongside
framework-maya: module loads, submenu appears, framework-maya
is also functional.
"""


def _ensure_bootstrap(dcc_client):
    """Force the deferred bootstrap to complete.

    Both framework-maya and framework-maya-deadline use
    evalDeferred(lp=True) which may not have fired by the
    time the test server accepts connections. Import the
    module explicitly and call bootstrap().
    """
    dcc_client.execute(
        "import ftrack_framework_maya_deadline\n"
        "ftrack_framework_maya_deadline.bootstrap()\n"
    )


class TestBootstrap:
    """Verify framework-maya-deadline loads inside Maya."""

    def test_module_importable(self, dcc_client):
        """ftrack_framework_maya_deadline is importable and
        bootstrap completes."""
        _ensure_bootstrap(dcc_client)
        result = dcc_client.execute(
            "import sys\n"
            "__result__ = 'ftrack_framework_maya_deadline'"
            " in sys.modules\n"
        )
        assert result is True

    def test_framework_maya_also_loaded(self, dcc_client):
        """framework-maya loaded first -- ftrack menu exists."""
        result = dcc_client.execute(
            "import maya.cmds as cmds\n"
            "import maya.mel as mm\n"
            "gMainWindow = mm.eval('$temp1=$gMainWindow')\n"
            "__result__ = cmds.menu(\n"
            "    'ftrack', exists=True, parent=gMainWindow\n"
            ")\n"
        )
        assert result is True

    def test_deadline_cloud_submenu_exists(self, dcc_client):
        """'Deadline Cloud' submenu is present under
        the ftrack menu."""
        # Maya replaces spaces with underscores in widget
        # names, so check by listing items under the ftrack
        # menu and matching by label.
        result = dcc_client.execute(
            "import maya.cmds as cmds\n"
            "items = cmds.menu('ftrack', q=True,"
            " itemArray=True) or []\n"
            "found = False\n"
            "for i in items:\n"
            "    if cmds.menuItem(i, q=True, label=True)"
            " == 'Deadline Cloud':\n"
            "        if cmds.menuItem(i, q=True,"
            " subMenu=True):\n"
            "            found = True\n"
            "            break\n"
            "__result__ = found\n"
        )
        assert result is True
