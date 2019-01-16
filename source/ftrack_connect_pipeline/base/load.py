import logging
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import base

logger = logging.getLogger(__name__)


class BaseLoadUiPipeline(base.BaseUiPipeline):
    def __init__(self, *args, **kwargs):
        super(BaseLoadUiPipeline, self).__init__()

        self.mapping = {
            constants.CONTEXT: (constants.CONTEXT_PLUGIN_TOPIC, self._on_run_context),
            constants.COMPONENTS : (constants.COMPONENTS_PLUGIN_TOPIC, self._on_run_components),
            constants.IMPORTERS : (constants.IMPORTERS_PLUGIN_TOPIC, self._on_run_importers)
        }
        self.stack_exec_order = constants.LOAD_ORDER

    def _on_run_context(self, widgets, previous_results=None):
        raise NotImplementedError()

    def _on_run_components(self, widgets, previous_results=None):
        raise NotImplementedError()

    def _on_run_importers(self, widgets, previous_results=None):
        raise NotImplementedError()