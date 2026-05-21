# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_loader import constants as loader_const


class LoaderCollectorPlugin(BasePlugin):
    """
    Base Loader Collector Plugin Class.

    Collector plugins query ftrack for component paths to load.
    """

    plugin_type = loader_const.PLUGIN_LOADER_COLLECTOR_TYPE

    def run(self, store):
        """
        Collect component paths from ftrack.

        *store* should contain:
        - context_data: Dict with version_id, etc.
        - component_data: Dict with component_name, file_formats, etc.

        Implementation should:
        - Query ftrack for AssetVersion components
        - Filter by component_name and file_formats
        - Store results in store['result'] as dict with keys:
          - component_path: File path
          - component_name: Component name
          - component_id: Component ID
        """
        raise NotImplementedError("Subclass must implement run()")
