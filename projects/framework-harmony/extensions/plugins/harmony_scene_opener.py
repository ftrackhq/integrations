# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack
import os
import zipfile

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_framework_harmony.utils.tcp_rpc import TCPRPCClient


class HarmonySceneOpenerPlugin(BasePlugin):
    name = "harmony_scene_opener"

    def run(self, store):
        """
        Unpack the collected scene snapshot zip and tell Harmony to open
        the contained scene, using the collected_path stored in *store*.
        """
        component_name = self.options.get("component")

        collected_path = store["components"][component_name].get(
            "collected_path"
        )
        if not collected_path:
            raise PluginExecutionError("No path provided to open!")

        # The snapshot is a zip of the Harmony scene folder. Unpack it to
        # a stable location and locate the .xstage to open.
        extract_dir = get_temp_path(is_directory=True)
        try:
            with zipfile.ZipFile(collected_path) as archive:
                archive.extractall(extract_dir)
        except Exception as error:
            raise PluginExecutionError(
                f"Could not unpack the scene snapshot: {error}"
            )

        xstage_path = None
        for root, _dirs, files in os.walk(extract_dir):
            for filename in files:
                if filename.endswith(".xstage"):
                    xstage_path = os.path.join(root, filename)
                    break
            if xstage_path:
                break

        if not xstage_path:
            raise PluginExecutionError(
                f"No .xstage scene found in snapshot: {collected_path}"
            )

        try:
            harmony_connection = TCPRPCClient.instance()
            open_response = harmony_connection.rpc(
                "openScene",
                [xstage_path.replace("\\", "/")],
                timeout=-1,  # Opening/closing a scene can take a while.
            )
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(f"Exception opening the scene: {e}")

        if "result" not in open_response:
            raise PluginExecutionError(
                f"Error opening the scene: "
                f"{open_response.get('error_message')}"
            )

        self.logger.debug(f"Harmony scene opened. Path: {xstage_path}")
        store["components"][component_name]["open_result"] = xstage_path
