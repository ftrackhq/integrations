import logging
from collections import OrderedDict
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import base

logger = logging.getLogger(__name__)


class BaseLoadUiPipeline(base.BaseUiPipeline):
    def __init__(self, *args, **kwargs):
        super(BaseLoadUiPipeline, self).__init__()

        self.mapping = OrderedDict([
            (constants.CONTEXT,  (constants.CONTEXT_PLUGIN_TOPIC, self._on_run_context)),
            (constants.IMPORTERS,  (constants.IMPORTERS_PLUGIN_TOPIC, self._on_run_importers))
        ])


    def _on_run_context(self, widgets):
        raise NotImplementedError()

    def _on_run_importers(self, widgets):
        raise NotImplementedError()