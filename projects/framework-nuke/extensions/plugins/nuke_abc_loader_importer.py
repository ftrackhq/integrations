# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import nuke

from ftrack_framework_loader.plugins.base_loader_importer import (
    LoaderImporterPlugin,
)
from ftrack_framework_nuke.asset import NukeFtrackObjectManager
from ftrack_framework_nuke.asset.dcc_object import NukeDccObject
from ftrack_framework_nuke import utils as nuke_utils


class NukeAbcLoaderImporterPlugin(LoaderImporterPlugin):
    """
    Nuke Alembic (.abc) loader importer plugin.

    Creates ReadGeo2 node for Alembic files.
    """

    name = "nuke.abc_loader_importer"

    FtrackObjectManager = NukeFtrackObjectManager
    DccObject = NukeDccObject

    @nuke_utils.run_in_main_thread
    def get_current_objects(self):
        """Return set of current Nuke node names"""
        return set([node.name() for node in nuke.allNodes()])

    @nuke_utils.run_in_main_thread
    def run_custom(self, store):
        """
        Create ReadGeo2 node for Alembic file.

        *store* contains:
        - result: Dict with component_path from collector
        """
        # Get component path from collector result
        collector_result = store.get("result", {})
        component_path = collector_result.get("component_path")

        if not component_path:
            raise ValueError("component_path required from collector")

        self.logger.info(f"Loading Alembic: {component_path}")

        # Create ReadGeo2 node
        readgeo_node = nuke.createNode("ReadGeo2")
        readgeo_node["file"].setValue(component_path)

        # Get additional settings
        node_settings = self.options.get("node_settings", {})

        # Apply settings
        for knob_name, knob_value in node_settings.items():
            if knob_name in readgeo_node.knobs():
                try:
                    readgeo_node[knob_name].setValue(knob_value)
                except Exception as e:
                    self.logger.warning(
                        f"Could not set {knob_name}={knob_value}: {e}"
                    )

        self.logger.info(f"Created Alembic node: {readgeo_node.name()}")

        return {
            "created_node": readgeo_node.name(),
            "component_path": component_path,
            "node_type": "ReadGeo2",
        }


def register(api_object, **kw):
    """Register plugin to framework"""
    # Auto-registration handled by framework plugin discovery
    pass
