# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import logging
import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.event import EventManager


class PublisherRunner(object):

    @property
    def hostid(self):
        return self._hostid

    @property
    def host(self):
        return self._host

    @property
    def ui(self):
        return self._ui

    def __init__(self, session, package_definitions, host,  ui, hostid):

        self.__remote_events = bool(os.environ.get(
            constants.PIPELINE_REMOTE_EVENTS_ENV, False
        ))

        self.component_stages_order = [
            constants.COLLECT,
            constants.VALIDATE,
            constants.OUTPUT]

        self.session = session
        self._host = host
        self._ui = ui
        self._hostid = hostid
        self.packages = package_definitions.result()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.event_manager = EventManager(session)

        session.event_hub.subscribe(
            'topic={} and data.pipeline.hostid={}'.format(constants.PIPELINE_RUN_PUBLISHER, self.hostid),
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
                    'host': self.host
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
            data={
                'pipeline': {
                    'hostid': self.hostid,
                    'widget_ref': widget_id,
                    'data': data,
                }
            }
        )

        self.event_manager.publish(
            event,
            remote=self.__remote_events
        )

    def run_context(self, context):
        results = {}
        for plugin in context:
            result = self._run_plugin(
                plugin, constants.CONTEXT,
                context=plugin['options']
            )
            results.update(result[0])
        return results

    def run_component(self, component_stages, context_data):
        results = {}

        sorted_stages = dict(
            sorted(
                component_stages.items(),
                key=lambda i: self.component_stages_order.index(i[0])
            )
        )

        for stage, plugins in sorted_stages.items():
            collected_data = results.get(constants.COLLECT, [])
            stages_result = []
            validators = results.get(constants.VALIDATE)

            if validators and not all(validators):
                # todo : customise exceptions
                raise Exception('Stage Validation Error')

            for plugin in plugins:
                result = self._run_plugin(
                    plugin, stage,
                    data=collected_data,
                    options=plugin['options'],
                    context=context_data
                )

                if len(result) > 0 and isinstance(result[0], list):
                    result = result[0]

                stages_result += result

            results[stage] = stages_result

        return results

    def run_publish(self, publisher, publish_data, context_data):
        results = []
        for plugin in publisher:
            result = self._run_plugin(
                plugin, constants.PUBLISH,
                data=publish_data,
                options=plugin['options'],
                context=context_data
            )
            results.append(result[0])

        return results

    def run(self, event):
        data = event['data']['pipeline']['data']
        publish_package = data['package']
        asset_type = self.packages[publish_package]['type']

        context_plugins = data[constants.CONTEXT]
        context_result = self.run_context(context_plugins)
        context_result['asset_type'] = asset_type

        components_plugins = data[constants.COMPONENTS]
        components_result = []
        for component_name, component_stages in components_plugins.items():
            component_result = self.run_component(
                component_stages, context_result
            )
            components_result.append(component_result)

        publish_plugins = data[constants.PUBLISH]

        publish_data = {}
        for item in components_result:
            for output in item.get(constants.OUTPUT):
                for key, value in output.items():
                    publish_data[key] = value

        publish_result = self.run_publish(
            publish_plugins, publish_data, context_result
        )

        self.logger.info(publish_result)






