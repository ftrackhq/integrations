# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_loader import constants as loader_const


class LoaderContextPlugin(BasePlugin):
    """
    Base Loader Context Plugin Class.

    Context plugins validate and prepare context data before loading begins.
    """

    plugin_type = loader_const.PLUGIN_LOADER_CONTEXT_TYPE

    def run(self, store):
        """
        Execute context validation/preparation.

        *store* should contain:
        - context_data: Dict with context information

        Implementations should validate context and update store as needed.
        """
        raise NotImplementedError("Subclass must implement run()")
