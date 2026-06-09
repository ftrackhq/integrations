# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import maya.cmds as cmds

from ftrack_framework_loader.plugins.base_loader_importer import (
    LoaderImporterPlugin,
)
from ftrack_framework_maya.asset import MayaFtrackObjectManager
from ftrack_framework_maya.asset.dcc_object import MayaDccObject
from ftrack_framework_maya.asset import constants as asset_const
from ftrack_framework_maya import utils as maya_utils


class MayaNativeLoaderImporterPlugin(LoaderImporterPlugin):
    """
    Maya native file (.ma/.mb/.fbx) loader importer plugin.

    Supports multiple load modes:
    - reference: Load as Maya reference (editable)
    - import: Import directly into scene
    - open: Open the file (replaces current scene)
    """

    name = "maya.native_loader_importer"

    FtrackObjectManager = MayaFtrackObjectManager
    DccObject = MayaDccObject

    @maya_utils.run_in_main_thread
    def get_current_objects(self):
        """Return set of current Maya scene assemblies"""
        return set(cmds.ls(assemblies=True, long=True))

    @maya_utils.run_in_main_thread
    def run_custom(self, store):
        """
        Import or reference Maya file into scene.

        *store* contains:
        - result: Dict with component_path from collector

        self.options contains:
        - load_mode: 'reference', 'import', or 'open'
        - load_options: Dict with Maya-specific options:
          - preserve_references: bool
          - add_namespace: bool
          - namespace_option: 'file_name' or 'component'
        """
        # Get component path from collector result
        collector_result = store.get("result", {})
        component_path = collector_result.get("component_path")

        if not component_path:
            raise ValueError("component_path required from collector")

        # Get load mode and options
        load_mode = self.options.get("load_mode", "import")
        load_options = self.options.get("load_options", {})

        self.logger.info(
            f"Loading {component_path} with mode: {load_mode}, options: {load_options}"
        )

        # Build Maya-specific options
        maya_options = self._build_maya_options(
            component_path, load_options, store
        )

        # Load FBX plugin if needed
        if component_path.lower().endswith(".fbx"):
            try:
                cmds.loadPlugin("fbxmaya", quiet=True)
            except Exception as e:
                self.logger.warning(
                    f"Could not load FBX plugin 'fbxmaya': {e}"
                )

        # Execute load based on mode
        result_nodes = None

        if load_mode == asset_const.REFERENCE_MODE:
            result_nodes = self._reference_asset(component_path, maya_options)
        elif load_mode == asset_const.IMPORT_MODE:
            result_nodes = self._import_asset(component_path, maya_options)
        elif load_mode == asset_const.OPEN_MODE:
            result_nodes = self._open_asset(component_path, maya_options)
        else:
            raise ValueError(f"Unknown load mode: {load_mode}")

        self.logger.info(
            f"Load completed with {len(result_nodes or [])} nodes"
        )

        return {
            "imported_nodes": result_nodes,
            "component_path": component_path,
            "load_mode": load_mode,
        }

    def _build_maya_options(self, component_path, load_options, store):
        """Build Maya command options dict"""
        maya_options = {}

        # Preserve references
        if load_options.get("preserve_references"):
            maya_options["pr"] = True

        # Add namespace
        if load_options.get("add_namespace"):
            ns_option = load_options.get("namespace_option", "file_name")

            if ns_option == "file_name":
                # Use filename without extension as namespace
                maya_options["ns"] = os.path.basename(component_path).split(
                    "."
                )[0]
            elif ns_option == "component":
                # Use component name as namespace
                component_data = store.get("component_data", {})
                maya_options["ns"] = component_data.get(
                    "component_name", "ftrack"
                )
            else:
                # Use the value directly as namespace
                maya_options["ns"] = ns_option

        return maya_options

    def _reference_asset(self, component_path, maya_options):
        """Load Maya file as reference"""
        self.logger.debug(
            f"Referencing: {component_path} with options: {maya_options}"
        )

        nodes = cmds.file(
            component_path, reference=True, returnNewNodes=True, **maya_options
        )

        return nodes

    def _import_asset(self, component_path, maya_options):
        """Import Maya file directly"""
        self.logger.debug(
            f"Importing: {component_path} with options: {maya_options}"
        )

        nodes = cmds.file(
            component_path, i=True, returnNewNodes=True, **maya_options
        )

        return nodes

    def _open_asset(self, component_path, maya_options):
        """Open Maya file (replaces current scene)"""
        self.logger.debug(
            f"Opening: {component_path} with options: {maya_options}"
        )

        # Open file
        cmds.file(component_path, open=True, force=True, **maya_options)

        # Return all objects in scene
        nodes = cmds.ls(assemblies=True, long=True)

        return nodes


def register(api_object, **kw):
    """Register plugin to framework"""
    # Auto-registration handled by framework plugin discovery
    pass
