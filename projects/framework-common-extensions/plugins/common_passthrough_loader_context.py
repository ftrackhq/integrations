# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_loader.plugins.base_loader_context import (
    LoaderContextPlugin,
)


class CommonPassthroughLoaderContextPlugin(LoaderContextPlugin):
    """
    Common passthrough loader context plugin.

    Does no validation - simply passes through.
    Useful for testing and simple loader configurations.
    """

    name = "common.passthrough_loader_context"

    def run(self, store):
        """Pass through - no validation"""
        self.logger.debug(
            "Passthrough context plugin - no validation performed"
        )
        store["result"] = {"status": "success"}
        return store["result"]


def register(api_object, **kw):
    """Register plugin to framework"""
    # Auto-registration handled by framework plugin discovery
    pass
