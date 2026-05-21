# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_loader.engines.loader_engine import LoaderEngine


class NukeLoaderEngine(LoaderEngine):
    """Nuke-specific Loader Engine"""

    name = "nuke_loader_engine"
    engine_types = ["loader"]

    def __init__(
        self,
        plugin_registry,
        session,
        context_id=None,
        on_plugin_executed=None,
    ):
        """Initialize Nuke Loader Engine"""
        super(NukeLoaderEngine, self).__init__(
            plugin_registry,
            session,
            context_id,
            on_plugin_executed=on_plugin_executed,
        )
