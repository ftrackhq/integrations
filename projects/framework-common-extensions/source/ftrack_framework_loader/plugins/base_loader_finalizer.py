# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_loader import constants as loader_const


class LoaderFinalizerPlugin(BasePlugin):
    """
    Base Loader Finalizer Plugin Class.

    Finalizer plugins perform finalization operations after all components loaded.
    """

    plugin_type = loader_const.PLUGIN_LOADER_FINALIZER_TYPE

    def run(self, store):
        """
        Execute finalization operations.

        *store* contains results from all component loads.

        Implementation can access:
        - store['component_results']: Dict of component results
        - store['context_data']: Context information
        """
        raise NotImplementedError("Subclass must implement run()")
