# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack
import os

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_utils.rpc import JavascriptRPC
import ftrack_framework_aftereffects


class AfterEffectsMovieExporterPlugin(BasePlugin):
    name = "aftereffects_movie_exporter"

    def run(self, store):
        """
        Export the current active sequence to a movie file, save the exported
        path to the store under the component name.
        """
        component_name = self.options.get("component")

        extension = "mp4"

        preset = "H.264 - Match Render Settings - 15 Mbps"

        new_file_path = get_temp_path(filename_extension=extension)

        try:
            # Get existing RPC connection instance
            aftereffects_connection = JavascriptRPC.instance()

            self.logger.debug(
                f"Exporting After Effects movie to {new_file_path}, using preset: {preset}"
            )

            export_result = aftereffects_connection.rpc(
                "render",
                [
                    new_file_path.replace("\\", "/"),
                    preset,
                ],
            )
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(f"Exception exporting the movie: {e}")

        if not export_result or isinstance(export_result, str):
            raise PluginExecutionError(
                f"Error exporting the movie: {export_result}"
            )

        store["components"][component_name]["exported_path"] = new_file_path
