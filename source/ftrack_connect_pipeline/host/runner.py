import logging
import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.event import EventManager


class PublisherRunner(object):
    def __init__(self, session, ui, host):
        self.session = session
        self.host = host
        self.ui = ui

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.event_manager = EventManager(session)

        session.event_hub.subscribe(
            'topic={}'.format(constants.PIPELINE_RUN_PUBLISHER),
            self.run
        )

    def _run_plugin(self, plugin, plugin_type, data=None, context=None):
        plugin_widget_ref = plugin['widget_ref']
        plugin_name = plugin['plugin']
        plugin_options = plugin.get('options', {})

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_TOPIC,
            data={
                'pipeline': {
                    'plugin_name': plugin_name,
                    'plugin_type': plugin_type,
                    'type': 'plugin',
                    'ui': self.ui,
                    'host': self.host,
                },
                'settings':
                    {
                        'data': data,
                        'options': plugin_options,
                        'context':context
                    }
            }
        )

        plugin_result = self.session.event_hub.publish(
            event,
            synchronous=True
        )

        self._notify_client(plugin_result, plugin_widget_ref)
        return plugin_result

    def _notify_client(self, data, widget_id):
        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_UPDATE_UI,
            data=data
        )
        self.event_manager.publish(
            event,
            remote=True
        )

    def run_context(self, context):
        results = []
        for ctx in context:
            result = self._run_plugin(ctx, 'context')
            results.append(result)

        return results

    def run(self, event):
        data = event['data']
        self.logger.info(data)

        context = data['context']
        context_result = self.run_context(context)

        components = data['components']
        publisher = data['publisher']







