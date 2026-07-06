# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack
import os
import shutil

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_framework_harmony.utils.tcp_rpc import TCPRPCClient


class HarmonySceneExporterPlugin(BasePlugin):
    name = "harmony_scene_exporter"

    def run(self, store):
        """
        Save the current Harmony scene and package its folder into a zip
        archive, storing the path in *store* under the component name so
        it can be published as a scene snapshot (openable by the opener).
        """
        component_name = self.options.get("component")

        try:
            harmony_connection = TCPRPCClient.instance()

            # Persist the scene so the on-disk folder is up to date.
            # RPC timeouts are in milliseconds.
            save_response = harmony_connection.rpc("saveScene", timeout=120000)
            if "result" not in save_response:
                raise PluginExecutionError(
                    f"Error saving the scene: "
                    f"{save_response.get('error_message')}"
                )

            scene_path_response = harmony_connection.rpc(
                "getScenePath", timeout=30000
            )
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f"Exception saving the Harmony scene: {e}"
            )

        if "result" not in scene_path_response:
            raise PluginExecutionError(
                f"Error resolving the scene path: "
                f"{scene_path_response.get('error_message')}"
            )

        scene_folder = scene_path_response["result"]
        if not scene_folder or not os.path.isdir(scene_folder):
            raise PluginExecutionError(
                f"Harmony scene folder does not exist: {scene_folder}"
            )

        # Package the whole scene folder into a zip archive.
        # get_temp_path returns a unique .zip path; make_archive appends
        # the extension to the base name, so strip it first.
        zip_path = get_temp_path(filename_extension="zip")
        archive_base = zip_path[: -len(".zip")]

        self.logger.debug(
            f"Packaging Harmony scene {scene_folder} into {zip_path}"
        )
        shutil.make_archive(archive_base, "zip", scene_folder)

        store["components"][component_name]["exported_path"] = zip_path
