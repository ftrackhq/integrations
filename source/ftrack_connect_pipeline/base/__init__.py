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
        self._task_results = {}

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

    def run_async(self, event_list):
        self.logger.debug(
            'Sending event list {} to host'.format(event_list)
        )

        self.session.event_hub.publish(
            ftrack_api.event.base.Event(
                topic=constants.PIPELINE_RUN_TOPIC,
                data={'event_list': event_list}
            ),
            on_reply=self.on_handle_async_reply
        )

    def fetch_widget(self, plugin, base_topic, plugin_type):
        ui = plugin.get('plugin_ui', 'default.{}'.format(self.widget_suffix))
        mytopic = base_topic.format(ui)

        # filter widgets which cannot be loaded in this host.
        if self.widget_suffix not in mytopic:
            self.logger.warning('cannot load widget topic of type {} for {}'.format(
                mytopic, self.widget_suffix
            ))
            return

        plugin_options = plugin.get('options', {})
        plugin_name = plugin.get('name', 'no name provided')
        description = plugin.get('description', 'No description provided')
        plugin_topic = self.mapping[plugin_type][0].format(plugin['plugin'])

        result_widget = self.session.event_hub.publish(
            ftrack_api.event.base.Event(
                topic=mytopic,
                data={
                    'options': plugin_options,
                    'name': plugin_name,
                    'description': description,
                    'plugin_topic': plugin_topic
                }
            ),
            synchronous=True
        )
        self.logger.info('UI WIDGET : {} FOUND: {}'.format(mytopic, result_widget))
        if result_widget:
            return result_widget[0]