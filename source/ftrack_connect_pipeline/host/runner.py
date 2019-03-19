import logging
import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.event import EventManager


class PublisherRunner(object):
    def __init__(self, session, ui, host):
        self.order = ['collect', 'validate', 'output']

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

    def _run_plugin(self, plugin, plugin_type, options=None, data=None, context=None):
        plugin_widget_ref = plugin['widget_ref']
        plugin_name = plugin['plugin']

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
                        'options': options,
                        'context':context
                    }
            }
        )
        self.logger.info('running plugin: {}'.format(event))

        plugin_result = self.session.event_hub.publish(
            event,
            synchronous=True
        )

        self._notify_client(plugin_result, plugin_widget_ref)
        return plugin_result

    def _notify_client(self, data, widget_id):
        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_UPDATE_UI,
            data = {
                'widget_ref': widget_id,
                'data': data
            }
        )
        self.logger.info('notifying client: {}'.format(event))

        self.event_manager.publish(
            event,
            remote=True
        )

    def run_context(self, context):
        results = []
        for ctx in context:
            result = self._run_plugin(ctx, 'context', context=ctx['options'])
            results.append(result)

        return results

    def run_component(self, component_stages, context_data):
        self.logger.info('stages: {}'.format(component_stages))
        results = {}
        sorted_stages = dict(sorted(component_stages.items(), key=lambda i: self.order.index(i[0])))
        for stage, plugins in sorted_stages.items():
            for plugin in plugins:
                result = self._run_plugin(plugin, stage, options=plugin['options'])
                self.logger.info('stage: {} result: {}'.format(stage, result))

    def run(self, event):
        data = event['data']
        self.logger.info(data)

        context = data['context']
        context_result = self.run_context(context)

        components = data['components']
        self.logger.info('components : {}'.format(components))
        for component_name, component_stages in components.items():
            component_result = self.run_component(component_stages, context_result)
            self.logger.info('{} : {}'.format(component_name, component_result))

        publisher = data['publish']







