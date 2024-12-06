# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_utils.rpc import JavascriptRPC


class AfterEffectsProjectCollectorPlugin(BasePlugin):
    name = "aftereffects_project_collector"

    def run(self, store):
        """
        Collect the current project path from After Effects
        and store in the given *store* on "project_name"
        """
        # Get existing RPC connection instance
        aftereffects_connection = JavascriptRPC.instance()

        # Get project data containing the path
        try:
            project_path = aftereffects_connection.rpc("getProjectPath")
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(f"Exception querying the project data: {e}")

        # Will return a path to the .aep file, or an error message if no
        # project is open.

        self.logger.debug(f"Got After Effects project path: {project_path}")

        if not project_path or project_path.startswith("Error:"):
            raise PluginExecutionError(
                "No project data available. Please have"
                " an active work project before you can "
                "publish"
            )

        component_name = self.options.get("component", "main")
        store["components"][component_name]["project_path"] = project_path
