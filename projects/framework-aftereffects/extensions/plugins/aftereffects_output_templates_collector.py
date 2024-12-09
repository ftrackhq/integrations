# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_utils.rpc import JavascriptRPC


class AfterEffectsOutputTemplatesCollectorPlugin(BasePlugin):
    name = "aftereffects_output_templates_collector"

    def ui_hook(self, payload):
        """
        Return all available templated aviable in Local After Effects Installation
        """
        # Get existing RPC connection instance
        aftereffects_connection = JavascriptRPC.instance()

        # Get project data containing the path
        try:
            templates = aftereffects_connection.rpc(
                "getOutputModuleTemplateNames"
            ).split(",")
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f"Exception querying the templates data: {e}"
            )
        # Will return a list of template, or an error message if no
        # templates aviable.

        self.logger.debug(f"Got After Effects templates: {templates}")

        return templates

    def run(self, store):
        """
        Set the selected template name to the *store*
        """
        try:
            template_name = self.options["template_name"]
        except Exception as error:
            raise PluginExecutionError(f"Provide template_name: {error}")

        component_name = self.options.get("component", "main")
        store["components"][component_name]["template_name"] = template_name
