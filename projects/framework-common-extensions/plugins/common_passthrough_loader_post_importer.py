# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_loader.plugins.base_loader_post_importer import (
    LoaderPostImporterPlugin,
)


class CommonPassthroughLoaderPostImporterPlugin(LoaderPostImporterPlugin):
    """
    Common passthrough loader post importer plugin.

    Does nothing - simply passes through.
    Useful for testing and simple loader configurations.
    """

    name = "common.passthrough_loader_post_importer"

    def run(self, store):
        """Pass through - no post-import operations"""
        self.logger.debug(
            "Passthrough post importer plugin - no operations performed"
        )
        store["result"] = store.get("result", {})
        return store["result"]


def register(api_object, **kw):
    """Register plugin to framework"""
    # Auto-registration handled by framework plugin discovery
    pass
