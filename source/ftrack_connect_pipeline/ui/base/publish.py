import logging
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.ui import base

logger = logging.getLogger(__name__)


class BasePublishUiFramework(base.BaseUiFramework):

    def __init__(self, *args, **kwargs):
        super(BasePublishUiFramework, self).__init__()

        self.mapping = {
            constants.CONTEXT:    (constants.CONTEXT_PLUGIN_TOPIC, self._on_run_context),
            constants.COLLECTORS: (constants.COLLECTORS_PLUGIN_TOPIC, self._on_run_collectors),
            constants.VALIDATORS: (constants.VALIDATORS_PLUGIN_TOPIC, self._on_run_validators),
            constants.EXTRACTORS: (constants.EXTRACTORS_PLUGIN_TOPIC, self._on_run_extractors),
            constants.PUBLISHERS: (constants.PUBLISHERS_PLUGIN_TOPIC, self._on_run_publishers)
        }

    @staticmethod
    def _on_run_context(widgets, previous_results=None):
        raise NotImplementedError()

    @staticmethod
    def _on_run_collectors(widgets, previous_results=None):
        raise NotImplementedError()

    @staticmethod
    def _on_run_validators(widgets, previous_results=None):
        raise NotImplementedError()

    @staticmethod
    def _on_run_extractors(widgets, previous_results=None):
        raise NotImplementedError()

    @staticmethod
    def _on_run_publishers(widgets, previous_results=None):
        raise NotImplementedError()

