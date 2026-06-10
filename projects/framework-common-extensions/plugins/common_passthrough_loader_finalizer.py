# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_loader.plugins.base_loader_finalizer import (
    LoaderFinalizerPlugin,
)


class CommonPassthroughLoaderFinalizerPlugin(LoaderFinalizerPlugin):
    """
    Common passthrough loader finalizer plugin.

    Does nothing - simply passes through.
    Useful for testing and simple loader configurations.
    """

    name = "common.passthrough_loader_finalizer"

    def run(self, store):
        """Pass through - no finalization operations"""
        self.logger.debug(
            "Passthrough finalizer plugin - no operations performed"
        )
        store["result"] = store.get("result", {})
        return store["result"]


def register(api_object, **kw):
    """Register plugin to framework"""
    # Auto-registration handled by framework plugin discovery
    pass
