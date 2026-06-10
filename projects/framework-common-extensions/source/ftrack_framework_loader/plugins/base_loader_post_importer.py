# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_loader import constants as loader_const


class LoaderPostImporterPlugin(BasePlugin):
    """
    Base Loader Post Importer Plugin Class.

    Post importer plugins perform operations after component import.
    """

    plugin_type = loader_const.PLUGIN_LOADER_POST_IMPORTER_TYPE

    def run(self, store):
        """
        Execute post-import operations for a component.

        *store* contains:
        - context_data: Context information
        - component_data: Component information
        - result: Importer result with asset_info, dcc_object, loaded_objects
        """
        raise NotImplementedError("Subclass must implement run()")
