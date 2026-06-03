# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_asset_manager.asset import constants as asset_const
from ftrack_framework_nuke import utils as nuke_utils
from ftrack_framework_nuke.asset.dcc_object import NukeDccObject


# Per-content-node file knob name. Matches nuke.am_update_assets.
FILE_KNOB_BY_CLASS = {
    "Read": "file",
    "ReadGeo2": "file",
    "AudioRead": "file",
    "Camera2": "file",
}


class NukeAmChangeVersionPlugin(BasePlugin):
    """Apply pending version changes staged by the dialog.

    ``self.options['pending_changes']`` is a list of dicts:
    ``{'asset_info_id': str, 'new_version_id': str, 'component_name': str}``.

    For each, query ftrack for the new AssetVersion + matching component,
    resolve a filesystem path from the picked location, rewrite the
    contained Read node's ``file`` knob and the FtrackAssetInfo knobs on
    the Backdrop. The subsequent ``nuke.am_scene_discover`` step picks up
    the new state.
    """

    name = "nuke.am_change_version"

    def run(self, store):
        pending = self.options.get("pending_changes") or []
        if not pending:
            self.logger.debug(
                "nuke.am_change_version: no pending_changes in options"
            )
            return

        changed_count = 0
        for change in pending:
            try:
                if self._apply_one(change):
                    changed_count += 1
            except Exception:
                self.logger.exception(
                    "nuke.am_change_version: failed to apply change {}".format(
                        change
                    )
                )

        self.logger.info(
            "nuke.am_change_version: applied {} of {} change(s)".format(
                changed_count, len(pending)
            )
        )

    def _apply_one(self, change):
        asset_info_id = change.get("asset_info_id")
        new_version_id = change.get("new_version_id")
        component_name = change.get("component_name")
        if not (asset_info_id and new_version_id and component_name):
            self.logger.warning(
                "nuke.am_change_version: incomplete change {}".format(change)
            )
            return False

        new_version = self.session.query(
            "select id, version, is_latest_version, components.id, "
            "components.name, components.component_locations.location.name "
            'from AssetVersion where id is "{}"'.format(new_version_id)
        ).first()
        if not new_version:
            self.logger.warning(
                "nuke.am_change_version: AssetVersion {} not found".format(
                    new_version_id
                )
            )
            return False

        new_component = None
        for component in new_version["components"]:
            if component["name"] == component_name:
                new_component = component
                break
        if new_component is None:
            self.logger.warning(
                "nuke.am_change_version: component {} not found on version {}".format(
                    component_name, new_version_id
                )
            )
            return False

        location = self.session.pick_location()
        if location.get_component_availability(new_component) != 100.0:
            self.logger.warning(
                "nuke.am_change_version: component {} not available in "
                "current location".format(new_component["id"])
            )
            return False
        new_component_path = location.get_filesystem_path(new_component)
        if not new_component_path:
            return False

        return self._apply_in_scene(
            asset_info_id, new_version, new_component, new_component_path
        )

    @nuke_utils.run_in_main_thread
    def _apply_in_scene(
        self, asset_info_id, new_version, new_component, new_component_path
    ):
        dcc_object = NukeDccObject(from_id=asset_info_id)
        if not dcc_object.name:
            self.logger.warning(
                "nuke.am_change_version: no Backdrop for asset_info_id {}".format(
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

        updates = {
            asset_const.VERSION_ID: new_version["id"],
            asset_const.VERSION_NUMBER: new_version["version"],
            asset_const.COMPONENT_ID: new_component["id"],
            asset_const.COMPONENT_PATH: new_component_path,
            asset_const.IS_LATEST_VERSION: new_version["is_latest_version"],
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
