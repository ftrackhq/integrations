import logging
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.ui import base

logger = logging.getLogger(__name__)


class BaseLoadUiFramework(base.BaseUiFramework):
    def __init__(self, *args, **kwargs):
        super(BaseLoadUiFramework, self).__init__()

        self.mapping = {
            constants.CONTEXT: (constants.CONTEXT_PLUGIN_TOPIC, self._on_run_context),
            constants.COMPONENTS : (constants.COMPONENTS_PLUGIN_TOPIC, self._on_run_components),
            constants.INTEGRATORS : (constants.INTEGRATORS_PLUGIN_TOPIC, self._on_run_integrators)
        }
        self.stack_exec_order = constants.LOAD_ORDER

    @staticmethod
    def _on_run_context(widgets, previous_results=None):
        raise NotImplementedError()

    @staticmethod
    def _on_run_components(widgets, previous_results=None):
        raise NotImplementedError()

    @staticmethod
    def _on_run_integrators(widgets, previous_results=None):
        raise NotImplementedError()