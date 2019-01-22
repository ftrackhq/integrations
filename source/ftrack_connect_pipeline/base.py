import logging
import ftrack_api
import itertools

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import get_registered_assets, register_assets

logger = logging.getLogger(__name__)


class BaseUiPipeline(object):
    widget_suffix = None

    @property
    def asset_type(self):
        return self._current_asset_type

    def __init__(self, *args, **kwargs):
        super(BaseUiPipeline, self).__init__()

        self.stage_type = None
        self.mapping = {}
        self._stages_results = {}

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.session = ftrack_api.Session(auto_connect_event_hub=True)

        register_assets(self.session)
        self._asset_configs = get_registered_assets('Task')
        self._current_asset_type = None

    @staticmethod
    def merge_list(list_data):
        logger.info('Merging {} '.format(list_data))
        result = list(set(itertools.chain.from_iterable(list_data)))
        logger.info('into {}'.format(result))
        return result

    @staticmethod
    def merge_dict(dict_data):
        logger.info('Merging {} '.format(dict_data))
        result = {k: v for d in dict_data for k, v in d.items()}
        logger.info('into {}'.format(result))
        return result

    def build(self):
        raise NotImplementedError()
