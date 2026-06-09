# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_loader.plugins.base_loader_importer import (
    LoaderImporterPlugin,
)


class CommonPassthroughLoaderImporterPlugin(LoaderImporterPlugin):
    """
    Common passthrough loader importer plugin.

    Does nothing - simply forwards the collector result.
    Useful for testing and simple loader configurations where no DCC node
    creation is required (e.g. ``standalone-loader-test``).

    Overrides ``run`` directly rather than ``run_custom`` so the base
    ``init_and_load`` / ``init_nodes`` path - which requires a real
    ``FtrackObjectManager`` / ``DccObject`` - is bypassed.
    """

    name = "common.passthrough_loader_importer"

    def run(self, store):
        """Pass through - no DCC import performed."""
        result = store.get("result", {}) or {}
        self.logger.debug(
            "Passthrough importer plugin - no import performed "
            "(component_path={})".format(result.get("component_path"))
        )
        store["result"] = result
        return result


def register(api_object, **kw):
    """Register plugin to framework"""
    # Auto-registration handled by framework plugin discovery
    pass
