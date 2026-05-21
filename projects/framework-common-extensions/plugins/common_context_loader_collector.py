# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os

from ftrack_framework_loader.plugins.base_loader_collector import (
    LoaderCollectorPlugin,
)
from ftrack_framework_asset_manager.asset import constants as asset_const


class CommonContextLoaderCollectorPlugin(LoaderCollectorPlugin):
    """
    Common loader collector plugin.

    Collects component paths from ftrack AssetVersion based on:
    - version_id from context_data
    - component_name from component_data
    - file_formats from options (optional filter)
    """

    name = "common.context_loader_collector"

    def run(self, store):
        """
        Collect component paths from ftrack.

        *store* should contain:
        - context_data: Dict with version_id
        - component_data: Dict with component_name, file_formats

        Stores result in store['result'] as dict:
        - component_path: File path
        - component_name: Component name
        - component_id: Component ID
        """
        context_data = store.get("context_data", {})
        component_data = store.get("component_data", {})

        # Get version_id from context
        version_id = context_data.get("version_id")
        if not version_id:
            raise ValueError("version_id required in context_data")

        # Get component name
        component_name = component_data.get("component_name")
        if not component_name:
            raise ValueError("component_name required in component_data")

        # Get optional file format filter from options or component_data
        file_formats = self.options.get(
            "file_formats", component_data.get("file_formats", [])
        )

        self.logger.debug(
            f"Collecting component: {component_name} for version: {version_id}, "
            f"file_formats: {file_formats}"
        )

        # Query ftrack for AssetVersion
        asset_version_entity = self.session.query(
            'AssetVersion where id is "{}"'.format(version_id)
        ).one()

        # Find matching component
        location = self.session.pick_location()
        component_path = None
        component_id = None

        for component in asset_version_entity["components"]:
            if component["name"] == component_name:
                # Get filesystem path
                path = location.get_filesystem_path(component)

                # Check file format filter
                if file_formats:
                    file_ext = os.path.splitext(path)[-1]
                    if file_ext not in file_formats:
                        self.logger.warning(
                            f"Component path {path} has extension {file_ext} "
                            f"not in accepted formats {file_formats}"
                        )
                        continue

                component_path = path
                component_id = component["id"]
                break

        if not component_path:
            raise RuntimeError(
                f'No component found with name "{component_name}" '
                f"for version {version_id}"
            )

        self.logger.info(f"Collected component path: {component_path}")

        result = {
            asset_const.COMPONENT_PATH: component_path,
            asset_const.COMPONENT_NAME: component_name,
            asset_const.COMPONENT_ID: component_id,
        }

        store["result"] = result
        return result


def register(api_object, **kw):
    """Register plugin to framework"""
    # Auto-registration handled by framework plugin discovery
    pass
