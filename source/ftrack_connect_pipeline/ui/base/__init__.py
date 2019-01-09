import logging
import ftrack_api
import itertools

logger = logging.getLogger(__name__)


class BaseUiFramework(object):
    widget_suffix = None

    def __init__(self, *args, **kwargs):
        super(BaseUiFramework, self).__init__()

        self.mapping = {}
        self.session = ftrack_api.Session(auto_connect_event_hub=True)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

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

    def fetch_widget(self, plugin, base_topic, plugin_type):
        ui = plugin.get('ui', 'default.{}'.format(self.widget_suffix))
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
        call_topic = self.mapping[plugin_type][0].format(plugin['call'])

        result_widget = self.session.event_hub.publish(
            ftrack_api.event.base.Event(
                topic=mytopic,
                data={
                    'options': plugin_options,
                    'name': plugin_name,
                    'description': description,
                    'call_topic': call_topic
                }
            ),
            synchronous=True
        )
        self.logger.info('UI WIDGET : {} FOUND: {}'.format(mytopic, result_widget))
        if result_widget:
            return result_widget[0]