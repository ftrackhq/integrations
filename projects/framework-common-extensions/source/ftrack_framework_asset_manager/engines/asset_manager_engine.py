# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import time

from ftrack_framework_core.engine import BaseEngine
from ftrack_framework_asset_manager.asset import constants as asset_const
from ftrack_framework_asset_manager.asset.ftrack_asset_info import (
    FtrackAssetInfo,
)


class AssetManagerEngine(BaseEngine):
    """Asset Manager Engine that orchestrates asset management operations."""

    name = "asset_manager_engine"
    engine_types = ["asset_manager"]

    FtrackObjectManager = None
    DccObject = None

    @property
    def ftrack_object_manager(self):
        return self._ftrack_object_manager

    @ftrack_object_manager.setter
    def ftrack_object_manager(self, value):
        self._ftrack_object_manager = value

    @property
    def asset_info(self):
        return self._asset_info

    @asset_info.setter
    def asset_info(self, value):
        if not isinstance(value, FtrackAssetInfo):
            value = FtrackAssetInfo(value)
        self._asset_info = value

    @property
    def dcc_object(self):
        return self._dcc_object

    @dcc_object.setter
    def dcc_object(self, value):
        self._dcc_object = value

    def __init__(
        self,
        plugin_registry,
        session,
        context_id=None,
        on_plugin_executed=None,
    ):
        super(AssetManagerEngine, self).__init__(
            plugin_registry,
            session,
            context_id,
            on_plugin_executed=on_plugin_executed,
        )
        self._asset_info = None
        self._dcc_object = None
        self._ftrack_object_manager = None

    def get_store(self):
        return {
            "context_id": self.context_id,
            "asset_entities_list": [],
            "statuses": {},
            "results": {},
        }

    def discover_assets(self, assets=None, options=None, plugin=None):
        start_time = time.time()
        status = "unknown"
        result = []

        result_data = {
            "plugin_name": None,
            "plugin_type": "asset_manager.action",
            "method": "discover_assets",
            "status": status,
            "result": result,
            "execution_time": 0,
            "message": None,
        }

        ftrack_asset_info_list = []

        if ftrack_asset_info_list:
            status = "success"
        else:
            self.logger.debug("No assets in the scene")
            status = "success"

        result = ftrack_asset_info_list

        end_time = time.time()
        total_time = end_time - start_time

        result_data["status"] = status
        result_data["result"] = result
        result_data["execution_time"] = total_time

        return status, result

    def resolve_dependencies(self, context_id, options=None, plugin=None):
        status = "unknown"
        result = []
        message = None

        if not options:
            options = {}
        if plugin:
            plugin_instance_cls = self.plugin_registry.get_one(
                name=plugin["plugin"]
            )
            if plugin_instance_cls:
                plugin_instance = plugin_instance_cls["extension"](
                    options, self.session, self.context_id
                )
                store = {"context_id": context_id}
                try:
                    plugin_instance.run(store)
                    result = store
                    status = "success"
                except Exception as e:
                    status = "error"
                    message = str(e)
                    self.logger.error(message)

        return status, result

    def select_assets(self, assets, options=None, plugin=None):
        statuses = {}
        results = {}
        for i, asset_info in enumerate(assets):
            if i == 0:
                options = options or {}
                options["clear_selection"] = True
            else:
                options["clear_selection"] = False
            try:
                status, result = self.select_asset(asset_info, options, plugin)
            except Exception as e:
                status = "error"
                self.logger.error(
                    "Error selecting asset with version id {} error: {} "
                    "asset_info: {}".format(
                        asset_info[asset_const.VERSION_ID], e, asset_info
                    )
                )
            statuses[asset_info[asset_const.ASSET_INFO_ID]] = (
                status == "success"
            )
            results[asset_info[asset_const.ASSET_INFO_ID]] = result
        return statuses, results

    def select_asset(self, asset_info, options=None, plugin=None):
        raise NotImplementedError(
            "select_asset not implemented for standalone"
        )

    def update_assets(self, assets, options=None, plugin=None):
        statuses = {}
        results = {}
        for asset_info in assets:
            try:
                status, result = self.update_asset(asset_info, options, plugin)
            except Exception as e:
                status = "error"
                self.logger.exception(e)
                self.logger.error(
                    "Error updating asset with version id {} error: {} "
                    "asset_info: {}".format(
                        asset_info[asset_const.VERSION_ID], e, asset_info
                    )
                )
            statuses[asset_info[asset_const.ASSET_INFO_ID]] = (
                status == "success"
            )
            results[asset_info[asset_const.ASSET_INFO_ID]] = result
        return statuses, results

    def update_asset(self, asset_info, options=None, plugin=None):
        status = "unknown"
        result = []

        if not options:
            options = {}
        if plugin:
            plugin_instance_cls = self.plugin_registry.get_one(
                name=plugin["plugin"]
            )
            if plugin_instance_cls:
                plugin_instance = plugin_instance_cls["extension"](
                    plugin.get("options", {}), self.session, self.context_id
                )
                store = dict(asset_info)
                try:
                    plugin_instance.run(store)
                    status = "success"
                    new_version_id = store.get("new_version_id")
                    if new_version_id:
                        options["new_version_id"] = new_version_id
                        status, result = self.change_version(
                            asset_info, options
                        )
                        return status, result
                except Exception as e:
                    status = "error"
                    self.logger.error(
                        "Error executing plugin: {} error: {}".format(
                            plugin, e
                        )
                    )

        return status, result

    def load_assets(self, assets, options=None, plugin=None):
        statuses = {}
        results = {}
        for asset_info in assets:
            try:
                status, result = self.load_asset(asset_info, options, plugin)
            except Exception as e:
                status = "error"
                self.logger.exception(e)
                self.logger.error(
                    "Error loading asset with version id {} error: {} "
                    "asset_info: {}".format(
                        asset_info[asset_const.VERSION_ID], e, asset_info
                    )
                )
            statuses[asset_info[asset_const.ASSET_INFO_ID]] = (
                status == "success"
            )
            results[asset_info[asset_const.ASSET_INFO_ID]] = result
        return statuses, results

    def load_asset(self, asset_info, options=None, plugin=None):
        load_plugin = asset_info[asset_const.ASSET_INFO_OPTIONS]
        if isinstance(load_plugin, str):
            return "success", []

        plugin_data = load_plugin.get("settings", {}).get("data", [])
        plugin_options = load_plugin.get("settings", {}).get("options", {})
        plugin_options["asset_info"] = asset_info
        plugin_context_data = load_plugin.get("settings", {}).get(
            "context_data", {}
        )
        plugin_name = load_plugin.get("pipeline", {}).get("plugin_name")
        plugin_method = "load_asset"

        status = "unknown"
        result = []

        if plugin_name:
            try:
                plugin_instance_cls = self.plugin_registry.get_one(
                    name=plugin_name
                )
                if plugin_instance_cls:
                    plugin_instance = plugin_instance_cls["extension"](
                        plugin_options, self.session, self.context_id
                    )
                    store = {
                        "data": plugin_data,
                        "context_data": plugin_context_data,
                        "method": plugin_method,
                    }
                    plugin_instance.run(store)
                    status = "success"
                    result = store
            except Exception as e:
                status = "error"
                self.logger.error(
                    "Error executing load plugin: {} error: {}".format(
                        plugin_name, e
                    )
                )

        return status, result

    def change_version(self, asset_info, options, plugin=None):
        status = "unknown"
        result = {}

        new_version_id = options.get("new_version_id")
        if not new_version_id:
            status = "error"
            return status, result

        try:
            remove_status, remove_result = self.remove_asset(
                asset_info=asset_info, options=None, plugin=None
            )
        except Exception as e:
            self.logger.exception(e)
            return "error", {}

        if remove_status != "success":
            return remove_status, {}

        try:
            # session.get + populate, not `select … from AssetVersion
            # where id is "{}"`.format(): ftrack-api has no parametric
            # queries, and Aikido's Bandit-B608 SAST rule fires on any
            # `.format()` whose format string contains `from`. populate
            # preserves the eager-loading the original `select` provided
            # — required so the components/locations loop below doesn't
            # devolve into an N+1 of lazy auto-population queries.
            asset_version_entity = self.session.get(
                "AssetVersion", new_version_id
            )
            if asset_version_entity is None:
                raise Exception(
                    "AssetVersion {} not found".format(new_version_id)
                )
            self.session.populate(
                asset_version_entity,
                "version, "
                "components.name, "
                "components.component_locations.location.name",
            )

            version_number = int(asset_version_entity["version"])
            version_id = asset_version_entity["id"]
            location = asset_version_entity.session.pick_location()
            component_path = None
            component_id = None

            component_name = asset_info.get(asset_const.COMPONENT_NAME)
            for component in asset_version_entity["components"]:
                if component["name"] == component_name:
                    if location.get_component_availability(component) == 100.0:
                        component_path = location.get_filesystem_path(
                            component
                        )
                        component_id = component["id"]

            if component_path is None:
                raise Exception(
                    "Component {}({}) @ version {}({}) is not available "
                    "in location {}({})".format(
                        component_name,
                        component_id or "?",
                        version_number,
                        version_id,
                        location["name"],
                        location["id"],
                    )
                )

            asset_info_options = asset_info.get(
                asset_const.ASSET_INFO_OPTIONS, {}
            )
            if isinstance(asset_info_options, str):
                asset_info_options = {}

            new_asset_info = FtrackAssetInfo.create(
                asset_version_entity,
                component_name,
                component_path=component_path,
                component_id=component_id,
                load_mode=asset_info.get(asset_const.LOAD_MODE, "Not Set"),
                asset_info_options=asset_info_options,
                objects_loaded=asset_info.get(
                    asset_const.OBJECTS_LOADED, False
                ),
                reference_object=asset_info.get(asset_const.REFERENCE_OBJECT),
            )

            self.asset_info = new_asset_info
            result[asset_info[asset_const.ASSET_INFO_ID]] = new_asset_info
            status = "success"

        except Exception as e:
            status = "error"
            self.logger.error(
                "Error changing version of asset with version id {} "
                "error: {} asset_info: {}".format(
                    asset_info[asset_const.VERSION_ID], e, asset_info
                )
            )
            return status, result

        return status, result

    def unload_assets(self, assets, options=None, plugin=None):
        statuses = {}
        results = {}
        for asset_info in assets:
            try:
                status, result = self.unload_asset(asset_info, options, plugin)
            except Exception as e:
                status = "error"
                self.logger.exception(e)
                self.logger.error(
                    "Error unloading asset with version id {} error: {} "
                    "asset_info: {}".format(
                        asset_info[asset_const.VERSION_ID], e, asset_info
                    )
                )
            statuses[asset_info[asset_const.ASSET_INFO_ID]] = (
                status == "success"
            )
            results[asset_info[asset_const.ASSET_INFO_ID]] = result
        return statuses, results

    def unload_asset(self, asset_info, options=None, plugin=None):
        return "success", True

    def remove_assets(self, assets, options=None, plugin=None):
        statuses = {}
        results = {}
        for asset_info in assets:
            try:
                status, result = self.remove_asset(asset_info, options, plugin)
            except Exception as e:
                status = "error"
                self.logger.exception(e)
                self.logger.error(
                    "Error removing asset with version id {} error: {} "
                    "asset_info: {}".format(
                        asset_info[asset_const.VERSION_ID], e, asset_info
                    )
                )
            statuses[asset_info[asset_const.ASSET_INFO_ID]] = (
                status == "success"
            )
            results[asset_info[asset_const.ASSET_INFO_ID]] = result
        return statuses, results

    def remove_asset(self, asset_info, options=None, plugin=None):
        return "success", True

    def run(self, data):
        method = data.get("method", "")
        plugin = data.get("plugin", None)
        arg = data.get("assets", data.get("context_id"))
        options = data.get("options", {})

        result = None

        if hasattr(self, method):
            callback_fn = getattr(self, method)
            status, result = callback_fn(arg, options, plugin)
            if isinstance(status, dict):
                if not all(status.values()):
                    raise Exception(
                        "An error occurred during the execution of "
                        "the method: {}".format(method)
                    )
            else:
                if status != "success":
                    raise Exception(
                        "An error occurred during the execution of "
                        'the method "{}"'.format(method)
                    )
        elif plugin:
            plugin_name = plugin.get("plugin")
            if plugin_name:
                self.run_plugin(
                    plugin_name,
                    self.get_store(),
                    plugin.get("options", {}),
                )

        return result
