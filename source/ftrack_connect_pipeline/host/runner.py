import logging
import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.event import EventManager


class PublisherRunner(object):
    def __init__(self, session, host,  ui):
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
        plugin_name = plugin['plugin']

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_TOPIC,
            data={
                'pipeline': {
                    'plugin_name': plugin_name,
                    'plugin_type': plugin_type,
                    'type': 'plugin',
                    'host': self.host,
                },
                'settings':
                    {
                        'data': data,
                        'options': options,
                        'context': context
                    }
            }
        )

        plugin_result = self.session.event_hub.publish(
            event,
            synchronous=True
        )

        plugin_widget_ref = plugin['widget_ref']
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

        self.event_manager.publish(
            event,
            remote=True
        )

    def run_context(self, context):
        results = {}
        for ctx in context:
            result = self._run_plugin(ctx, 'context', context=ctx['options'])
            results.update(result)

        return results

    def run_component(self, component_stages, context_data):
        results = {}
        sorted_stages = dict(sorted(component_stages.items(), key=lambda i: self.order.index(i[0])))
        for stage, plugins in sorted_stages.items():
            collected_data = results.get(constants.COLLECTORS,[])
            stages_result = []
            validators = results.get(constants.VALIDATORS)

            if validators and not all(validators):
                raise Exception('Validation Error')

            for plugin in plugins:
                result = self._run_plugin(plugin, stage, data=collected_data, options=plugin['options'], context=context_data)
                self.logger.info('result of {}-{} = {}'.format(stage, plugin['name'], result))

                if len(result) > 0 and isinstance(result[0], list):
                    result = result[0]

                stages_result += result

            results[stage] = stages_result

        return results

    def run(self, event):
        data = event['data']
        self.logger.info(data)

        context = data['context']
        context_result = self.run_context(context)

        components = data['components']
        for component_name, component_stages in components.items():
            component_result = self.run_component(component_stages, context_result)
            self.logger.info('{} : {}'.format(component_name, component_result))

        publish = data['publish']







