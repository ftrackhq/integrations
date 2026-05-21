# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import nuke

from ftrack_framework_loader.plugins.base_loader_importer import (
    LoaderImporterPlugin,
)
from ftrack_framework_nuke.asset import NukeFtrackObjectManager
from ftrack_framework_nuke.asset.dcc_object import NukeDccObject
from ftrack_framework_nuke import utils as nuke_utils


class NukeNativeLoaderImporterPlugin(LoaderImporterPlugin):
    """
    Nuke native loader importer plugin.

    Creates Read nodes for image sequences, movies, etc.
    """

    name = "nuke.native_loader_importer"

    FtrackObjectManager = NukeFtrackObjectManager
    DccObject = NukeDccObject

    @nuke_utils.run_in_main_thread
    def get_current_objects(self):
        """Return set of current Nuke node names"""
        return set([node.name() for node in nuke.allNodes()])

    @nuke_utils.run_in_main_thread
    def run_custom(self, store):
        """
        Create Read node for component.

        *store* contains:
        - result: Dict with component_path from collector

        self.options contains:
        - node_type: Type of node to create ('Read', 'ReadGeo', etc.) - default 'Read'
        - node_settings: Dict of knob values to set on created node
        """
        # Get component path from collector result
        collector_result = store.get("result", {})
        component_path = collector_result.get("component_path")

        if not component_path:
            raise ValueError("component_path required from collector")

        # Get node type and settings
        node_type = self.options.get("node_type", "Read")
        node_settings = self.options.get("node_settings", {})

        self.logger.info(f"Creating {node_type} node for: {component_path}")

        # Create Read node
        read_node = None

        if node_type == "Read":
            read_node = self._create_read_node(component_path, node_settings)
        elif node_type == "ReadGeo":
            read_node = self._create_readgeo_node(
                component_path, node_settings
            )
        elif node_type == "Camera":
            read_node = self._create_camera_node(component_path, node_settings)
        else:
            # Generic node creation
            read_node = nuke.createNode(node_type)
            if "file" in read_node.knobs():
                read_node["file"].setValue(component_path)

        if not read_node:
            raise RuntimeError(f"Failed to create {node_type} node")

        # Apply additional settings
        for knob_name, knob_value in node_settings.items():
            if knob_name in read_node.knobs():
                try:
                    read_node[knob_name].setValue(knob_value)
                except Exception as e:
                    self.logger.warning(
                        f"Could not set {knob_name}={knob_value}: {e}"
                    )

        self.logger.info(f"Created node: {read_node.name()}")

        return {
            "created_node": read_node.name(),
            "component_path": component_path,
            "node_type": node_type,
        }

    def _create_read_node(self, component_path, node_settings):
        """Create a Read node for image sequences/movies"""
        read_node = nuke.createNode("Read")
        read_node["file"].setValue(component_path)

        # Auto-detect sequence/movie settings if not provided
        if "before" not in node_settings:
            read_node["before"].setValue("hold")
        if "after" not in node_settings:
            read_node["after"].setValue("hold")

        return read_node

    def _create_readgeo_node(self, component_path, node_settings):
        """Create a ReadGeo node for geometry (Alembic, OBJ, etc.)"""
        readgeo_node = nuke.createNode("ReadGeo2")
        readgeo_node["file"].setValue(component_path)
        return readgeo_node

    def _create_camera_node(self, component_path, node_settings):
        """Create a Camera node from file"""
        camera_node = nuke.createNode("Camera2")
        if "file" in camera_node.knobs():
            camera_node["file"].setValue(component_path)
        return camera_node


def register(api_object, **kw):
    """Register plugin to framework"""
    # Auto-registration handled by framework plugin discovery
    pass
