# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_loader.engines.loader_engine import LoaderEngine


class MayaLoaderEngine(LoaderEngine):
    """Maya-specific Loader Engine"""

    name = "maya_loader_engine"
    engine_types = ["loader"]

    def __init__(
        self,
        plugin_registry,
        session,
        context_id=None,
        on_plugin_executed=None,
    ):
        """Initialize Maya Loader Engine"""
        super(MayaLoaderEngine, self).__init__(
            plugin_registry,
            session,
            context_id,
            on_plugin_executed=on_plugin_executed,
        )
