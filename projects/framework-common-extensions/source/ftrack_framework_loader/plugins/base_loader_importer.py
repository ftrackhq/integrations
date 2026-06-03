# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import json
import base64

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_loader import constants as loader_const
from ftrack_framework_asset_manager.asset.ftrack_asset_info import (
    FtrackAssetInfo,
)


class LoaderImporterPlugin(BasePlugin):
    """
    Base Loader Importer Plugin Class.

    This is the CRITICAL plugin that:
    1. Creates ftrack tracking nodes with metadata (init_nodes)
    2. Loads DCC content and connects to tracking nodes (load_asset)
    3. Or does both in one operation (init_and_load)

    Subclasses MUST implement:
    - get_current_objects(): Return set of current scene objects
    - run(): DCC-specific import logic (reference, import, etc.)
    """

    plugin_type = loader_const.PLUGIN_LOADER_IMPORTER_TYPE

    FtrackObjectManager = None
    """FtrackObjectManager class to use - subclass must set"""

    DccObject = None
    """DccObject class to use - subclass must set"""

    @property
    def ftrack_object_manager(self):
        """Returns FtrackObjectManager instance"""
        return self._ftrack_object_manager

    @ftrack_object_manager.setter
    def ftrack_object_manager(self, value):
        """Sets FtrackObjectManager instance"""
        self._ftrack_object_manager = value

    @property
    def asset_info(self):
        """Returns FtrackAssetInfo instance"""
        return self._asset_info

    @asset_info.setter
    def asset_info(self, value):
        """Sets FtrackAssetInfo instance"""
        if not isinstance(value, FtrackAssetInfo):
            value = FtrackAssetInfo(value)
        self._asset_info = value

    @property
    def dcc_object(self):
        """Returns DccObject instance"""
        return self._dcc_object

    @dcc_object.setter
    def dcc_object(self, value):
        """Sets DccObject instance"""
        self._dcc_object = value

    def __init__(self, options, session, context_id=None):
        """
        Initialize LoaderImporterPlugin with *options*, *session*, *context_id*.
        """
        super(LoaderImporterPlugin, self).__init__(
            options, session, context_id
        )

        self._asset_info = None
        self._dcc_object = None
        self._ftrack_object_manager = None

        # Initialize FtrackObjectManager if classes provided
        if self.FtrackObjectManager:
            self._ftrack_object_manager = self.FtrackObjectManager(session)

    def run(self, store):
        """
        Execute the appropriate method based on options['method'].

        Dispatches to:
        - init_nodes: Create tracking nodes only
        - load_asset: Load content only (assumes node exists)
        - init_and_load: Create nodes + load content (default)
        - run: DCC-specific run (for subclass override)
        """
        method = self.options.get("method", loader_const.METHOD_INIT_AND_LOAD)

        self.logger.debug(f"LoaderImporterPlugin.run() with method: {method}")

        if method == loader_const.METHOD_INIT_NODES:
            result = self.init_nodes(store)
        elif method == loader_const.METHOD_LOAD_ASSET:
            result = self.load_asset(store)
        elif method == loader_const.METHOD_INIT_AND_LOAD:
            result = self.init_and_load(store)
        else:
            # Custom run - subclass should override
            result = self.run_custom(store)

        store["result"] = result
        return result

    def init_nodes(self, store):
        """
        Create ftrack tracking node with metadata.

        *store* should contain:
        - context_data: Dict with version_id, asset_id, etc.
        - component_data: Dict with component_name
        - result: Collector result with component_path, component_id

        This method:
        1. Creates FtrackAssetInfo from context + collector data
        2. Creates DCC tracking node via FtrackObjectManager
        3. Stores asset_info and dcc_object in result

        Returns dict with:
        - asset_info: FtrackAssetInfo instance
        - dcc_object: DccObject instance
        """
        context_data = store.get("context_data", {})
        component_data = store.get("component_data", {})
        collector_result = store.get("result", {})

        # Build asset_info_options (base64 encoded JSON for storage in DCC node)
        asset_info_options = self._build_asset_info_options(
            context_data, store
        )

        # Get asset version entity from ftrack
        version_id = context_data.get("version_id")
        if not version_id:
            raise ValueError("version_id required in context_data")

        # session.get + populate, not `select … from AssetVersion where
        # id is "{}"`.format(): ftrack-api has no parametric queries, and
        # Aikido's Bandit-B608 SAST rule fires on any `.format()` whose
        # format string contains `from`. The populate projection mirrors
        # every attribute FtrackAssetInfo.create reads downstream, so the
        # asset/components/locations traversal it performs doesn't fall
        # back to lazy auto-population (N+1 round-trips).
        asset_version_entity = self.session.get("AssetVersion", version_id)
        if asset_version_entity is None:
            raise ValueError("AssetVersion {} not found".format(version_id))
        self.session.populate(
            asset_version_entity,
            "version, is_latest_version, "
            "asset.name, asset.type.name, "
            "asset.ancestors.name, asset.parent.project.name, "
            "uses_versions.id, "
            "components.name, "
            "components.component_locations.location.name",
        )

        # Get component info from collector result
        component_name = collector_result.get("component_name")
        component_path = collector_result.get("component_path")
        component_id = collector_result.get("component_id")

        if not component_name:
            component_name = component_data.get("component_name")

        # Get load mode from options
        load_mode = self.options.get("load_mode", "import")

        # Create FtrackAssetInfo
        asset_info = FtrackAssetInfo.create(
            asset_version_entity,
            component_name=component_name,
            component_path=component_path,
            component_id=component_id,
            load_mode=load_mode,
            asset_info_options=asset_info_options,
        )

        self.logger.debug(f"Created FtrackAssetInfo: {asset_info}")

        # Create tracking node via FtrackObjectManager
        if not self.ftrack_object_manager:
            raise RuntimeError(
                "FtrackObjectManager not available - subclass must set FtrackObjectManager class"
            )

        self.ftrack_object_manager.asset_info = asset_info
        dcc_object = self.ftrack_object_manager.create_new_dcc_object()

        self.logger.info(
            f"Created tracking node: {dcc_object.name} for component: {component_name}"
        )

        # Store references
        self.asset_info = asset_info
        self.dcc_object = dcc_object

        result = {
            "asset_info": asset_info,
            "dcc_object": dcc_object,
            "status": "success",
        }

        return result

    def load_asset(self, store):
        """
        Load DCC content and connect to tracking node.

        *store* should contain:
        - result: Dict with asset_info and dcc_object (from init_nodes)
        - context_data, component_data

        This method:
        1. Gets current scene objects (before load)
        2. Executes DCC-specific import via run_custom()
        3. Gets new scene objects (after load)
        4. Marks tracking node as loaded
        5. Connects loaded objects to tracking node

        Returns dict with:
        - result: DCC-specific import result
        - loaded_objects: Set of newly loaded objects
        """
        # Get asset_info and dcc_object from store (created by init_nodes)
        existing_result = store.get("result", {})
        asset_info = existing_result.get("asset_info")
        dcc_object = existing_result.get("dcc_object")

        if not asset_info or not dcc_object:
            raise RuntimeError(
                "asset_info and dcc_object required in store - call init_nodes first"
            )

        # Set up object manager
        self.asset_info = asset_info
        self.dcc_object = dcc_object
        self.ftrack_object_manager.asset_info = asset_info
        self.ftrack_object_manager.dcc_object = dcc_object

        # Get current scene objects before load
        old_objects = self.get_current_objects()
        self.logger.debug(f"Scene objects before load: {len(old_objects)}")

        # Execute DCC-specific import
        run_result = self.run_custom(store)

        # Get new scene objects after load
        new_objects = self.get_current_objects()
        self.logger.debug(f"Scene objects after load: {len(new_objects)}")

        # Find newly loaded objects
        diff = new_objects.difference(old_objects)
        self.logger.info(f"Newly loaded objects: {len(diff)}")

        # Mark as loaded
        self.ftrack_object_manager.objects_loaded = True

        # Connect loaded objects to ftrack node
        if diff:
            self.ftrack_object_manager.connect_objects(diff)
            self.logger.debug(
                f"Connected {len(diff)} objects to tracking node"
            )

        result = {
            "result": run_result,
            "loaded_objects": list(diff),
            "status": "success",
        }

        return result

    def init_and_load(self, store):
        """
        Combined operation: create tracking nodes + load content.

        This is the default method and most common use case.

        Returns dict with combined results.
        """
        # Step 1: Create tracking nodes
        init_result = self.init_nodes(store)

        # Merge init result into store["result"] so load_asset can find
        # asset_info / dcc_object without losing the collector's
        # component_path / component_name / component_id — run_custom
        # reads those keys to do the actual DCC import.
        merged = dict(store.get("result") or {})
        merged.update(init_result)
        store["result"] = merged

        # Step 2: Load content
        load_result = self.load_asset(store)

        # Combine results
        result = {
            "asset_info": init_result["asset_info"],
            "dcc_object": init_result["dcc_object"],
            "import_result": load_result["result"],
            "loaded_objects": load_result["loaded_objects"],
            "status": "success",
        }

        return result

    def _build_asset_info_options(self, context_data, store):
        """
        Build asset_info_options as base64-encoded JSON.

        This stores the full context for later retrieval.
        """
        # Build serializable data dict
        data_dict = {
            "context_data": context_data,
            "component_data": store.get("component_data", {}),
        }

        # Serialize to JSON
        json_data = json.dumps(
            data_dict, default=lambda o: "<not serializable>"
        )

        # Base64 encode for safe storage in DCC node attributes
        encoded = base64.b64encode(json_data.encode("utf8")).decode("ascii")

        return encoded

    def get_current_objects(self):
        """
        Return set of current scene objects.

        Subclass MUST implement this to return scene objects
        before/after import for diff calculation.

        Example (Maya):
            return set(cmds.ls(assemblies=True, long=True))

        Example (Nuke):
            return set([node.name() for node in nuke.allNodes()])
        """
        raise NotImplementedError(
            "Subclass must implement get_current_objects() to return set of scene objects"
        )

    def run_custom(self, store):
        """
        DCC-specific import logic.

        Subclass MUST implement this to perform the actual import/reference
        operation in the DCC.

        *store* contains:
        - context_data
        - component_data
        - result: Collector result with component_path

        Implementation should:
        - Get component_path from store['result']['component_path']
        - Get load_mode from self.options['load_mode']
        - Get load_options from self.options['load_options']
        - Execute DCC import/reference command
        - Return result dict (e.g., {'imported_nodes': [...]})

        Example (Maya reference):
            component_path = store['result']['component_path']
            load_mode = self.options.get('load_mode', 'reference')
            maya_options = self._build_maya_options()
            if load_mode == 'reference':
                nodes = cmds.file(component_path, reference=True, **maya_options)
            return {'imported_nodes': nodes}
        """
        raise NotImplementedError(
            "Subclass must implement run_custom() for DCC-specific import logic"
        )
