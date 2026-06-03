# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_asset_manager.asset import constants as asset_const
from ftrack_framework_nuke import utils as nuke_utils
from ftrack_framework_nuke.asset.dcc_object import NukeDccObject


# Names of the per-Read node knobs that hold the file path; depends on the
# node class.
FILE_KNOB_BY_CLASS = {
    "Read": "file",
    "ReadGeo2": "file",
    "AudioRead": "file",
    "Camera2": "file",
}


class NukeAmUpdateAssetsPlugin(BasePlugin):
    """For each entry in ``self.options['assets']``, query ftrack for the
    latest AssetVersion of the same asset+component, replace the contained
    content node's file path, and rewrite the FtrackAssetInfo knobs on the
    Backdrop. If an asset is already on its latest version, it's skipped.
    """

    name = "nuke.am_update_assets"

    def run(self, store):
        assets = self.options.get("assets") or []
        if not assets:
            self.logger.debug("nuke.am_update_assets: no assets in options")
            return

        updated_count = 0

        for asset_info in assets:
            try:
                if self._update_one(asset_info):
                    updated_count += 1
            except Exception:
                self.logger.exception(
                    "nuke.am_update_assets: failed to update {}".format(
                        asset_info.get(asset_const.ASSET_NAME)
                    )
                )

        self.logger.info(
            "nuke.am_update_assets: updated {} asset(s)".format(updated_count)
        )

    def _update_one(self, asset_info):
        asset_id = asset_info.get(asset_const.ASSET_ID)
        component_name = asset_info.get(asset_const.COMPONENT_NAME)
        current_version_id = asset_info.get(asset_const.VERSION_ID)
        asset_info_id = asset_info.get(asset_const.ASSET_INFO_ID)
        if not (asset_id and component_name and asset_info_id):
            return False

        latest = self.session.query(
            "select id, version, components.id, components.name, "
            "components.component_locations.location.name "
            'from AssetVersion where asset_id is "{}" '
            "and is_latest_version is True".format(asset_id)
        ).first()
        if not latest:
            return False
        if latest["id"] == current_version_id:
            return False

        new_component = None
        for component in latest["components"]:
            if component["name"] == component_name:
                new_component = component
                break
        if new_component is None:
            self.logger.warning(
                "nuke.am_update_assets: component {} not found on latest "
                "version of asset {}".format(component_name, asset_id)
            )
            return False

        location = self.session.pick_location()
        if location.get_component_availability(new_component) != 100.0:
            self.logger.warning(
                "nuke.am_update_assets: component {} not available in "
                "current location".format(new_component["id"])
            )
            return False
        new_component_path = location.get_filesystem_path(new_component)
        if not new_component_path:
            return False

        return self._apply_in_scene(
            asset_info_id, latest, new_component, new_component_path
        )

    @nuke_utils.run_in_main_thread
    def _apply_in_scene(
        self, asset_info_id, latest_version, new_component, new_component_path
    ):
        dcc_object = NukeDccObject(from_id=asset_info_id)
        if not dcc_object.name:
            self.logger.warning(
                "nuke.am_update_assets: no Backdrop for asset_info_id {}".format(
                    asset_info_id
                )
            )
            return False

        ftrack_node = nuke.toNode(dcc_object.name)
        if ftrack_node is None:
            return False

        for contained in ftrack_node.getNodes() or []:
            file_knob_name = FILE_KNOB_BY_CLASS.get(contained.Class())
            if file_knob_name and contained.knob(file_knob_name) is not None:
                contained.knob(file_knob_name).setValue(new_component_path)
                if "reload" in contained.knobs():
                    try:
                        contained.knob("reload").execute()
                    except Exception:
                        pass

        # Rewrite the FtrackAssetInfo knobs on the Backdrop so the next
        # scene-discover reflects the new version.
        updates = {
            asset_const.VERSION_ID: latest_version["id"],
            asset_const.VERSION_NUMBER: latest_version["version"],
            asset_const.COMPONENT_ID: new_component["id"],
            asset_const.COMPONENT_PATH: new_component_path,
            asset_const.IS_LATEST_VERSION: True,
        }
        for knob_name, value in updates.items():
            knob = ftrack_node.knob(knob_name)
            if knob is None:
                continue
            knob.setValue(str(value))

        return True


def register(api_object, **kw):
    """Register plugin to framework"""
    pass
