# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import maya.cmds as cmds

from ftrack_framework_loader.plugins.base_loader_importer import (
    LoaderImporterPlugin,
)
from ftrack_framework_maya.asset import MayaFtrackObjectManager
from ftrack_framework_maya.asset.dcc_object import MayaDccObject
from ftrack_framework_maya import utils as maya_utils


class MayaAbcLoaderImporterPlugin(LoaderImporterPlugin):
    """
    Maya Alembic (.abc) loader importer plugin.

    Uses Maya's AbcImport command to load Alembic caches.
    """

    name = "maya.abc_loader_importer"

    FtrackObjectManager = MayaFtrackObjectManager
    DccObject = MayaDccObject

    @maya_utils.run_in_main_thread
    def get_current_objects(self):
        """Return set of current Maya scene assemblies"""
        return set(cmds.ls(assemblies=True, long=True))

    @maya_utils.run_in_main_thread
    def run_custom(self, store):
        """
        Import Alembic file into Maya scene.

        *store* contains:
        - result: Dict with component_path from collector
        """
        # Get component path from collector result
        collector_result = store.get("result", {})
        component_path = collector_result.get("component_path")

        if not component_path:
            raise ValueError("component_path required from collector")

        self.logger.info(f"Loading Alembic: {component_path}")

        # Ensure Alembic plugin is loaded; without it AbcImport is unavailable.
        try:
            cmds.loadPlugin("AbcImport", quiet=True)
        except Exception as e:
            self.logger.warning(
                f"Could not load AbcImport plugin 'AbcImport': {e}"
            )
            raise

        # Import Alembic
        import_result = cmds.AbcImport(component_path)

        self.logger.info(f"Alembic import result: {import_result}")

        return {
            "imported_nodes": import_result,
            "component_path": component_path,
            "load_mode": "alembic_import",
        }


def register(api_object, **kw):
    """Register plugin to framework"""
    # Auto-registration handled by framework plugin discovery
    pass
