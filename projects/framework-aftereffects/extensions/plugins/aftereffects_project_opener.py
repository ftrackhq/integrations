# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_utils.rpc import JavascriptRPC


class AfterEffectsProjectOpenerPlugin(BasePlugin):
    name = "aftereffects_project_opener"

    def run(self, store):
        """
        Expects collected_path in the <component_name> key of the given *store*,
        opens it in After Effects and stores the result as 'open_result' under the
        <component_name> key of the given *store*.
        """
        component_name = self.options.get("component")

        collected_path = store["components"][component_name].get("collected_path")

        if not collected_path:
            raise PluginExecutionError(f"No path provided to open!")

        if not os.path.exists(collected_path):
            raise PluginExecutionError(f'Project "{collected_path}" does not exist!')

        try:
            # Get existing RPC connection instance
            aftereffects_connection = JavascriptRPC.instance()

            self.logger.debug(
                f"Telling After Effects to open project from: {collected_path}"
            )

            # Tell After Effects to open document, convert backlash to forward slash
            # to prevent JSON encoding errors.
            open_result = aftereffects_connection.rpc(
                "openProject",
                [collected_path.replace("\\", "/")],
            )

        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f"Exception telling After Effects to open project: {e}"
            )

        if not open_result or isinstance(open_result, str):
            raise PluginExecutionError(
                f"Error opening the project in After Effects: {open_result}"
            )

        store["components"][component_name]["open_result"] = open_result
