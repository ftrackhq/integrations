import logging
import ftrack_api

logger = logging.getLogger(__name__)


class BaseUiFramework(object):
    widget_suffix = None

    def __init__(self, *args, **kwargs):
        super(BaseUiFramework, self).__init__()

        self.mapping = {}
        self.session = ftrack_api.Session(auto_connect_event_hub=True)

    def build(self):
        raise NotImplementedError()

    def fetch_widget(self, plugin, base_topic, plugin_type):
        ui = plugin.get('ui', 'default.{}'.format(self.widget_suffix))
        mytopic = base_topic.format(ui)

        # filter widgets which cannot be loaded in this host.
        if self.widget_suffix not in mytopic:
            logger.warning('cannot load widget topic of type {} for {}'.format(
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
        logger.info('UI WIDGET : {} FOUND: {}'.format(mytopic, result_widget))
        if result_widget:
            return result_widget[0]