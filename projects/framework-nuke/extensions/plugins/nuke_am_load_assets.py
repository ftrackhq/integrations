# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os

import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_asset_manager.asset import constants as asset_const
from ftrack_framework_nuke import utils as nuke_utils
from ftrack_framework_nuke.asset import constants as nuke_asset_const
from ftrack_framework_nuke.asset.dcc_object import NukeDccObject


# Component file extension → Nuke content-node class. Mirrors the
# extension groups in ``nuke-render-loader.yaml`` so the choice of node
# type agrees between fresh-load (loader pipeline) and re-load (this
# plugin).
_NODE_TYPE_BY_EXT = {
    ".exr": "Read",
    ".dpx": "Read",
    ".jpg": "Read",
    ".jpeg": "Read",
    ".png": "Read",
    ".tif": "Read",
    ".tiff": "Read",
    ".mov": "Read",
    ".mp4": "Read",
    ".wav": "AudioRead",
    ".aiff": "AudioRead",
    ".aif": "AudioRead",
    ".abc": "ReadGeo2",
}

_FILE_KNOB_BY_CLASS = {
    "Read": "file",
    "AudioRead": "file",
    "ReadGeo2": "file",
    "Camera2": "file",
}


def _node_type_for_path(path):
    if not path:
        return None
    _, ext = os.path.splitext(path)
    return _NODE_TYPE_BY_EXT.get(ext.lower())


class NukeAmLoadAssetsPlugin(BasePlugin):
    """Re-create the content node inside each Backdrop in
    ``self.options['assets']`` whose ``objects_loaded`` is False, and
    flip that knob to ``True``. Skips rows that are already loaded or
    whose Backdrop / component path can't be resolved.
    """

    name = "nuke.am_load_assets"

    @nuke_utils.run_in_main_thread
    def run(self, store):
        assets = self.options.get("assets") or []
        if not assets:
            self.logger.debug("nuke.am_load_assets: no assets in options")
            return

        loaded_count = 0

        # Disable undo tracking for the duration of the batch. Each
        # ``nuke.nodes.<NodeType>`` call would otherwise register an
        # undo entry + walk the undo stack, which dominates the wall
        # time when re-loading several assets at once.
        undo = nuke.Undo()
        undo.disable()
        try:
            for asset_info in assets:
                if asset_info.get(asset_const.OBJECTS_LOADED) in (
                    True,
                    "True",
                ):
                    # Already loaded — nothing to do.
                    continue

                asset_info_id = asset_info.get(asset_const.ASSET_INFO_ID)
                if not asset_info_id:
                    continue

                dcc_object = NukeDccObject(from_id=asset_info_id)
                if not dcc_object.name:
                    self.logger.warning(
                        "nuke.am_load_assets: no Backdrop found for "
                        "asset_info_id={}".format(asset_info_id)
                    )
                    continue

                backdrop = nuke.toNode(dcc_object.name)
                if backdrop is None:
                    continue

                component_path = asset_info.get(asset_const.COMPONENT_PATH)
                node_type = _node_type_for_path(component_path)
                if node_type is None:
                    self.logger.warning(
                        "nuke.am_load_assets: no node-type mapping for "
                        "component_path={!r}".format(component_path)
                    )
                    continue

                # ``nuke.nodes.<NodeType>(file=...)`` is the low-level
                # constructor; significantly faster than
                # ``nuke.createNode`` because it skips the interactive
                # "create node" path (auto-selection, properties bin,
                # undo coalescing) and sets the file knob in the same
                # transaction as creation.
                node_class = getattr(nuke.nodes, node_type, None)
                if node_class is None:
                    self.logger.warning(
                        "nuke.am_load_assets: nuke.nodes has no %s",
                        node_type,
                    )
                    continue

                file_knob = _FILE_KNOB_BY_CLASS.get(node_type, "file")
                content_node = node_class(**{file_knob: component_path})

                # Position the content node at the Backdrop's center so
                # it's visually contained. Read-node default size ~80x40.
                bd_x = backdrop["xpos"].value()
                bd_y = backdrop["ypos"].value()
                bd_w = backdrop["bdwidth"].value()
                bd_h = backdrop["bdheight"].value()
                content_node["xpos"].setValue(int(bd_x + bd_w / 2 - 40))
                content_node["ypos"].setValue(int(bd_y + bd_h / 2 - 20))

                # Refresh the link knob with the new node's name and flip
                # objects_loaded back to True so the AM row updates.
                backdrop.knob(nuke_asset_const.ASSET_LINK).setValue(
                    content_node.name()
                )
                loaded_knob = backdrop.knob(asset_const.OBJECTS_LOADED)
                if loaded_knob is not None:
                    loaded_knob.setValue("True")

                loaded_count += 1
        finally:
            undo.enable()

        self.logger.info(
            "nuke.am_load_assets: loaded {} asset(s)".format(loaded_count)
        )


def register(api_object, **kw):
    """Register plugin to framework"""
    pass
