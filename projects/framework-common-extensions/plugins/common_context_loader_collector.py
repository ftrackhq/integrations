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

    Reads (from ``self.options``):
    - ``asset_version_id``: written by the dialog after the user picks a
      version on the top-level ``common.loader_asset_picker``.
    - ``component``: written by the dialog when the user enables a row;
      the specific component name to load from the AssetVersion.
    - ``file_types``: optional list of extensions the parent group knows how
      to import (flattened in by the engine from the group's
      ``options.file_types``). Used to validate that the resolved component's
      extension is one this group is configured for. ``file_formats`` is
      still read as a legacy fallback.

    Stores the resolved component path, name, and id in ``store['result']``.
    Also populates ``store['context_data']`` and ``store['component_data']``
    with the keys the base importer's ``init_nodes()`` reads when building
    its ``FtrackAssetInfo`` and DCC tracking node.
    """

    name = "common.context_loader_collector"

    def run(self, store):
        """Collect the component path from ftrack."""
        asset_version_id = self.options.get("asset_version_id")
        if not asset_version_id:
            raise ValueError("asset_version_id required in plugin options")

        component_name = self.options.get("component")
        if not component_name:
            raise ValueError("component required in plugin options")

        # Accept either the new ``file_types`` key or the legacy
        # ``file_formats``; both are list-of-extension semantics.
        file_types = (
            self.options.get("file_types")
            or self.options.get("file_formats")
            or []
        )
        file_types = [self._normalize_extension(ft) for ft in file_types]

        self.logger.debug(
            f"Collecting component: {component_name} for version: "
            f"{asset_version_id}, file_types: {file_types}"
        )

        # session.get + populate instead of `AssetVersion where id is
        # "{}"`.format(): same family as the Aikido-B608 fixes elsewhere
        # in this PR (B608 itself doesn't fire here because the format
        # string lacks the `from` keyword, but the structural fix
        # removes the interpolation entirely). populate eagerly loads
        # everything the component loop below reads, so we don't fall
        # back to N+1 lazy auto-population.
        asset_version_entity = self.session.get(
            "AssetVersion", asset_version_id
        )
        if asset_version_entity is None:
            raise RuntimeError(f'AssetVersion "{asset_version_id}" not found')
        self.session.populate(
            asset_version_entity,
            "asset_id, "
            "components.name, "
            "components.component_locations.location.name",
        )

        component_path = None
        component_id = None

        for component in asset_version_entity["components"]:
            if component["name"] != component_name:
                continue

            # pick_location(component) returns the highest-priority location
            # that actually holds this component; the dialog has already
            # filtered out components whose only location is ftrack.server,
            # but check defensively here too.
            location = self.session.pick_location(component)
            if not location or location["name"] == "ftrack.server":
                raise RuntimeError(
                    f'Component "{component_name}" on version '
                    f"{asset_version_id} is not available in a local "
                    f"location."
                )
            path = location.get_filesystem_path(component)

            if file_types:
                file_ext = self._normalize_extension(
                    os.path.splitext(path)[-1]
                )
                if file_ext not in file_types:
                    self.logger.warning(
                        f"Component path {path} has extension {file_ext} "
                        f"not in accepted file_types {file_types}"
                    )
                    continue

            component_path = path
            component_id = component["id"]
            break

        if not component_path:
            raise RuntimeError(
                f'No component found with name "{component_name}" '
                f"for version {asset_version_id}"
            )

        self.logger.info(f"Collected component path: {component_path}")

        result = {
            asset_const.COMPONENT_PATH: component_path,
            asset_const.COMPONENT_NAME: component_name,
            asset_const.COMPONENT_ID: component_id,
        }

        store["context_data"] = {
            asset_const.VERSION_ID: asset_version_id,
            "asset_version_id": asset_version_id,
            asset_const.ASSET_ID: asset_version_entity["asset_id"],
            "context_id": self.context_id,
        }
        store["component_data"] = {
            asset_const.COMPONENT_NAME: component_name,
            asset_const.COMPONENT_ID: component_id,
        }

        store["result"] = result
        return result

    @staticmethod
    def _normalize_extension(value):
        """Normalize a filetype string to a lowercased leading-dot form so
        ``.ABC``, ``abc``, and ``.abc`` all compare equal."""
        if not value:
            return ""
        value = value.lower()
        if not value.startswith("."):
            value = "." + value
        return value


def register(api_object, **kw):
    """Register plugin to framework"""
    # Auto-registration handled by framework plugin discovery
    pass
