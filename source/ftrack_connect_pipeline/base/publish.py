import logging
from collections import OrderedDict

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import base

logger = logging.getLogger(__name__)


class BasePublishUiPipeline(base.BaseUiPipeline):

    def __init__(self, *args, **kwargs):
        super(BasePublishUiPipeline, self).__init__()

        self.mapping = OrderedDict([
            (constants.CONTEXT,    (constants.CONTEXT_PLUGIN_TOPIC, self._on_run_context)),
            (constants.COLLECTORS, (constants.COLLECTORS_PLUGIN_TOPIC, self._on_run_collectors)),
            (constants.VALIDATORS, (constants.VALIDATORS_PLUGIN_TOPIC, self._on_run_validators)),
            (constants.EXTRACTORS, (constants.EXTRACTORS_PLUGIN_TOPIC, self._on_run_extractors)),
            (constants.PUBLISHERS, (constants.PUBLISHERS_PLUGIN_TOPIC, self._on_run_publishers))
        ])

    def _on_run_context(self, widgets):
        raise NotImplementedError()

    def _on_run_collectors(self, widgets):
        raise NotImplementedError()

    def _on_run_validators(self, widgets):
        raise NotImplementedError()

    def _on_run_extractors(self, widgets):
        raise NotImplementedError()

    def _on_run_publishers(self, widgets):
        raise NotImplementedError()

